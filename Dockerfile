# Sprint 6 — Render production image. Lokalde Docker Desktop YOK; bu Dockerfile
# yalnızca Render'ın otomatik build pipeline'ı için tasarlandı. CI/Render üzerinde
# build edilir; lokal `docker compose up` hedefi bilerek atlandı.
#
# ChromaDB persistans stratejisi:
#   - Knowledge base (chroma_db) build sırasında image'a COPY edilir.
#   - Runtime'da yazılan history.sqlite3 + generation_cache repo'da yok; ilk
#     boot'ta sıfırdan oluşur (cache havuzu zamanla dolar).
#   - Render free tier kalıcı disk vermiyor; restart sonrası cache reset olur,
#     müfredat verisi (chroma_db) image'da geldiği için kayıp yok.

FROM python:3.13-slim AS base

# pip yavaşlık / cache şişmesin
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ChromaDB hnswlib için gcc + g++ gerekiyor
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bağımlılıkları önce yükle — kod değişiminde docker layer cache korunur
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Uygulama kodu
COPY app ./app
COPY scripts ./scripts

# Müfredat / vector store (büyük ama tek seferlik)
COPY knowledge_base ./knowledge_base

# Non-root çalışma kullanıcısı (Render best practice)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Render $PORT'u runtime'da inject eder; default 8000.
ENV PORT=8000
EXPOSE 8000

# Healthcheck — Render bunu kullanmasa da Docker run'da işe yarar
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail "http://localhost:${PORT}/healthz" || exit 1

# Shell formu: $PORT expand edilsin
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
