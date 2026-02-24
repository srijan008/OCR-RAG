"""Query router: RAG queries scoped to the current user's documents."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Document, User
from app.schemas import QueryRequest, QueryResponse, SourceChunk
from app.dependencies import get_current_user
from app.services.rag import query_rag

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    RAG query — automatically scoped to the current user's documents only.
    Optionally further filtered by document_ids (must belong to the user).
    """
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty.")

    # Resolve which document IDs to search — always restrict to current user
    if request.document_ids:
        result = await db.execute(
            select(Document.id).where(
                Document.user_id == current_user.id,
                Document.id.in_(request.document_ids),
                Document.status == "completed",
            )
        )
        allowed_ids = [row[0] for row in result.fetchall()]
    else:
        result = await db.execute(
            select(Document.id).where(
                Document.user_id == current_user.id,
                Document.status == "completed",
            )
        )
        allowed_ids = [row[0] for row in result.fetchall()]

    if not allowed_ids:
        raise HTTPException(
            status_code=404,
            detail="No completed documents found. Upload and wait for processing to finish.",
        )

    try:
        rag_result = await query_rag(
            db=db,
            query=request.query,
            top_k=request.top_k,
            document_ids=allowed_ids,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    sources = [
        SourceChunk(
            document_id=chunk["document_id"],
            document_name=chunk["document_name"],
            chunk_text=chunk["text"],
            chunk_index=chunk["chunk_index"],
            page_number=chunk["page_number"],
            similarity_score=round(chunk["similarity"], 4),
        )
        for chunk in rag_result["sources"]
    ]

    return QueryResponse(
        query=request.query,
        answer=rag_result["answer"],
        sources=sources,
        model=rag_result["model"],
    )
