"""Documents router: list, detail, download — scoped to the authenticated user."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Document, User
from app.schemas import DocumentResponse, DocumentListResponse
from app.dependencies import get_current_user
from app.services.chroma_store import delete_document_chunks

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return paginated documents belonging to the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip).limit(limit)
    )
    docs = result.scalars().all()
    count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar()
    return DocumentListResponse(documents=list(docs), total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single document by ID (only if it belongs to the current user)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document + ChromaDB chunks (only owner can delete)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    delete_document_chunks(document_id)
    
    # Delete physical files
    if doc.original_path:
        Path(doc.original_path).unlink(missing_ok=True)
    if doc.pdf_path:
        Path(doc.pdf_path).unlink(missing_ok=True)
        
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted successfully."}


@router.get("/{document_id}/download")
async def download_pdf(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the searchable PDF (only owner)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc.pdf_path or not Path(doc.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not yet generated or processing failed.")
    return FileResponse(
        path=doc.pdf_path,
        media_type="application/pdf",
        filename=f"{Path(doc.original_filename).stem}_searchable.pdf",
    )
