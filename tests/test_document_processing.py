import textwrap
from pathlib import Path

import pytest

from document_processing import DocumentProcessingError, process_file, SUPPORTED_EXTENSIONS
def test_supported_extensions_contains_basics():
    assert '.pdf' in SUPPORTED_EXTENSIONS
    assert '.docx' in SUPPORTED_EXTENSIONS
    assert '.txt' in SUPPORTED_EXTENSIONS


def _write_file(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")






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
        process_file("nonexistent.txt")

