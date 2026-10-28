"""Document splitting services for parallel processing of large files."""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from file2md.config import get_settings

logger = structlog.get_logger()


@dataclass
class DocumentChunk:
    """Represents an isolated chunk of a split document."""

    chunk_index: int
    total_chunks: int
    file_path: Path
    extension: str
    metadata: dict[str, Any] = field(default_factory=dict)


def should_split_document(file_path: Path, ext: str, size_bytes: int) -> bool:
    """Determine whether a document warrants parallel splitting."""
    settings = get_settings()

    # Only PDF and CSV formats are split
    if ext.lower() not in {".pdf", ".csv"}:
        return False

    # Check size threshold
    if size_bytes >= settings.CHUNK_SPLIT_THRESHOLD_BYTES:
        return True

    # For PDFs, check page count even if size is below threshold (e.g. text-dense)
    if ext.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path), strict=False)
            total_pages = len(reader.pages)
            return total_pages > settings.PDF_CHUNK_PAGE_SIZE
        except Exception as exc:
            logger.warning("pdf_page_check_failed", error=str(exc))
            return False

    # For CSVs, also check row count even if file is compact
    if ext.lower() == ".csv":
        try:
            with open(file_path, newline="", encoding="utf-8", errors="ignore") as f:
                csv_reader = csv.reader(f)
                for count, _ in enumerate(csv_reader):
                    if count >= settings.CSV_CHUNK_ROW_SIZE * 3:
                        return True
        except Exception as exc:
            logger.warning("csv_row_check_failed", error=str(exc))
            return False

    return False


def split_pdf(
    file_path: Path, output_dir: Path, pages_per_chunk: int | None = None
) -> list[DocumentChunk]:
    """Split a multi-page PDF into smaller PDF chunks for parallel conversion."""
    from pypdf import PdfReader, PdfWriter

    settings = get_settings()
    chunk_size = pages_per_chunk or settings.PDF_CHUNK_PAGE_SIZE

    try:
        reader = PdfReader(str(file_path), strict=False)
        total_pages = len(reader.pages)
    except Exception as exc:
        logger.warning("pdf_split_read_failed", error=str(exc))
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=".pdf",
                metadata={"fallback_reason": f"PdfReader failed: {exc}"},
            )
        ]

    if total_pages <= chunk_size:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=".pdf",
                metadata={
                    "start_page": 1,
                    "end_page": total_pages,
                    "total_pages": total_pages,
                },
            )
        ]

    chunks: list[DocumentChunk] = []
    chunk_count = (total_pages + chunk_size - 1) // chunk_size

    try:
        for idx, start_page in enumerate(range(0, total_pages, chunk_size)):
            end_page = min(start_page + chunk_size, total_pages)
            writer = PdfWriter()

            # Using append with import_outline=False prevents outline recursion
            try:
                writer.append(
                    reader, pages=(start_page, end_page), import_outline=False
                )
            except Exception:
                for page_num in range(start_page, end_page):
                    writer.add_page(reader.pages[page_num])

            chunk_path = output_dir / f"chunk_{idx:04d}.pdf"
            with open(chunk_path, "wb") as f_out:
                writer.write(f_out)

            chunks.append(
                DocumentChunk(
                    chunk_index=idx,
                    total_chunks=chunk_count,
                    file_path=chunk_path,
                    extension=".pdf",
                    metadata={
                        "start_page": start_page + 1,
                        "end_page": end_page,
                        "total_pages": total_pages,
                    },
                )
            )

        logger.info(
            "pdf_split_completed",
            total_pages=total_pages,
            chunks_created=len(chunks),
            chunk_size=chunk_size,
        )
        return chunks

    except Exception as exc:
        logger.warning("pdf_split_failed_fallback_to_single", error=str(exc))
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=".pdf",
                metadata={"fallback_reason": f"Splitting failed: {exc}"},
            )
        ]


def split_csv(
    file_path: Path, output_dir: Path, rows_per_chunk: int | None = None
) -> list[DocumentChunk]:
    """Split a CSV into row chunks, retaining the header row in each chunk."""
    settings = get_settings()
    chunk_size = rows_per_chunk or settings.CSV_CHUNK_ROW_SIZE

    with open(file_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [
                DocumentChunk(
                    chunk_index=0,
                    total_chunks=1,
                    file_path=file_path,
                    extension=".csv",
                    metadata={"rows": 0},
                )
            ]
        data_rows = list(reader)

    total_data_rows = len(data_rows)
    if total_data_rows <= chunk_size:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=".csv",
                metadata={"rows": total_data_rows + 1},
            )
        ]

    chunks: list[DocumentChunk] = []
    chunk_count = (total_data_rows + chunk_size - 1) // chunk_size

    for idx, start_idx in enumerate(range(0, total_data_rows, chunk_size)):
        chunk_rows = data_rows[start_idx : start_idx + chunk_size]
        chunk_path = output_dir / f"chunk_{idx:04d}.csv"

        with open(chunk_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            writer.writerow(header)
            writer.writerows(chunk_rows)

        chunks.append(
            DocumentChunk(
                chunk_index=idx,
                total_chunks=chunk_count,
                file_path=chunk_path,
                extension=".csv",
                metadata={"chunk_rows": len(chunk_rows), "is_first": idx == 0},
            )
        )

    logger.info(
        "csv_split_completed",
        total_rows=total_data_rows,
        chunks_created=len(chunks),
    )
    return chunks


def split_document(file_path: Path, ext: str, output_dir: Path) -> list[DocumentChunk]:
    """Dispatch file to the appropriate splitter."""
    ext_clean = ext.lower()
    if ext_clean == ".pdf":
        return split_pdf(file_path, output_dir)
    elif ext_clean == ".csv":
        return split_csv(file_path, output_dir)
    else:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=ext_clean,
            )
        ]
