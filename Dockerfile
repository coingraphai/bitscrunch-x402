# Use Python 3.11 with OpenSSL support
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY .env.example .env.example

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8001 8002 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "backend.facilitator_server:app", "--host", "0.0.0.0", "--port", "8002"]
