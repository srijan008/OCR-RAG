# Stage 1: Build the React application
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend

# Copy package.json and package-lock.json
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY frontend/ ./

# Build the application
# Use a build argument for the API URL (defaults to root relative in production)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Backend + Production
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy the rest of the backend code
COPY backend/ ./backend/

# Copy the built frontend assets from Stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create storage directories
RUN mkdir -p /app/backend/storage/uploads /app/backend/storage/pdfs

# Expose port 8000
EXPOSE 8000

# Set working directory to backend to run main.py
WORKDIR /app/backend

# Run the backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
