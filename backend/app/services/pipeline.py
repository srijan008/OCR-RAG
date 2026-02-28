"""
Ingestion pipeline orchestrator:
Preprocessing → OCR → PDF Generation → Chunking → Embedding → ChromaDB upsert
"""
import asyncio
from pathlib import Path
from PIL import Image
import pypdf
from pdf2image import convert_from_path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Document, DocumentStatus
from app.services.preprocessing import preprocess_image
from app.services.ocr import extract_page, PageOCRResult
from app.services.pdf_generator import generate_searchable_pdf
from app.services.chunker import chunk_pages
from app.services.embedder import embed_documents
from app.services.chroma_store import upsert_chunks
from app.utils.file_utils import get_pdf_path


async def run_pipeline(
    db: AsyncSession,
    document_id: int,
    file_path: str,
    file_type: str,
) -> None:
    """Full OCR-to-RAG ingestion pipeline. Updates Document record in place."""
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one_or_none()
    if not doc:
        return

    try:
        doc.status = DocumentStatus.PROCESSING
        doc.processing_step = "Uploading"
        await db.commit()

        # ── Step 1: Load pages as PIL Images ──────────────────────────────
        doc.processing_step = "Preprocessing"
        await db.commit()
        pages_pil: list[Image.Image] = []
        fallback_texts: list[str] = []

        if file_type in (".pdf",):
            try:
                # Attempt to convert PDF to images for OCR (vital for scanned docs)
                # Note: Requires Poppler to be installed and in PATH on Windows
                imgs = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: convert_from_path(file_path, dpi=200)
                )
                if not imgs:
                    raise ValueError("No images extracted from PDF.")
                pages_pil.extend(imgs)
            except Exception as e:
                # Fallback to direct text extraction if pdf2image/poppler fails
                # Log the error so it's visible in uvicorn terminal
                print(f"pdf2image conversion failed: {e}")
                
                reader = pypdf.PdfReader(file_path)
                if not reader.pages:
                    raise ValueError("PDF file has no pages or is unreadable.")
                
                for page in reader.pages:
                    text_direct = page.extract_text() or ""
                    pages_pil.append(None)
                    fallback_texts.append(text_direct)
                
                # If we have no images and no extracted text, this doc is basically empty for RAG
                if all(not t.strip() for t in fallback_texts):
                    error_hint = (
                        "Scanned PDF detected but pdf2image/Poppler is not working. "
                        "Please install Poppler and add its 'bin' folder to your PATH."
                    )
                    doc.error_message = error_hint
                    await db.commit()
                    # We don't necessarily raise here if we want to allow "empty" results, 
                    # but usually it's better to fail if it's useless.
        else:
            img = Image.open(file_path)
            try:
                for i in range(img.n_frames):
                    img.seek(i)
                    pages_pil.append(img.copy())
            except (AttributeError, EOFError):
                pages_pil.append(img.copy())

        # ── Step 2: Preprocess + OCR each page ────────────────────────────
        doc.processing_step = "OCR"
        doc.ocr_text = ""
        await db.commit()

        page_ocr_results: list[PageOCRResult] = []
        original_pages: list[Image.Image] = []
        page_texts: list[tuple[int, str]] = []

        for i, pil_img in enumerate(pages_pil, start=1):
            if pil_img is None:
                text = fallback_texts[i - 1] if (i - 1) < len(fallback_texts) else ""
                page_texts.append((i, text))
                continue

            original_rgb, processed = preprocess_image(pil_img)
            original_pages.append(original_rgb)

            ocr_result = await asyncio.get_event_loop().run_in_executor(
                None, extract_page, processed, i
            )
            page_ocr_results.append(ocr_result)
            page_texts.append((i, ocr_result.text))
            
            # Append to ocr_text for real-time SSE streaming
            doc.ocr_text += ocr_result.text + "\n\n"
            await db.commit()

        # ── Step 3: Generate searchable PDF ───────────────────────────────
        doc.processing_step = "PDF Generation"
        await db.commit()
        
        stem = Path(file_path).stem
        pdf_output_path = get_pdf_path(stem)

        if original_pages and page_ocr_results:
            paired = list(zip(original_pages, page_ocr_results))
            await asyncio.get_event_loop().run_in_executor(
                None, generate_searchable_pdf, paired, pdf_output_path
            )
        else:
            pdf_output_path = file_path if file_type == ".pdf" else None

        # ── Step 4: Chunk text ────────────────────────────────────────────
        chunks = chunk_pages(page_texts)

        # ── Step 5: Embed child chunks via Gemini ─────────────────────────
        doc.processing_step = "Embedding"
        await db.commit()
        
        child_chunks = [c for c in chunks if c.chunk_type == "child"]
        parent_chunks = [c for c in chunks if c.chunk_type == "parent"]
        
        texts_to_embed = [c.text for c in child_chunks]
        child_embeddings: list[list[float]] = []
        if texts_to_embed:
            child_embeddings = await asyncio.get_event_loop().run_in_executor(
                None, embed_documents, texts_to_embed
            )

        # ── Step 6: Upsert into ChromaDB ──────────────────────────────────
        # We index child chunks with real embeddings.
        # We index parent chunks with dummy embeddings so we can retrieve them by parent_id.
        from app.config import get_settings
        dim = get_settings().embed_dimension
        
        chunk_dicts = []
        all_embeddings = []
        
        for c, emb in zip(child_chunks, child_embeddings):
            chunk_dicts.append({
                "text": c.text, "chunk_index": c.chunk_index, "page_number": c.page_number,
                "chunk_type": c.chunk_type, "parent_id": c.parent_id
            })
            all_embeddings.append(emb)
            
        for c in parent_chunks:
            chunk_dicts.append({
                "text": c.text, "chunk_index": c.chunk_index, "page_number": c.page_number,
                "chunk_type": c.chunk_type, "parent_id": c.parent_id
            })
            all_embeddings.append([0.0] * dim) # Dummy embedding

        upsert_chunks(
            document_id=document_id,
            chunks=chunk_dicts,
            embeddings=all_embeddings,
        )

        # ── Step 7: Update document record ────────────────────────────────
        doc.pdf_path = pdf_output_path
        doc.page_count = len(pages_pil)
        doc.chunk_count = len(chunks)
        doc.ocr_confidence_avg = (
            sum(r.avg_confidence for r in page_ocr_results) / len(page_ocr_results)
            if page_ocr_results
            else 0.0
        )
        doc.status = DocumentStatus.COMPLETED
        doc.processing_step = "Done"
        await db.commit()

    except Exception as exc:
        doc.status = DocumentStatus.FAILED
        doc.processing_step = "error"
        doc.error_message = str(exc)
        await db.commit()
        raise
