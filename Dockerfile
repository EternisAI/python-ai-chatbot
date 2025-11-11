# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for state storage
RUN mkdir -p /app/data

# Set environment variables (these will be overridden by docker-compose or -e flags)
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python3", "app.py"]

