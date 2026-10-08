# ==========================================================
# Stage 1: Build Frontend
# ==========================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================================
# Stage 2: Production Python Runtime
# ==========================================================
FROM python:3.11-slim AS production

# Prevent Python from buffering stdout/stderr and creating .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    DATABASE_URL=sqlite:///./data/agriguard.db \
    MODEL_PATH=ml/outputs/agriguard_model.onnx \
    UPLOAD_DIR=uploads

WORKDIR /app

# Install minimal OS dependencies needed for OpenCV headless & runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install production Python dependencies (without PyTorch)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root system user
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser

# Copy application code, knowledge base, ONNX model, and built frontend
COPY backend/ ./backend/
COPY knowledge/ ./knowledge/
COPY ml/outputs/class_names.json ./ml/outputs/class_names.json
COPY ml/outputs/agriguard_model.onnx ./ml/outputs/agriguard_model.onnx
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create storage directories and assign ownership to non-root user
RUN mkdir -p /app/data /app/uploads && \
    chown -R appuser:appgroup /app/data /app/uploads /app

# Switch to non-root user
USER appuser

EXPOSE 10000

# Run uvicorn with a single worker for memory efficiency under 512MB RAM
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
