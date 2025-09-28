import textwrap
from pathlib import Path

import pytest

from document_processing import DocumentProcessingError, process_file, SUPPORTED_EXTENSIONS
def test_supported_extensions_contains_basics():
    assert '.pdf' in SUPPORTED_EXTENSIONS
    assert '.docx' in SUPPORTED_EXTENSIONS
    assert '.tex' in SUPPORTED_EXTENSIONS


def _write_file(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def test_process_file_latex_project_with_includes(tmp_path):
    project_root = tmp_path / "latex_project"
    project_root.mkdir()

    main_tex = project_root / "main.tex"
    appendix_dir = project_root / "sections"
    appendix_dir.mkdir()
    appendix_tex = appendix_dir / "appendix.tex"

    _write_file(
        main_tex,
        r"""
        \documentclass{article}
        \begin{document}
        \section{Introduction}
        Hello \textbf{world}!
        \subsection{Details}
        Here is an inline equation $a + b = c$ and a display:
        \[
            E = mc^2
        \]
        \begin{itemize}
            \item First item
            \item Second item
        \end{itemize}
        \input{sections/appendix}
        \end{document}
        """,
    )

    _write_file(
        appendix_tex,
        r"""
        \section{Appendix}
        Additional context lives here.
        """,
    )

    result = process_file(str(project_root))

    assert "SECTION: Introduction" in result
    assert "SUBSECTION: Details" in result
    assert "SECTION: Appendix" in result
    assert "[EQUATION:" in result
    assert "- First item" in result
    assert "- Second item" in result


def test_process_file_single_tex_entry(tmp_path):
    tex_file = tmp_path / "paper.tex"
    _write_file(
        tex_file,
        r"""
        \documentclass{article}
        \begin{document}
        \section{Overview}
        Plain content.
        \end{document}
        """,
    )

    result = process_file(str(tex_file))

    assert isinstance(result, str)
    assert "SECTION: Overview" in result


def test_process_file_docx_uses_docling_stub(monkeypatch, tmp_path):
    docx_path = tmp_path / "document.docx"
    docx_path.write_bytes(b"stub")

    calls = {}

    def fake_process_with_docling(path: Path) -> str:
        calls["invoked"] = True
        assert path == docx_path
        return "DOCX CONTENT"

    monkeypatch.setattr(
        "document_processing._process_with_docling", fake_process_with_docling
    )

    result = process_file(str(docx_path))

    assert result == "DOCX CONTENT"
    assert calls.get("invoked") is True


def test_process_file_unsupported_extension(tmp_path):
    txt_file = tmp_path / "note.md"
    txt_file.write_text("hello", encoding="utf-8")

    with pytest.raises(DocumentProcessingError):
        process_file(str(txt_file))


def test_process_file_missing_path():
    with pytest.raises(DocumentProcessingError):
        process_file("nonexistent.tex")

