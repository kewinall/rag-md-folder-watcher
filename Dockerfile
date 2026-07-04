FROM python:3.12-slim-bookworm

ARG VERSION=1.0.1
ARG SOURCE_REPOSITORY=https://github.com/unknown/rag-md-folder-watcher

LABEL org.opencontainers.image.title="RAG Markdown Folder Watcher" \
      org.opencontainers.image.description="Automatically converts files from a mounted folder into RAG-ready Markdown." \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="${SOURCE_REPOSITORY}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_ROOT=/data \
    HOME=/tmp/home \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libreoffice-writer \
       libreoffice-calc \
       libreoffice-impress \
       tesseract-ocr \
       tesseract-ocr-eng \
       tesseract-ocr-chi-tra \
       fonts-noto-cjk \
       tini \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --disable-pip-version-check --requirement requirements.txt

COPY app ./app
COPY rag_md_converter ./rag_md_converter
COPY VERSION ./VERSION
COPY LICENSE ./LICENSE

RUN mkdir -p /data /tmp/home \
    && chown -R appuser:appgroup /app /data /tmp/home

USER appuser

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "app.watcher"]
