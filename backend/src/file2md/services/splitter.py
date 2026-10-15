"""Document splitting services for parallel processing of large files."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
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
    metadata: Dict[str, Any] = field(default_factory=dict)


def should_split_document(file_path: Path, ext: str, size_bytes: int) -> bool:
    """Determine whether a document warrants parallel splitting."""
    settings = get_settings()

    # Only PDF, CSV, and plain text / MD formats are split
    if ext.lower() not in {".pdf", ".csv", ".txt", ".md"}:
        return False

    # Check size threshold
    if size_bytes >= settings.CHUNK_SPLIT_THRESHOLD_BYTES:
        return True

    # For PDFs, also check page count even if file size is below threshold (e.g., text-dense PDFs)
    if ext.lower() == ".pdf":
        try:
            import sys
            sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
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
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for count, _ in enumerate(f):
                    if count >= settings.CSV_CHUNK_ROW_SIZE * 3:
                        return True
        except Exception as exc:
            logger.warning("csv_row_check_failed", error=str(exc))
            return False

    return False


def split_pdf(
    file_path: Path, output_dir: Path, pages_per_chunk: int | None = None
) -> List[DocumentChunk]:
    """Split a multi-page PDF into smaller PDF chunks for parallel conversion."""
    import sys
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
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
                metadata={"start_page": 1, "end_page": total_pages, "total_pages": total_pages},
            )
        ]

    chunks: List[DocumentChunk] = []
    chunk_count = (total_pages + chunk_size - 1) // chunk_size

    try:
        for idx, start_page in enumerate(range(0, total_pages, chunk_size)):
            end_page = min(start_page + chunk_size, total_pages)
            writer = PdfWriter()

            # Using append with import_outline=False prevents deeply nested outline recursion
            try:
                writer.append(reader, pages=(start_page, end_page), import_outline=False)
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
) -> List[DocumentChunk]:
    """Split a CSV into row chunks, retaining the header row in each chunk."""
    settings = get_settings()
    chunk_size = rows_per_chunk or settings.CSV_CHUNK_ROW_SIZE

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if len(lines) <= 1:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=".csv",
                metadata={"rows": len(lines)},
            )
        ]

    header = lines[0]
    data_rows = lines[1:]
    total_data_rows = len(data_rows)

    if total_data_rows <= chunk_size:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=".csv",
                metadata={"rows": len(lines)},
            )
        ]

    chunks: List[DocumentChunk] = []
    chunk_count = (total_data_rows + chunk_size - 1) // chunk_size

    for idx, start_idx in enumerate(range(0, total_data_rows, chunk_size)):
        chunk_rows = data_rows[start_idx : start_idx + chunk_size]
        chunk_path = output_dir / f"chunk_{idx:04d}.csv"

        with open(chunk_path, "w", encoding="utf-8") as f_out:
            f_out.write(header)
            f_out.writelines(chunk_rows)

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


def split_text(
    file_path: Path, output_dir: Path, lines_per_chunk: int | None = None
) -> List[DocumentChunk]:
    """Split plain text or markdown by line boundaries."""
    settings = get_settings()
    chunk_size = lines_per_chunk or settings.TXT_CHUNK_LINE_SIZE
    ext = file_path.suffix.lower()

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if len(lines) <= chunk_size:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=ext,
                metadata={"lines": len(lines)},
            )
        ]

    chunks: List[DocumentChunk] = []
    chunk_count = (len(lines) + chunk_size - 1) // chunk_size

    for idx, start_idx in enumerate(range(0, len(lines), chunk_size)):
        chunk_lines = lines[start_idx : start_idx + chunk_size]
        chunk_path = output_dir / f"chunk_{idx:04d}{ext}"

        with open(chunk_path, "w", encoding="utf-8") as f_out:
            f_out.writelines(chunk_lines)

        chunks.append(
            DocumentChunk(
                chunk_index=idx,
                total_chunks=chunk_count,
                file_path=chunk_path,
                extension=ext,
                metadata={"lines": len(chunk_lines)},
            )
        )

    logger.info(
        "text_split_completed",
        total_lines=len(lines),
        chunks_created=len(chunks),
    )
    return chunks


def split_document(file_path: Path, ext: str, output_dir: Path) -> List[DocumentChunk]:
    """Dispatch file to the appropriate splitter."""
    ext_clean = ext.lower()
    if ext_clean == ".pdf":
        return split_pdf(file_path, output_dir)
    elif ext_clean == ".csv":
        return split_csv(file_path, output_dir)
    elif ext_clean in {".txt", ".md"}:
        return split_text(file_path, output_dir)
    else:
        return [
            DocumentChunk(
                chunk_index=0,
                total_chunks=1,
                file_path=file_path,
                extension=ext_clean,
            )
        ]
