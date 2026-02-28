"""
FastAPI application entry point for OCR-to-RAG pipeline.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import get_settings
from app.database import init_db
from app.routers import upload, documents, query, auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("ocrtorag")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database...")
    await init_db()
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    (Path(settings.storage_dir) / "uploads").mkdir(exist_ok=True)
    (Path(settings.storage_dir) / "pdfs").mkdir(exist_ok=True)
    logger.info("OCR-to-RAG API is online.")
    yield
    logger.info("Shutting down...")


from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="OCR-to-RAG API",
    description="Upload docs → OCR → Searchable PDF → RAG with Gemini 2.5 Flash | Auth enabled",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(query.router)

@app.get("/health", tags=["system"])
async def health():
    """Cloud Run / General Health Check."""
    return {"status": "ok", "service": "OCR-to-RAG API", "version": "1.1.0"}

# --- Serving Frontend ---
# Mount static files (JS, CSS, etc.)
# We assume 'dist' folder is at /app/frontend/dist in Docker
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_path.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Prevent serving API routes through this (FastAPI matches routers first, but just in case)
        if full_path.startswith("api") or full_path.startswith("docs"):
             return None 
             
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(), status_code=200)
        return {"error": "Frontend build not found."}
else:
    @app.get("/", tags=["system"])
    async def index():
        return {"message": "API is online.", "frontend_status": "not_bundled"}
