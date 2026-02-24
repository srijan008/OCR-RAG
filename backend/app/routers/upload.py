"""Upload router: accepts files, runs ingestion pipeline for authenticated user."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Document, DocumentStatus, User
from app.schemas import UploadResponse
from app.dependencies import get_current_user
from app.utils.file_utils import validate_file_extension, generate_unique_filename, save_upload
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document. Only accessible to authenticated users."""
    try:
        ext = validate_file_extension(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    unique_name = generate_unique_filename(file.filename)
    saved_path = await save_upload(contents, unique_name)

    doc = Document(
        user_id=current_user.id,
        filename=unique_name,
        original_filename=file.filename,
        file_type=ext,
        original_path=saved_path,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(
        _run_pipeline_bg,
        document_id=doc.id,
        file_path=saved_path,
        file_type=ext,
    )

    return UploadResponse(
        message="File uploaded successfully. Processing started.",
        document=doc,
    )


async def _run_pipeline_bg(document_id: int, file_path: str, file_type: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await run_pipeline(session, document_id, file_path, file_type)
