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
from app.services.chroma_store import search_chunks
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

    # 2. Retrieve top-k chunks from ChromaDB
    chunks = search_chunks(query_embedding, top_k=top_k, document_ids=document_ids)

    if not chunks:
        return {
            "answer": "No relevant documents found. Please upload some documents first.",
            "sources": [],
            "model": GEMINI_MODEL,
        }

    # 3. Enrich with document names from PostgreSQL
    chunks = await _enrich_with_doc_names(db, chunks)

    # 4. Build prompt and call Gemini 2.5 Flash
    prompt = build_rag_prompt(query, chunks)
    model = get_gemini_model()
    response = model.generate_content(prompt)
    answer = response.text.strip()

    return {
        "answer": answer,
        "sources": chunks,
        "model": GEMINI_MODEL,
    }
