FROM node:18-slim AS frontend-build

WORKDIR /app/frontend


COPY frontend/package*.json ./


RUN npm install


COPY frontend/ ./


ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build


FROM python:3.11-slim-bookworm

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/

RUN pip install --no-cache-dir -r ./backend/requirements.txt

COPY backend/ ./backend/

COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/backend/storage/uploads /app/backend/storage/pdfs

EXPOSE 8080

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]