"""
This script demonstrates how to access:
1. The Intermediate OCR Results for a document
2. The Hierarchical RAG retrieval results (the sources used by the LLM)

Run this script to see an example, or inspect the code to see how to call the API.
"""
import httpx
import asyncio

API_URL = "http://localhost:8000"
# NOTE: Replace 'test_token' with a real JWT token if authentication is required
HEADERS = {"Authorization": "Bearer test_token"}

async def demonstrate_results():
    async with httpx.AsyncClient() as client:
        print("--- Fetching your available documents ---")
        # 1. First, get a list of your documents
        list_res = await client.get(f"{API_URL}/documents", headers=HEADERS)
        if list_res.status_code != 200:
            print(f"Auth or server error: {list_res.text}")
            print("Note: If you have authentication enabled, you need to log in via the frontend first to get a token.")
            return
            
        docs = list_res.json().get("documents", [])
        if not docs:
            print("You have no documents uploaded. Please upload a document via the frontend first.")
            return
            
        doc_id = docs[0]["id"]
        
        # 2. Get Intermediate OCR Result
        print(f"\n--- Intermediate OCR text for Document ID: {doc_id} ---")
        doc_res = await client.get(f"{API_URL}/documents/{doc_id}", headers=HEADERS)
        doc_data = doc_res.json()
        
        ocr_text = doc_data.get("ocr_text")
        if ocr_text:
            # Print the first 500 characters
            print(f"Status: {doc_data['status']}")
            print("Extracted Text Preview:")
            print(ocr_text[:500] + "...\n[TRUNCATED]")
        else:
            print("No OCR text available yet. Is the document finished processing?")

        
        # 3. Get RAG Retrieval Results (the sources)
        print("\n--- Hierarchical RAG Retrieval Results ---")
        query = "What is this document about?"
        print(f"Query: '{query}'")
        
        rag_res = await client.post(
            f"{API_URL}/rag/query", 
            json={"query": query, "top_k": 3},
            headers=HEADERS
        )
        
        if rag_res.status_code == 200:
            rag_data = rag_res.json()
            sources = rag_data.get("sources", [])
            print(f"\nLLM Answer: {rag_data['answer']}")
            print(f"\nNumber of Parent Chunks retrieved for context: {len(sources)}")
            
            for idx, source in enumerate(sources, 1):
                print(f"\nSource {idx} (from {source['document_name']}, page {source['page_number']})")
                print(f"Parent Chunk length: {len(source['text'])} characters")
                print(f"Preview: {source['text'][:200]}...")
        else:
            print(f"RAG query failed: {rag_res.text}")

if __name__ == "__main__":
    asyncio.run(demonstrate_results())
