"""Hybrid document processing pipeline for LaTeX, PDF, and DOCX files."""

from __future__ import annotations

import logging
import re
import threading
from pathlib import Path
from io import BytesIO
from typing import Iterable, Iterator, List, Optional, Sequence, Set

from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import (
    ConversionResult,
    ConversionStatus,
    DocumentStream,
)
from docling.datamodel.pipeline_options import AcceleratorOptions, AcceleratorDevice, PdfPipelineOptions
from docling.datamodel.settings import settings as docling_settings
from docling.document_converter import DocumentConverter
from docling.exceptions import ConversionError
from pylatexenc.latexwalker import (
    LatexCharsNode,
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
    LatexNode,
    LatexWalker,
)

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".tex", ".latex", ".txt"}
LATEX_EXTENSIONS = {".tex", ".latex"}

_DOC_CONVERTER: Optional[DocumentConverter] = None
_DOC_CONVERTER_LOCK = threading.Lock()


SECTION_MACROS = {
    "part": "PART",
    "chapter": "CHAPTER",
    "section": "SECTION",
    "subsection": "SUBSECTION",
    "subsubsection": "SUBSUBSECTION",
    "paragraph": "PARAGRAPH",
}

CONTENT_PRESERVING_MACROS = {
    "textbf",
    "textit",
    "emph",
    "texttt",
    "underline",
    "item",
}

IGNORED_MACROS = {
    "documentclass",
    "usepackage",
    "newcommand",
    "renewcommand",
    "title",
    "author",
    "date",
    "maketitle",
    "tableofcontents",
    "listoffigures",
    "listoftables",
    "label",
    "ref",
    "pagestyle",
    "thispagestyle",
    "setlength",
    "addtolength",
    "geometry",
    "includeonly",
    "bibliographystyle",
    "bibliography",
}

NEWLINE_MACROS = {
    "\\",
    "par",
    "newline",
    "linebreak",
    "pagebreak",
}

EQUATION_ENVIRONMENTS = {
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "flalign",
    "flalign*",
    "math",
    "displaymath",
}

LIST_ENVIRONMENTS = {"itemize", "enumerate", "description"}


def process_file(file_path: str) -> str:
    """Process the document located at *file_path* and return extracted text."""

    if not file_path:
        raise DocumentProcessingError("No file path provided")

    resolved_path = Path(file_path).expanduser().resolve()
    if not resolved_path.exists():
        raise DocumentProcessingError(f"File not found: {resolved_path}")

    if resolved_path.is_dir():
        return _process_latex_project(resolved_path)

    suffix = resolved_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentProcessingError(f"Unsupported file extension: {suffix}")

    if suffix in LATEX_EXTENSIONS:
        return _process_latex_project(resolved_path)

    if suffix == ".txt":
        return _read_text(resolved_path)

    return _process_with_docling(resolved_path)


def _get_docling_converter() -> DocumentConverter:
    global _DOC_CONVERTER

    with _DOC_CONVERTER_LOCK:
        if _DOC_CONVERTER is None:
            # Try to detect GPU availability and configure accelerator
            device = AcceleratorDevice.CPU
            try:
                import torch
                if torch.cuda.is_available():
                    device = AcceleratorDevice.CUDA
                    logger.info("GPU acceleration enabled (CUDA)")
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device = AcceleratorDevice.MPS
                    logger.info("GPU acceleration enabled (MPS - Apple Silicon)")
                else:
                    logger.info("GPU not available, using CPU")
            except ImportError:
                logger.info("PyTorch not available, using CPU")
            except Exception as e:
                logger.warning("Failed to detect GPU availability: %s, using CPU", e)

            # Create converter with default options first
            _DOC_CONVERTER = DocumentConverter(
                allowed_formats=[InputFormat.PDF, InputFormat.DOCX]
            )
            
            # Update accelerator options for each format
            accelerator_options = AcceleratorOptions(device=device)
            for format_type in [InputFormat.PDF, InputFormat.DOCX]:
                if format_type in _DOC_CONVERTER.format_to_options:
                    format_option = _DOC_CONVERTER.format_to_options[format_type]
                    # Update the accelerator options in the existing pipeline options
                    if hasattr(format_option.pipeline_options, 'accelerator_options'):
                        format_option.pipeline_options.accelerator_options = accelerator_options
    return _DOC_CONVERTER


