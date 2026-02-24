from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str
    cohere_api_key: str
    jwt_secret_key: str = "change-me-in-production-use-a-long-random-secret"

    # Database
    database_url: str

    # OCR
    tesseract_cmd: str = "tesseract"

    # Storage
    storage_dir: str = "./storage"

    # ChromaDB Cloud
    chroma_api_key: str
    chroma_tenant: str
    chroma_database: str
    chroma_collection: str = "ocrtorag_chunks"

    # App
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    cohere_model: str = "embed-english-v3.0"
    embed_dimension: int = 1024

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
