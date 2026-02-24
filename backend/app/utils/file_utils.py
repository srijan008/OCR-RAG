import os
import uuid
import aiofiles
from pathlib import Path
from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".pdf"}


def get_storage_paths() -> tuple[Path, Path]:
    """Return (uploads_dir, pdfs_dir), creating them if needed."""
    base = Path(settings.storage_dir)
    uploads = base / "uploads"
    pdfs = base / "pdfs"
    uploads.mkdir(parents=True, exist_ok=True)
    pdfs.mkdir(parents=True, exist_ok=True)
    return uploads, pdfs


def validate_file_extension(filename: str) -> str:
    """Return the extension if valid, else raise ValueError."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


def generate_unique_filename(original_filename: str) -> str:
    """Generate a UUID-prefixed filename to avoid collisions."""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


async def save_upload(file_bytes: bytes, filename: str) -> str:
    """Save raw upload bytes to the uploads directory. Returns absolute path."""
    uploads_dir, _ = get_storage_paths()
    dest = uploads_dir / filename
    async with aiofiles.open(dest, "wb") as f:
        await f.write(file_bytes)
    return str(dest)


def get_pdf_path(stem: str) -> str:
    """Return the destination path for a generated PDF."""
    _, pdfs_dir = get_storage_paths()
    return str(pdfs_dir / f"{stem}.pdf")
