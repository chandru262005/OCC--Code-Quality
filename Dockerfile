# Multi-stage build for smaller image
  FROM python:3.11-slim as base

  # Set environment variables
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      PIP_NO_CACHE_DIR=1

  WORKDIR /app

  # Install system dependencies (git needed for cloning repos)
  RUN apt-get update && \
      apt-get install -y --no-install-recommends git && \
      rm -rf /var/lib/apt/lists/*

  # Install Python dependencies
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY . .

  # Create non-root user
  RUN useradd -m appuser && \
      mkdir -p /tmp/cqg_uploads /tmp/cqg_repos && \
      chown -R appuser:appuser /app /tmp/cqg_uploads /tmp/cqg_repos
  USER appuser

  EXPOSE 8000

  HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
      CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]