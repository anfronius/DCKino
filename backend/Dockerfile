FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements_minimal.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/backend_server.py .
COPY backend/utils/ ./utils/

# Copy shared config directory (contains title_processing.json needed by title_normalizer)
COPY shared/ ./shared/

# Create directories for data and posters
RUN mkdir -p /app/data /app/data_backup /app/posters

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3001/health', timeout=5)" || exit 1

# Run the server
CMD ["python", "-m", "uvicorn", "backend_server:app", "--host", "0.0.0.0", "--port", "3001", "--reload"]