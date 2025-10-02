"""Document processing pipeline for PDF and DOCX files."""

from __future__ import annotations

import logging
import re
import threading
from pathlib import Path
from typing import Optional

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

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

_DOC_CONVERTER: Optional[DocumentConverter] = None
_DOC_CONVERTER_LOCK = threading.Lock()




def process_file(file_path: str) -> str:
    """Process the document located at *file_path* and return extracted text."""

    if not file_path:
        raise DocumentProcessingError("No file path provided")

    resolved_path = Path(file_path).expanduser().resolve()
    if not resolved_path.exists():
        raise DocumentProcessingError(f"File not found: {resolved_path}")

    suffix = resolved_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentProcessingError(f"Unsupported file extension: {suffix}")

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


def _read_text(path: Path, quiet: bool = False) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    message = f"Unable to decode text file: {path}"
    if not quiet:
        logger.error(message)
    raise DocumentProcessingError(message)


def _normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    collapsed = re.sub(r"[\t ]+", " ", text)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    return collapsed.strip()


__all__ = ["process_file", "DocumentProcessingError", "SUPPORTED_EXTENSIONS"]


