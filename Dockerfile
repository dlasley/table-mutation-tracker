FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install only Chromium (skip Firefox/WebKit to save ~800MB)
RUN playwright install chromium

# Copy application code
COPY src/ src/
COPY config/ config/

ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "src.webhook:app", "--host", "0.0.0.0", "--port", "8080"]
