# Use official Python image
FROM python:3.11-slim

# Prevent .pyc files + enable logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (important for Google Cloud + cryptography libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better caching)
COPY pyproject.toml ./

# Install dependencies using pip (PEP 517 build)
RUN pip install --upgrade pip && pip install .

# Copy entire project
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Start FastAPI app. Reload mode is development-only: the app writes logs under
# the project directory, which would otherwise cause Uvicorn to restart forever.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
