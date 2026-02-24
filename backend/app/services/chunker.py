"""
Text chunking service.
Splits extracted OCR text into overlapping chunks suitable for embedding.
"""
from dataclasses import dataclass
from app.config import get_settings

settings = get_settings()


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    page_number: int


def chunk_text(
    text: str,
    page_number: int = 1,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    start_index: int = 0,
) -> list[TextChunk]:
    """
    Split text into overlapping fixed-character chunks.
    Falls back to paragraph-aware splitting when paragraphs are short.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    text = text.strip()
    if not text:
        return []

    chunks: list[TextChunk] = []
    idx = start_index
    pos = 0

    while pos < len(text):
        end = min(pos + chunk_size, len(text))

        # Try to break at a sentence boundary
        snippet = text[pos:end]
        if end < len(text):
            # Back up to last sentence terminator
            for sep in [". ", ".\n", "! ", "? ", "\n\n"]:
                last = snippet.rfind(sep)
                if last != -1 and last > chunk_size // 2:
                    end = pos + last + len(sep)
                    snippet = text[pos:end]
                    break

        if snippet.strip():
            chunks.append(
                TextChunk(
                    text=snippet.strip(),
                    chunk_index=idx,
                    page_number=page_number,
                )
            )
            idx += 1

        # Advance with overlap
        pos = end - chunk_overlap if end < len(text) else end

    return chunks


def chunk_pages(page_texts: list[tuple[int, str]]) -> list[TextChunk]:
    """
    Chunk a list of (page_number, text) tuples.
    Returns combined list with correct global chunk indices.
    """
    all_chunks: list[TextChunk] = []
    for page_num, text in page_texts:
        new_chunks = chunk_text(
            text, page_number=page_num, start_index=len(all_chunks)
        )
        all_chunks.extend(new_chunks)
    return all_chunks
