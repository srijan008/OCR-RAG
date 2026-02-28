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
    chunk_type: str  # 'parent' or 'child'
    parent_id: str   # Unique identifier linking child to parent


def chunk_text_hierarchical(
    text: str,
    page_number: int = 1,
    start_index: int = 0,
) -> list[TextChunk]:
    """
    Split text into large parent chunks, then split those into smaller child chunks.
    """
    text = text.strip()
    if not text:
        return []

    chunks: list[TextChunk] = []
    idx = start_index

    # 1. Create Parent Chunks
    parent_pos = 0
    parent_size = settings.parent_chunk_size

    while parent_pos < len(text):
        parent_end = min(parent_pos + parent_size, len(text))
        parent_snippet = text[parent_pos:parent_end]

        # Break at sentence boundary if possible
        if parent_end < len(text):
            for sep in [". ", ".\n", "! ", "? ", "\n\n"]:
                last = parent_snippet.rfind(sep)
                if last != -1 and last > parent_size // 2:
                    parent_end = parent_pos + last + len(sep)
                    parent_snippet = text[parent_pos:parent_end]
                    break

        parent_snippet = parent_snippet.strip()
        if not parent_snippet:
            parent_pos = parent_end
            continue

        parent_id = f"page{page_number}_idx{idx}"
        chunks.append(
            TextChunk(
                text=parent_snippet,
                chunk_index=idx,
                page_number=page_number,
                chunk_type="parent",
                parent_id=parent_id,
            )
        )
        idx += 1

        # 2. Create Child Chunks from this Parent
        child_pos = 0
        while child_pos < len(parent_snippet):
            child_end = min(child_pos + settings.child_chunk_size, len(parent_snippet))
            child_snippet = parent_snippet[child_pos:child_end]

            if child_end < len(parent_snippet):
                for sep in [". ", ".\n", "! ", "? ", "\n\n"]:
                    last = child_snippet.rfind(sep)
                    if last != -1 and last > settings.child_chunk_size // 2:
                        child_end = child_pos + last + len(sep)
                        child_snippet = parent_snippet[child_pos:child_end]
                        break

            if child_snippet.strip():
                chunks.append(
                    TextChunk(
                        text=child_snippet.strip(),
                        chunk_index=idx,
                        page_number=page_number,
                        chunk_type="child",
                        parent_id=parent_id,
                    )
                )
                idx += 1

            # Advance child with overlap
            child_pos = child_end - settings.child_chunk_overlap if child_end < len(parent_snippet) else child_end

        # Advance parent (no overlap for parents)
        parent_pos = parent_end

    return chunks


def chunk_pages(page_texts: list[tuple[int, str]]) -> list[TextChunk]:
    """
    Chunk a list of (page_number, text) tuples.
    Returns combined list with correct global chunk indices.
    """
    all_chunks: list[TextChunk] = []
    for page_num, text in page_texts:
        new_chunks = chunk_text_hierarchical(
            text, page_number=page_num, start_index=len(all_chunks)
        )
        all_chunks.extend(new_chunks)
    return all_chunks
