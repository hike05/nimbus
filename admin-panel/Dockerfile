FROM python:3.11-alpine

# Install system dependencies including tini
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    tini

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy core interfaces from parent directory
COPY ../core/interfaces.py /app/core/

# Create non-root user with proper permissions
RUN addgroup -g 1000 appuser && \
    adduser -D -s /bin/sh -u 1000 -G appuser appuser && \
    mkdir -p /var/lib/admin && \
    chown -R appuser:appuser /app /var/lib/admin && \
    chmod 755 /var/lib/admin

# Switch to non-root user
USER appuser

# Set Python path
ENV PYTHONPATH=/app:/app/core

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health', timeout=5)" || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Run application
CMD ["python", "app.py"]