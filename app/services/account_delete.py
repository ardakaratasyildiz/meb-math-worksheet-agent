"""Kullanıcı hesabını TAMAMEN silme — Apple 5.1.1(v) / Google Play veri-silme zorunluluğu.

Tüm kullanıcıya ait satırları TEK bağlantı + TEK commit içinde siler (worksheet
geçmişi, quiz'ler, denemeler, ustalık, paylaşımlar, çalışma programı, ek kredi,
e-posta tercihi, abonelik, veli/öğrenci bağı, sınıflar). Muhasebe/maliyet kaydı
(usage_ledger, billing_events) VUK saklama zorunluluğu nedeniyle SİLİNMEZ, geri
döndürülemez biçimde ANONİMLEŞTİRİLİR (tenant_id → "deleted_" + sha256 kısaltması).

Tablo eksikse (Turso migrasyon gecikmesi) o adım atlanır + loglanır, diğerleri
devam eder — tek bir eksik tablo tüm silme işlemini düşürmez (worksheet_history/
usage_ledger deseniyle aynı fail-soft yaklaşım). İdempotent: ikinci çağrıda zaten
silinmiş satırlar için 0 döner, hata fırlatmaz.

DOKUNULMAYAN tablolar: `history` (tenant'a bağlı değil, RAG tekrar-önleme),
`generation_cache`, `spare_questions`, `admin_audit` (denetim izi — silme
işleminin KENDİSİ ayrıca oraya kaydedilir, bkz. app/routers/me.py).

Bilinen risk (kasıtlı tasarım — çağıran/ürün kararı): `quizzes` silinirken o
quiz'lere ait TÜM `attempts` satırları da silinir; bu, BAŞKA kullanıcıların o
quiz'i çözerken bıraktığı denemeleri de kapsar (paylaşılan/ödev quiz'i). Aktif
bir aboneliği (`subscriptions`) olan kullanıcı hesabını silerse ödeme sağlayıcı
tarafında (iyzico/RevenueCat) iptal AYRICA yapılmaz — yalnız yerel satır silinir.
"""
from __future__ import annotations

import hashlib
import logging

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


def anon_tenant_id(tenant_id: str) -> str:
    """Tenant kimliğini geri döndürülemez biçimde takma isimlendirir (VUK saklama).

    Aynı tenant_id her zaman aynı takma adı üretir (deterministik) ama tenant_id
    takma addan GERİ ÇIKARILAMAZ (tek yönlü hash). Public — çağıran (router) aynı
    takma adı `admin_audit.target` alanına yazmak için tekrar üretebilsin diye.
    """
    return "deleted_" + hashlib.sha256(tenant_id.encode("utf-8")).hexdigest()[:16]


def _run(conn, results: dict[str, int], key: str, sql: str, params: tuple) -> None:
    """Tek bir DELETE/UPDATE çalıştırır; etkilenen satır sayısını `results[key]`e
    EKLER (üzerine yazmaz — aynı tabloya birden çok kural uygulanabilir, örn.
    `attempts` iki farklı WHERE'den beslenir).

    Tablo yoksa (Turso migrasyon gecikmesi) ya da başka bir SQL hatası olursa
    hatayı yutar + loglar; diğer adımlar etkilenmeden devam eder.
    """
    try:
        cur = conn.execute(sql, params)
        results[key] = results.get(key, 0) + int(cur.rowcount or 0)
    except Exception as exc:  # noqa: BLE001 — bir tablo eksikse diğerleri etkilenmesin
        logger.warning("Hesap silme adımı atlandı (%s): %s", key, exc)


