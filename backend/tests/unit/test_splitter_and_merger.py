"""Unit tests for document splitter and markdown merger services."""

import tempfile
from pathlib import Path

from pypdf import PdfWriter

from file2md.services.merger import merge_csv_tables, merge_markdown_chunks
from file2md.services.splitter import (
    should_split_document,
    split_csv,
    split_document,
    split_pdf,
)


def create_dummy_pdf(path: Path, num_pages: int) -> None:
    """Create a minimal valid multi-page PDF for testing."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)


def test_split_pdf_generates_page_chunks() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        pdf_file = tmp_path / "test_doc.pdf"
        output_dir = tmp_path / "chunks"
        output_dir.mkdir()

        # Create a 35-page PDF
        create_dummy_pdf(pdf_file, 35)

        chunks = split_pdf(pdf_file, output_dir, pages_per_chunk=10)
        assert len(chunks) == 4  # 10 + 10 + 10 + 5
        assert chunks[0].metadata["start_page"] == 1
        assert chunks[0].metadata["end_page"] == 10
        assert chunks[3].metadata["start_page"] == 31
        assert chunks[3].metadata["end_page"] == 35

        for chunk in chunks:
            assert chunk.file_path.exists()
            assert chunk.file_path.stat().st_size > 0


def test_split_csv_retains_header_in_each_chunk() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "data.csv"
        output_dir = tmp_path / "chunks"
        output_dir.mkdir()

        # Write CSV with header and 25 data rows
        lines = ["id,name,role\n"] + [f"{i},user_{i},dev\n" for i in range(1, 26)]
        csv_file.write_text("".join(lines))

        chunks = split_csv(csv_file, output_dir, rows_per_chunk=10)
        assert len(chunks) == 3  # 10 + 10 + 5

        # Verify each chunk has header
        for chunk in chunks:
            chunk_content = chunk.file_path.read_text()
            assert chunk_content.startswith("id,name,role\n")


def test_text_and_md_documents_are_not_split() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        txt_file = tmp_path / "doc.txt"
        output_dir = tmp_path / "chunks"
        output_dir.mkdir()

        txt_file.write_text("Hello world")

        assert not should_split_document(txt_file, ".txt", 10_000_000)
        assert not should_split_document(txt_file, ".md", 10_000_000)

        chunks = split_document(txt_file, ".txt", output_dir)
        assert len(chunks) == 1
        assert chunks[0].file_path == txt_file


def test_merge_csv_tables_combines_without_repeated_headers() -> None:
    chunk1 = """| id | name |
| --- | --- |
| 1 | Alice |
| 2 | Bob |"""

    chunk2 = """| id | name |
| --- | --- |
| 3 | Charlie |
| 4 | Dave |"""

    merged = merge_csv_tables([chunk1, chunk2])
    lines = merged.split("\n")
    assert len(lines) == 6
    assert lines[0] == "| id | name |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| 1 | Alice |"
    assert lines[5] == "| 4 | Dave |"


def test_merge_markdown_chunks_normalizes_spacing() -> None:
    c1 = "# Header\n\nFirst paragraph."
    c2 = "## Next section\n\nSecond paragraph."

    merged = merge_markdown_chunks([c1, c2], ".pdf")
    assert "# Header" in merged
    assert "## Next section" in merged
    assert "\n\n" in merged
    assert "\n\n\n" not in merged


def test_split_pdf_falls_back_on_unreadable_file() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        corrupted_pdf = tmp_path / "corrupted.pdf"
        corrupted_pdf.write_bytes(
            b"%PDF-1.4\nCorrupted content without valid xref table"
        )
        output_dir = tmp_path / "chunks"
        output_dir.mkdir()

        chunks = split_pdf(corrupted_pdf, output_dir)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].file_path == corrupted_pdf


def test_split_csv_preserves_quoted_newline_across_chunks() -> None:
    csv_content = (
        "id,description,status\r\n"
        '1,"Row 1 single line",ok\r\n'
        '2,"Row 2 with\nembedded newline",active\r\n'
        '3,"Row 3 final",done\r\n'
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        out_dir = tmp_path / "chunks"
        out_dir.mkdir()

        chunks = split_csv(csv_file, out_dir, rows_per_chunk=2)
        assert len(chunks) == 2

        chunk0_text = chunks[0].file_path.read_text(encoding="utf-8")
        assert chunk0_text.startswith("id,description,status")
        assert "embedded newline" in chunk0_text

        chunk1_text = chunks[1].file_path.read_text(encoding="utf-8")
        assert chunk1_text.startswith("id,description,status")
        assert "3,Row 3 final,done" in chunk1_text