def _process_with_docling(file_path: Path) -> str:
    converter = _get_docling_converter()

    try:
        result: ConversionResult
        result = converter.convert(str(file_path), raises_on_error=False)
    except ConversionError as exc:
        logger.error("Docling conversion failed for %s: %s", file_path, exc)
        raise DocumentProcessingError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - docling internals
        logger.exception("Unhandled Docling error for %s", file_path)
        raise DocumentProcessingError("Docling failed to process the file") from exc

    if result.status not in {ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS}:
        errors = ", ".join(err.error_message for err in result.errors) or "unknown error"
        raise DocumentProcessingError(
            f"Docling conversion status {result.status}: {errors}"
        )

    text = result.document.export_to_markdown(
        delim="\n\n",
        escape_html=False,
        escape_underscores=False,
        image_placeholder="[IMAGE]",
    )

    cleaned = _normalize_whitespace(text)
    if not cleaned:
        raise DocumentProcessingError("Docling produced empty output")
    return cleaned


def _process_latex_project(path: Path) -> str:
    main_tex = _locate_main_tex(path)
    if main_tex is None:
        raise DocumentProcessingError("Unable to locate main LaTeX file")

    project_root = main_tex.parent
    visited: Set[Path] = set()
    output_segments: List[str] = []

    def _visit(tex_path: Path) -> None:
        tex_path = tex_path.resolve()
        if tex_path in visited:
            return
        if not tex_path.exists():
            logger.warning("Referenced LaTeX file missing: %s", tex_path)
            return
        visited.add(tex_path)

        content = _read_text(tex_path)
        nodes = _parse_latex_nodes(content)
        includes = _collect_includes(nodes)
        rendered = _render_nodelist(nodes)
        rendered = _normalize_whitespace(rendered)
        if rendered:
            output_segments.append(rendered)

        for include in includes:
            include_path = _resolve_include_path(include, tex_path.parent, project_root)
            if include_path is not None:
                _visit(include_path)

    _visit(main_tex)

    combined = "\n\n".join(segment for segment in output_segments if segment)
    return _normalize_whitespace(combined)


def _locate_main_tex(path: Path) -> Optional[Path]:
    candidate = path
    if candidate.is_file():
        if candidate.suffix.lower() in LATEX_EXTENSIONS:
            return candidate
        candidate = candidate.parent

    current = candidate.resolve()
    while True:
        main_file = current / "main.tex"
        if main_file.exists():
            return main_file

        top_level_candidates = sorted(current.glob("*.tex"))
        for tex_file in top_level_candidates:
            try:
                content = _read_text(tex_file, quiet=True)
            except DocumentProcessingError:
                continue
            if "\\documentclass" in content:
                return tex_file

        if current == current.parent:
            break
        current = current.parent

    if path.is_file() and path.suffix.lower() in LATEX_EXTENSIONS:
        return path.resolve()

    logger.error("No LaTeX entry point found starting from %s", path)
    return None


def _read_text(path: Path, quiet: bool = False) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    message = f"Unable to decode LaTeX file: {path}"
    if not quiet:
        logger.error(message)
    raise DocumentProcessingError(message)


def _parse_latex_nodes(content: str) -> List[LatexNode]:
    walker = LatexWalker(content)
    nodes, _, _ = walker.get_latex_nodes()
    return list(nodes or [])


def _collect_includes(nodes: Sequence[LatexNode]) -> List[str]:
    includes: List[str] = []
    for node in nodes:
        includes.extend(list(_collect_includes_from_node(node)))
    return includes


def _collect_includes_from_node(node: LatexNode) -> Iterator[str]:
    if isinstance(node, LatexMacroNode) and node.macroname in {"input", "include"}:
        include_target = _render_macro_argument(node, arg_index=0).strip()
        if include_target:
            yield include_target

    for child in _iter_child_nodes(node):
        yield from _collect_includes_from_node(child)


