# OCR-to-RAG Pipeline: Technical Trade-offs & Future Roadmap

This document outlines the key architectural decisions and trade-offs made during the development of the OCR-to-RAG application, along with proposed improvements for future iterations.

## ⚖️ Architectural Trade-offs

### 1. Unified Docker Image vs. Microservices
- **Decision**: Consolidated frontend (React) and backend (FastAPI) into a single multi-stage Docker image served on port 8080.
- **Trade-off**: Simplified deployment (specifically for Google Cloud Run) and reduced orchestration complexity. However, it sacrifices the ability to scale the frontend and backend independently and adds slight overhead to the backend which now serves static files.

### 2. Local OCR (Tesseract) vs. Cloud OCR APIs
- **Decision**: Utilized Tesseract OCR running within the Docker container.
- **Trade-off**: Zero per-page cost and high privacy (data never leaves the container for OCR). The trade-off is lower accuracy on handwritten or highly complex layouts compared to premium services like Google Vision or AWS Textract, and higher CPU utilization during processing.

### 3. Hybrid Storage: Relational (PostgreSQL) + Vector (ChromaDB)
- **Decision**: Stored user/document metadata in PostgreSQL and vector embeddings in ChromaDB Cloud.
- **Trade-off**: Provides robust user management and relational integrity for the library, but introduces "split-brain" risks where a deletion must succeed in two different systems. A pure Vector-only approach was rejected to ensure reliable authentication and document ownership logic.

### 4. Direct Processing vs. Task Queues
- **Decision**: Integrated OCR and Embedding directly into the request-response lifecycle (or simple async tasks).
- **Trade-off**: Much simpler architecture without the need for Redis or Celery. The risk is that very large PDFs could time out or consume all available worker threads, leading to a degraded user experience for concurrent users.

---

## 🚀 Future Improvements

### 1. Asynchronous Task Orchestration
Implement **Celery + Redis** to handle document processing. This would allow the user to navigate away immediately after upload and receive a notification (or via WebSocket) when the RAG pipeline is complete.

### 2. Multi-Modal Embedding & Advanced OCR
Transition to **Layout-aware OCR** (like DocTR or Azure Document Intelligence) to better preserve tables and multi-column headers, which significantly improves RAG retrieval accuracy.

### 3. PDF Preview & Annotation
Add a frontend PDF viewer (pdf.js) that allows users to see exactly which parts of the document the AI is citing, perhaps even highlighting the text in the PDF in real-time.

### 4. Streaming Responses
Update the query endpoint to support **Server-Sent Events (SSE)** or WebSockets to stream the LLM response character-by-character, making the interface feel much more responsive.

### 5. Independent Scaling
If traffic grows, split the frontend (to a CDN/Static Host) and the backend (to an auto-scaling cluster) to optimize costs and performance.
