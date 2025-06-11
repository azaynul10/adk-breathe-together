# Dockerfile for Transnational AQMS
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
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create agents directory and __init__.py files if they don't exist
RUN mkdir -p agents schemas communication && \
    touch agents/__init__.py schemas/__init__.py communication/__init__.py

# Create non-root user for security
RUN useradd -m -u 1000 aqms && chown -R aqms:aqms /app
USER aqms

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV COUNTRY_CODE=""
ENV SERVICE_TYPE=""
ENV ENVIRONMENT="production"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "demo_server.py", "main.py", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]