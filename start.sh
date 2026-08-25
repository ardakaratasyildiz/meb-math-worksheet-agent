#!/bin/bash
set -e

echo "[startup] Grade 8 + LGS ingest kontrol ediliyor..."
PYTHONIOENCODING=utf-8 python scripts/ingest_to_chroma.py 2>&1
PYTHONIOENCODING=utf-8 python scripts/ingest_textbook.py --grade 8 2>&1

echo "[startup] Ingest tamam. Sunucu baslatiliyor..."

# --forwarded-allow-ips: GERCEK ziyaretci IP'sini X-Forwarded-For'dan cozmek icin
# ZORUNLU. Varsayilan "127.0.0.1" ve Render uygulamaya kendi ic IP'siyle (10.x)
# bagladigi icin XFF HIC OKUNMUYORDU: soket peer'i proxy oldugundan rate-limit
# kimligi (app/security.py::_identifier -> get_remote_address) TUM anonim
# ziyaretcilerde AYNI cikiyordu -> hepsi tek kovayi paylasiyor, 5/dk + 30/saat
# sinirini birbirinden yiyorlardi (kanit: prod log'unda istemci 10.24.184.2).
#
# NEDEN "*" DEGIL: uvicorn 0.41 `always_trust` modunda XFF'in EN SOLUNDAKI
# girdiyi alir (ProxyHeadersMiddleware._TrustedHosts.get_trusted_client_host) —
# o girdi tamamen istemcinin yazdigi degerdir, yani saldirgan her istekte farkli
# IP uydurup rate-limit kovasi acabilir (maliyet-DoS). CIDR verildiginde ise
# liste SAGDAN taranir ve guvenilmeyen ilk girdi alinir: Render'in ekledigi
# gercek IP kazanir, uydurma soldaki girdi yok sayilir.
#
# Deger env ile override edilebilir (render.yaml: FORWARDED_ALLOW_IPS).
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-10.0.0.0/8}"
