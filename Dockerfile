# Dockerfile for FastAPI backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/
COPY openapi_specs/ openapi_specs/

# Create data directories
RUN mkdir -p /app/data /app/generated_tests

# Environment variables
ENV DATABASE_PATH=/app/data/app.db
ENV GENERATED_TESTS_DIR=/app/generated_tests
ENV DEFAULT_TARGET_URL=http://example-api:8001

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
