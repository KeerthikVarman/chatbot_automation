# Use official lightweight Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Explicitly disable automatic webhooks, automatic background ETL pipelines, and usage stats
ENV AUTOMATIC_WEBHOOKS=false
ENV AUTOMATIC_ETL=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Set working directory inside container
WORKDIR /app

# Install system dependencies for SSL certificates and curl healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY . .

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Healthcheck targeting FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command to start FastAPI application server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
