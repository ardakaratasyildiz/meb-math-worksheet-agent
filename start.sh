#!/bin/bash
set -e

echo "[startup] Grade 8 + LGS ingest kontrol ediliyor..."
PYTHONIOENCODING=utf-8 python scripts/ingest_to_chroma.py 2>&1
PYTHONIOENCODING=utf-8 python scripts/ingest_textbook.py --grade 8 2>&1

echo "[startup] Ingest tamam. Sunucu baslatiliyor..."

# --forwarded-allow-ips: GERCEK ziyaretci IP'sini X-Forwarded-For'dan cozmek icin.
# Rate-limit kimligi (app/security.py::_identifier -> get_remote_address) soket
# peer'ina bakiyor; proxy arkasinda bu deger ziyaretci DEGIL ara hop olur ve tum
# anonim trafik ayni kovayi paylasir (5/dk + 30/saat birbirinden yenir).
#
# CANLIDA OLCULEN ZINCIR (GET /diag/client, 2026-08-25):
#   x_forwarded_for = "5.46.235.101, 172.69.150.209, 10.25.117.71"
#   client_host     = 127.0.0.1
# yani: [ziyaretci] -> [Cloudflare edge] -> [Render ic agi] -> (loopback) -> app
#
# uvicorn listeyi SAGDAN tarar ve GUVENILMEYEN ilk girdiyi istemci sayar. O yuzden
# ARADAKI TUM hop'lar (loopback + Render ozel agi + Cloudflare egress araliklari)
# guvenilen listede olmak zorunda; biri eksik kalirsa tarama orada durur ve kimlik
# ziyaretci yerine o hop olur.
#
# NEDEN "*" DEGIL: uvicorn `always_trust` modunda XFF'in EN SOLUNDAKI girdiyi alir;
# o girdi tamamen istemcinin yazdigi degerdir → saldirgan her istekte farkli IP
# uydurup sinirsiz kova acar (maliyet-DoS). Aralik listesiyle ters tarama yapildiginda
# Cloudflare'in ekledigi gercek IP kazanir, soldaki uydurma girdi yok sayilir.
#
# Cloudflare araliklari degisirse (nadiren) buraya eklenmeli — bkz. render.yaml
# FORWARDED_ALLOW_IPS (env override) ve teshis icin GET /diag/client.
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,173.245.48.0/20,103.21.244.0/22,103.22.200.0/22,103.31.4.0/22,141.101.64.0/18,108.162.192.0/18,190.93.240.0/20,188.114.96.0/20,197.234.240.0/22,198.41.128.0/17,162.158.0.0/15,104.16.0.0/13,104.24.0.0/14,172.64.0.0/13,131.0.72.0/22,2400:cb00::/32,2606:4700::/32,2803:f800::/32,2405:b500::/32,2405:8100::/32,2a06:98c0::/29,2c0f:f248::/32}"
