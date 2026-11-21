FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (remove playwright since it's in the base image)
RUN grep -v "playwright" requirements.txt > requirements_filtered.txt && \
    pip install --no-cache-dir -r requirements_filtered.txt && \
    pip install --no-cache-dir playwright==1.45.0 && \
    echo "Installing Playwright browsers..." && \
    python -m playwright install chromium && \
    echo "✅ Chromium installed successfully"

# Copy application
COPY app.py .
COPY watcher.py .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Start application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "300", "--log-level", "info"]
