FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libappindicator1 \
    libappindicator3-1 \
    libdbus-1-3 \
    libxss1 \
    libxrandr2 \
    xdg-utils \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (with debugging)
RUN echo "Installing Playwright browsers..." && \
    python -m playwright install chromium && \
    echo "✅ Chromium installed successfully"

# Copy application
COPY app.py .
COPY watcher.py .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)"

# Start application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "300", "--log-level", "info"]
