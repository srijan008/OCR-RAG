"""
RAG service:
1. Embed user query via Cohere
2. Retrieve top-k similar chunks via ChromaDB cosine search
3. Fetch document names from PostgreSQL
4. Build grounded prompt → Gemini 2.5 Flash
"""
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.services.embedder import embed_query
from app.services.chroma_store import search_chunks, get_parent_chunks
from app.models import Document

settings = get_settings()

genai.configure(api_key=settings.gemini_api_key)
GEMINI_MODEL = "gemini-3-flash-preview"


def get_gemini_model():
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=2048,
        ),
    )


async def _enrich_with_doc_names(
    db: AsyncSession,
    chunks: list[dict],
) -> list[dict]:
    """Join ChromaDB results with document names from PostgreSQL."""
    doc_ids = list({c["document_id"] for c in chunks})
    result = await db.execute(
        select(Document.id, Document.original_filename).where(Document.id.in_(doc_ids))
    )
    id_to_name = {row[0]: row[1] for row in result.fetchall()}

    for chunk in chunks:
        chunk["document_name"] = id_to_name.get(chunk["document_id"], f"Doc #{chunk['document_id']}")
    return chunks


def build_rag_prompt(query: str, chunks: list[dict]) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[Source {i}: {chunk['document_name']} | Page {chunk['page_number']}]\n"
            f"{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are an intelligent document assistant. Use ONLY the context below to answer the user's question.
If the answer is not found in the context, say "I couldn't find relevant information in the uploaded documents."

CONTEXT:
{context}

USER QUESTION: {query}

ANSWER (cite the source document name where relevant):"""


async def query_rag(
    db: AsyncSession,
    query: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
) -> dict:
    """Full RAG pipeline: Cohere embed → ChromaDB search → Gemini 2.5 Flash."""
    top_k = top_k or settings.top_k_results

    # 1. Embed the query (Cohere "search_query" mode)
    query_embedding = embed_query(query)

    # 2. Retrieve top-k child chunks from ChromaDB
    child_chunks = search_chunks(query_embedding, top_k=top_k, document_ids=document_ids)

    if not child_chunks:
        return {
            "answer": "No relevant documents found. Please upload some documents first.",
            "sources": [],
            "model": GEMINI_MODEL,
        }

    # 3. Retrieve broader context via Parent Chunks
    parent_ids = list({c["parent_id"] for c in child_chunks if c.get("parent_id")})
    
    # Fallback to the child chunks themselves if no parent_ids exist (e.g. legacy data)
    if parent_ids:
        context_chunks = get_parent_chunks(parent_ids)
    else:
        context_chunks = child_chunks

    # 4. Enrich context chunks with document names from PostgreSQL
    context_chunks = await _enrich_with_doc_names(db, context_chunks)

    # 5. Build prompt and call Gemini 1.5 Flash
    prompt = build_rag_prompt(query, context_chunks)
    model = get_gemini_model()
    response = model.generate_content(prompt)
    answer = response.text.strip()

    return {
        "answer": answer,
        "sources": context_chunks,
        "model": settings.gemini_model,
    }
