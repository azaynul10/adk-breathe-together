# syntax=docker/dockerfile:1

# --- Builder stage ---
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --user -r requirements.txt

# --- Runtime stage ---
FROM python:3.11-slim
WORKDIR /app

# Copy only necessary files
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .

# Expose port (Cloud Run default is 8080)
EXPOSE 8080

# Use environment variable for port if set
ENV PORT=8080

# Entrypoint for FastAPI (main.py must define app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]