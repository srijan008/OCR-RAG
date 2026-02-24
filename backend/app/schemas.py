from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models import DocumentStatus


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()


# ─── Document Schemas ─────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    page_count: int
    chunk_count: int
    ocr_confidence_avg: float
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


# ─── Query Schemas ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    document_ids: Optional[list[int]] = None


class SourceChunk(BaseModel):
    document_id: int
    document_name: str
    chunk_text: str
    chunk_index: int
    page_number: int
    similarity_score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceChunk]
    model: str


# ─── Upload Response ──────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse
