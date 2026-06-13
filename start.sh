#!/bin/bash
set -e

echo "[startup] Grade 8 + LGS ingest kontrol ediliyor..."
PYTHONIOENCODING=utf-8 python scripts/ingest_to_chroma.py 2>&1
PYTHONIOENCODING=utf-8 python scripts/ingest_textbook.py --grade 8 2>&1

echo "[startup] Ingest tamam. Sunucu baslatiliyor..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
