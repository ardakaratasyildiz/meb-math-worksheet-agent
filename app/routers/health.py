"""Liveness ve readiness endpoint'leri.

- /healthz → process ayakta mı (Render & UptimeRobot ping hedefi).
- /readyz  → bağımlılıklar hazır mı (ChromaDB ulaşılabilir + Gemini key var).

Mevcut /health endpoint'i (app/main.py) basit OK döndürmeye devam eder; eski
client'ları kırmamak için saklı tutuldu.
"""
from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.config import settings
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
