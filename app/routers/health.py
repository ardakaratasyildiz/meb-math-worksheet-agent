"""Liveness ve readiness endpoint'leri.

- /healthz → process ayakta mı (Render & UptimeRobot ping hedefi).
- /readyz  → bağımlılıklar hazır mı (ChromaDB ulaşılabilir + Gemini key var).

Mevcut /health endpoint'i (app/main.py) basit OK döndürmeye devam eder; eski
client'ları kırmamak için saklı tutuldu.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.config import settings
from app.security import require_api_key
from app.services.db_connection import is_turso_enabled
from app.services.retriever import get_retriever
from app.services.worksheet_history import WORKSHEET_HISTORY

router = APIRouter()


# GET + HEAD: UptimeRobot gibi uptime monitor'leri varsayılan olarak HEAD atar.
# Yalnız GET tanımlıysa HEAD → 405 döner ve monitor "down" sanır. Her iki metodu
# da kabul ederek hangi pinger olursa olsun 200 alınır.
@router.api_route("/healthz", methods=["GET", "HEAD"], tags=["system"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["system"])
def readyz(response: Response) -> dict[str, object]:
    checks: dict[str, object] = {}

    checks["gemini_api_key"] = bool(settings.gemini_api_key)

    # DB persistence backend — Turso (kalıcı, restart'a dayanıklı) mı yoksa
    # lokal SQLite (ephemeral diskte; her deploy/cold-start'ta cache+history
    # sıfırlanır) mı? "Üretim geçmişi göremiyorum" teşhisini Render dashboard'a
    # girmeden, tek curl ile yapabilmek için. all_ok'u GATING ETMEZ — lokal
    # SQLite'ta da uygulama çalışır, sadece kalıcılık yoktur (bilgilendirme).
    checks["db_backend"] = "turso" if is_turso_enabled() else "local-sqlite"

    # worksheet_history tablosu canlı bağlantıdan fiilen okunabiliyor mu +
    # kaç kayıt var? "Üretim geçmişi göremiyorum" teşhisi: 0 → hiç kayıt yok
    # (yazma/sync yolu kopuk), >0 → kayıt var, sorun okuma/tenant tarafında.
    # Bilgilendirme amaçlı — all_ok'u GATING ETMEZ (boş tablo geçerli durum).
    try:
        checks["worksheet_history_rows"] = WORKSHEET_HISTORY.total_count()
    except Exception as exc:  # noqa: BLE001
        checks["worksheet_history_rows"] = {"ok": False, "error": str(exc)[:200]}

    retriever = get_retriever()
    if retriever is None:
        checks["chroma"] = {"ok": False, "count": 0}
    else:
        try:
            count = retriever.count()
            checks["chroma"] = {"ok": count > 0, "count": count}
        except Exception as exc:
            checks["chroma"] = {"ok": False, "error": str(exc)[:200]}

    all_ok = bool(checks["gemini_api_key"]) and bool(
        (checks["chroma"] if isinstance(checks["chroma"], dict) else {}).get("ok")
    )
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": all_ok, "checks": checks}


# ── GEÇİCİ TEŞHİS — Gemini 403 incident (2026-07-16). Sonuç alınınca KALDIR. ──
# Render'ın Gemini'ye erişimini SUNUCUNUN KENDİSİNDEN ölçer: çıkış IP'si, SDK
# sürümü, key şekli (sır değil — uzunluk/prefix/whitespace), ve ham vs strip'li
# key ile canlı Gemini çağrısı. "IP bloğu mu, whitespace mı, sürüm mü" sorusunu
# tek istekle kesin ayırır. Public API-key ile gate'li (sır döndürmez).
@router.get("/diag/gemini", tags=["system"])
def diag_gemini(_api_key: str = Depends(require_api_key)) -> dict[str, object]:
    import importlib.metadata
    import os
    import urllib.request

    out: dict[str, object] = {}

    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=6) as r:
            out["egress_ip"] = r.read().decode().strip()
    except Exception as exc:  # noqa: BLE001
        out["egress_ip"] = {"error": str(exc)[:200]}

    try:
        out["genai_version"] = importlib.metadata.version("google-genai")
    except Exception as exc:  # noqa: BLE001
        out["genai_version"] = {"error": str(exc)[:120]}

    k = settings.gemini_api_key or ""
    out["gemini_key_shape"] = {
        "len": len(k),
        "stripped_len": len(k.strip()),
        "prefix": k[:6],
        "has_edge_whitespace": k != k.strip(),
    }

    out["fallback_models"] = settings.fallback_model_list
    out["primary_model"] = settings.gemini_model
    out["region_env"] = (
        os.environ.get("RENDER_REGION")
        or os.environ.get("GOOGLE_CLOUD_LOCATION")
        or "?"
    )

    def _try(key: str) -> dict[str, object]:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="hi",
                config=types.GenerateContentConfig(
                    temperature=0.0, max_output_tokens=1
                ),
            )
            return {"ok": True, "text": (getattr(resp, "text", "") or "")[:40]}
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "type": type(exc).__name__,
                "code": getattr(exc, "code", None),
                "error": str(exc)[:400],
            }

    out["gemini_test_raw"] = _try(k)
    if k != k.strip():
        out["gemini_test_stripped"] = _try(k.strip())
    return out
