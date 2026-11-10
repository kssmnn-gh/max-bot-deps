FROM python:3.11-slim-bookworm

# OCR and language data are installed at build time, not on every bot restart.
RUN printf '%s\n' 'Acquire::ForceIPv4 "true";' 'Acquire::Retries "5";' \
    'Acquire::http::Timeout "30";' 'Acquire::https::Timeout "30";' \
    > /etc/apt/apt.conf.d/80-build-network \
    && apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng libreoffice-writer ca-certificates fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt constraints-v12-py311.txt ./
# One heavy layer avoids repeatedly snapshotting all ML/browser dependencies.
# Keep the manager's dependency resolution separate from the bot's constraints.
RUN pip install --no-cache-dir --timeout 120 --retries 8 -c constraints-v12-py311.txt -r requirements.txt \
    && python -m playwright install --with-deps --only-shell chromium \
    && pip install --no-cache-dir --timeout 120 --retries 8 Flask==3.1.3 gunicorn==26.2.0 \
    && rm -rf /var/lib/apt/lists/*