def purge_tenant(tenant_id: str) -> dict[str, int]:
    """Bir kullanıcının TÜM verisini siler/anonimleştirir. {tablo: satır_sayısı} döner.

    Sıra ÖNEMLİ: bağımlı satırlar (attempts, classroom_members, assignments) üst
    tablo (quizzes, classrooms) silinmeden ÖNCE temizlenir — subquery hâlâ üst
    tabloyu görebilmeli. usage_ledger/billing_events SİLİNMEZ, anonimleştirilir;
    sayıları `*_anonymized` anahtarıyla döner.

    tenant_id boşsa no-op ({} döner) — çağıran (router) zaten 401 ile keser.
    """
    if not tenant_id:
        return {}
    results: dict[str, int] = {}
    conn = db_connect(settings.history_db_path)
    try:
        # ── Çalışma kağıdı geçmişi ────────────────────────────────────────────
        _run(
            conn, results, "worksheet_history",
            "DELETE FROM worksheet_history WHERE tenant_id = ?", (tenant_id,),
        )

        # ── Quiz'ler + bağımlı denemeler (BAŞKALARININ bu quiz'lerdeki denemeleri
        # de silinir — quiz sahibi silinince deneme öksüz kalır; bkz. modül docstring) ──
        _run(
            conn, results, "attempts",
            "DELETE FROM attempts WHERE quiz_id IN "
            "(SELECT id FROM quizzes WHERE owner_tenant_id = ?)", (tenant_id,),
        )
        _run(
            conn, results, "quizzes",
            "DELETE FROM quizzes WHERE owner_tenant_id = ?", (tenant_id,),
        )
        # Kullanıcının KENDİ çözüm denemeleri (başkasının quiz'inde olsa bile).
        _run(
            conn, results, "attempts",
            "DELETE FROM attempts WHERE solver_tenant_id = ?", (tenant_id,),
        )

        _run(
            conn, results, "mastery_state",
            "DELETE FROM mastery_state WHERE tenant_id = ?", (tenant_id,),
        )

        # ── Paylaşımlar: sahip olduğu + kendisine hedeflenmiş ────────────────
        _run(
            conn, results, "shares",
            "DELETE FROM shares WHERE owner_tenant_id = ? OR target_tenant_id = ?",
            (tenant_id, tenant_id),
        )

        _run(
            conn, results, "study_plans",
            "DELETE FROM study_plans WHERE tenant_id = ?", (tenant_id,),
        )
        _run(
            conn, results, "top_up_credits",
            "DELETE FROM top_up_credits WHERE tenant_id = ?", (tenant_id,),
        )
        _run(
            conn, results, "email_prefs",
            "DELETE FROM email_prefs WHERE tenant_id = ?", (tenant_id,),
        )
        _run(
            conn, results, "subscriptions",
            "DELETE FROM subscriptions WHERE tenant_id = ?", (tenant_id,),
        )

        # ── Veli ↔ öğrenci bağı ───────────────────────────────────────────────
        _run(
            conn, results, "parent_codes",
            "DELETE FROM parent_codes WHERE student_tenant_id = ?", (tenant_id,),
        )
        _run(
            conn, results, "parent_links",
            "DELETE FROM parent_links WHERE parent_tenant_id = ? OR student_tenant_id = ?",
            (tenant_id, tenant_id),
        )

        # ── Sınıflar (sahibiyse) + bağımlı üyelik/ödev, SONRA sınıf satırı ────
        _run(
            conn, results, "classroom_members",
            "DELETE FROM classroom_members WHERE classroom_id IN "
            "(SELECT id FROM classrooms WHERE owner_tenant_id = ?)", (tenant_id,),
        )
        _run(
            conn, results, "assignments",
            "DELETE FROM assignments WHERE classroom_id IN "
            "(SELECT id FROM classrooms WHERE owner_tenant_id = ?)", (tenant_id,),
        )
        _run(
            conn, results, "classrooms",
            "DELETE FROM classrooms WHERE owner_tenant_id = ?", (tenant_id,),
        )
        # Kullanıcının ÜYE olduğu (sahibi olmadığı) sınıflardaki üyeliği.
        _run(
            conn, results, "classroom_members",
            "DELETE FROM classroom_members WHERE student_tenant_id = ?", (tenant_id,),
        )

        # ── Anonimleştirme (silinmez — muhasebe/VUK saklama) ─────────────────
        anon = anon_tenant_id(tenant_id)
        _run(
            conn, results, "usage_ledger_anonymized",
            "UPDATE usage_ledger SET tenant_id = ? WHERE tenant_id = ?",
            (anon, tenant_id),
        )
        _run(
            conn, results, "billing_events_anonymized",
            "UPDATE billing_events SET tenant_id = ? WHERE tenant_id = ?",
            (anon, tenant_id),
        )

        conn.commit()
    finally:
        try:
            conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Hesap silme bağlantısı kapatılamadı: %s", exc)
    return results


__all__ = ["purge_tenant", "anon_tenant_id"]
