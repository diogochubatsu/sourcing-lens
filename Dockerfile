FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY app/backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code
COPY app/backend/ /app/backend/
COPY scripts/ /app/scripts/
COPY config/ /app/config/

# Create data directory
RUN mkdir -p /app/data/images

WORKDIR /app/backend

EXPOSE 5000

CMD ["python", "main.py"]
