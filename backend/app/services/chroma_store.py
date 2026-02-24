"""
ChromaDB Cloud vector store service.
Connects to ChromaDB Cloud using API key + tenant + database.
Stores chunk text + Cohere embeddings — one collection shared, filtered by user via document_id.
"""
import chromadb
from app.config import get_settings

settings = get_settings()

_client = None
_collection = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            ssl=True,
            host="api.trychroma.com",
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
            headers={"x-chroma-token": settings.chroma_api_key},
        )
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert_chunks(
    document_id: int,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> int:
    """Upsert chunk embeddings into ChromaDB Cloud."""
    if not chunks or not embeddings:
        return 0

    collection = get_collection()
    ids       = [f"doc{document_id}_chunk{c['chunk_index']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "chunk_index": c["chunk_index"],
            "page_number": c["page_number"],
        }
        for c in chunks
    ]

    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return len(ids)


def search_chunks(
    query_embedding: list[float],
    top_k: int = 5,
    document_ids: list[int] | None = None,
) -> list[dict]:
    """Cosine similarity search in ChromaDB Cloud. Filtered by document_ids."""
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    where = None
    if document_ids and len(document_ids) == 1:
        where = {"document_id": {"$eq": document_ids[0]}}
    elif document_ids and len(document_ids) > 1:
        where = {"document_id": {"$in": document_ids}}

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(top_k, count),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for i, doc_text in enumerate(results["documents"][0]):
        meta     = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        similarity = max(0.0, 1.0 - distance)
        output.append({
            "text":        doc_text,
            "document_id": meta["document_id"],
            "chunk_index": meta["chunk_index"],
            "page_number": meta["page_number"],
            "similarity":  round(similarity, 4),
        })
    return output


def delete_document_chunks(document_id: int) -> None:
    """Remove all chunks for a document from ChromaDB Cloud."""
    collection = get_collection()
    results = collection.get(where={"document_id": {"$eq": document_id}})
    if results["ids"]:
        collection.delete(ids=results["ids"])
