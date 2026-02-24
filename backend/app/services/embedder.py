"""
Cohere embedding service using embed-english-v3.0 (1024 dimensions).
"""
import cohere
from app.config import get_settings

settings = get_settings()
_client: cohere.Client | None = None


def get_cohere_client() -> cohere.Client:
    global _client
    if _client is None:
        _client = cohere.Client(api_key=settings.cohere_api_key)
    return _client


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings for document storage.
    Uses input_type='search_document' as required by Cohere v3.
    """
    if not texts:
        return []
    client = get_cohere_client()

    # Cohere API has a max batch size of 96
    all_embeddings: list[list[float]] = []
    batch_size = 90
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embed(
            texts=batch,
            model=settings.cohere_model,
            input_type="search_document",
            embedding_types=["float"],
        )
        all_embeddings.extend(response.embeddings.float_)
    return all_embeddings


def embed_query(text: str) -> list[float]:
    """
    Embed a single query string.
    Uses input_type='search_query' as required by Cohere v3.
    """
    client = get_cohere_client()
    response = client.embed(
        texts=[text],
        model=settings.cohere_model,
        input_type="search_query",
        embedding_types=["float"],
    )
    return response.embeddings.float_[0]