def _resolve_include_path(
    include: str, base_dir: Path, project_root: Path
) -> Optional[Path]:
    sanitized = include.strip()
    if not sanitized:
        return None

    potential_paths = []
    include_path = (base_dir / sanitized).resolve()
    potential_paths.append(include_path)
    if include_path.suffix == "":
        potential_paths.append((base_dir / f"{sanitized}.tex").resolve())

    for candidate in potential_paths:
        try:
            candidate.relative_to(project_root)
        except ValueError:
            continue
        if candidate.exists():
            return candidate

    logger.warning("Unable to resolve include '%s' relative to %s", include, base_dir)
    return None


def _render_nodelist(nodelist: Optional[Iterable[LatexNode]]) -> str:
    if not nodelist:
        return ""
    return "".join(_render_node(node) for node in nodelist)


def _render_node(node: LatexNode) -> str:
    if isinstance(node, LatexCharsNode):
        return node.chars

    if isinstance(node, LatexCommentNode):
        return ""

    if isinstance(node, LatexGroupNode):
        return _render_nodelist(node.nodelist)

    if isinstance(node, LatexMathNode):
        math_text = node.latex_verbatim().strip()
        return f"[EQUATION: {math_text}]"

    if isinstance(node, LatexMacroNode):
        name = node.macroname
        if name in SECTION_MACROS:
            title = _render_macro_argument(node, arg_index=0).strip()
            if title:
                return f"\n{SECTION_MACROS[name]}: {title}\n"
            return ""
        if name in {"input", "include"}:
            return ""
        if name in NEWLINE_MACROS:
            return "\n"
        if name in IGNORED_MACROS:
            return ""
        if name in CONTENT_PRESERVING_MACROS:
            return _render_macro_argument(node, arg_index=0)
        return _render_all_arguments(node)

    if isinstance(node, LatexEnvironmentNode):
        env = node.envname
        if env in EQUATION_ENVIRONMENTS:
            equation_text = node.latex_verbatim().strip()
            return f"[EQUATION: {equation_text}]"
        if env in LIST_ENVIRONMENTS:
            return _render_list_environment(node)
        return _render_nodelist(node.nodelist)

    return getattr(node, "latex_verbatim", lambda: "")()


def _render_all_arguments(node: LatexMacroNode) -> str:
    if not node.nodeargd:
        return ""
    parts = [
        _render_nodelist(arg.nodelist) if arg and arg.nodelist else ""
        for arg in node.nodeargd.argnlist
    ]
    return "".join(parts)


def _render_macro_argument(node: LatexMacroNode, arg_index: int) -> str:
    if not node.nodeargd:
        return ""
    args = node.nodeargd.argnlist
    if arg_index >= len(args):
        return ""
    arg = args[arg_index]
    if arg is None or arg.nodelist is None:
        return ""
    return _render_nodelist(arg.nodelist)


def _render_list_environment(node: LatexEnvironmentNode) -> str:
    ordered = node.envname == "enumerate"
    items: List[str] = []
    buffer: List[str] = []

    def flush_buffer() -> None:
        if not buffer:
            return
        text = _normalize_whitespace("".join(buffer))
        buffer.clear()
        if text:
            items.append(text)

    for child in node.nodelist or []:
        if isinstance(child, LatexMacroNode) and child.macroname == "item":
            flush_buffer()
            item_header = _render_all_arguments(child)
            if item_header.strip():
                buffer.append(item_header.strip() + " ")
            continue
        buffer.append(_render_node(child))

    flush_buffer()

    rendered_items: List[str] = []
    for index, item_text in enumerate(items, start=1):
        bullet = f"{index}." if ordered else "-"
        rendered_items.append(f"{bullet} {item_text}")

    return "\n".join(rendered_items) + ("\n" if rendered_items else "")


def _iter_child_nodes(node: LatexNode) -> Iterator[LatexNode]:
    if isinstance(node, LatexGroupNode):
        yield from node.nodelist or []
    elif isinstance(node, LatexEnvironmentNode):
        yield from node.nodelist or []
    elif isinstance(node, LatexMacroNode) and node.nodeargd:
        for arg in node.nodeargd.argnlist:
            if arg and arg.nodelist:
                yield from arg.nodelist
    elif isinstance(node, LatexMathNode):
        yield from node.nodelist or []


def _normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    collapsed = re.sub(r"[\t ]+", " ", text)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    return collapsed.strip()


__all__ = ["process_file", "DocumentProcessingError", "SUPPORTED_EXTENSIONS"]


