"""Pro / Pro+ ayrımı — kağıt sayısı DIŞINDAKİ plan sınırları.

Pytest gerektirmez — `python tests/test_plan_limits.py`. LLM/ağ çağrısı yok.

Neden var: Pro ile Pro+ arasındaki tek fark kağıt adediydi; Pro+ cezbedici
değildi. 2026-08-21 denetiminde iki şey çıktı:

  1. Paywall "Aile paylaşımı: 3 çocuğa kadar" diyordu ama KODDA SINIR YOKTU —
     `_family_tenants` bağlı tüm çocukları havuza alıyor, yani verdiğimiz sözden
     fazlasını veriyorduk.
  2. "Çoklu sınıf yönetimi" Pro+ ayrıcalığı olarak duyurulacaktı ama sınıf
     sayısına hiç sınır uygulanmıyordu.

Bu test merdiveni kilitler. Seçim ölçütü MARJİNAL MALİYET: Pro+ kağıt başına daha
ince marjlı (₺349/120 = ₺2,91 · Pro ₺199/50 = ₺3,98; kağıt ~₺1,50) → Pro+
ayrıcalıkları üretim maliyetini artırmayan şeyler olmalı (kaç kişi/sınıf havuzu
paylaşıyor), model kalitesi gibi maliyetli şeyler DEĞİL.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.services import entitlements  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


PLANS = (
    entitlements.PLAN_FREE,
    entitlements.PLAN_TRIAL,
    entitlements.PLAN_PRO,
    entitlements.PLAN_PRO_PLUS,
)


def test_classroom_ladder() -> None:
    print("sınıf sayısı merdiveni")
    free, trial, pro, plus = (entitlements.classroom_limit(p) for p in PLANS)
    check(plus > pro, f"Pro+ Pro'dan fazla sınıf ({plus} > {pro})")
    check(free >= 1, f"ücretsizde en az 1 sınıf korunuyor ({free}) — çalışan özellik geri alınmaz")
    check(trial == plus, f"deneme Pro+'ı tattırır ({trial} == {plus})")


def test_family_children_ladder() -> None:
    print("aile paylaşımı merdiveni")
    free, trial, pro, plus = (entitlements.family_children_limit(p) for p in PLANS)
    check(plus == 3, f"Pro+ 3 çocuk — paywall'da duyurulan sayı ({plus})")
    check(pro == 0, f"Pro'da aile paylaşımı kapalı ({pro}) — Pro+ ayrıcalığı")
    check(free == 0, f"ücretsizde kapalı ({free})")
    check(trial == plus, f"deneme Pro+'ı tattırır ({trial} == {plus})")


def test_paper_quota_ladder_unchanged() -> None:
    """Kağıt merdiveni bozulmadı (yeni sınırlar onu etkilememeli)."""
    print("kağıt kotası merdiveni (regresyon)")
    q = {p: entitlements.quota_limit(p) for p in PLANS}
    check(
        q[entitlements.PLAN_PRO] == 50 and q[entitlements.PLAN_PRO_PLUS] == 120,
        f"Pro 50 · Pro+ 120 ({q[entitlements.PLAN_PRO]} · {q[entitlements.PLAN_PRO_PLUS]})",
    )
    check(
        q[entitlements.PLAN_FREE] < q[entitlements.PLAN_PRO],
        "ücretsiz < Pro",
    )


def test_limits_are_enforced_at_creation() -> None:
    """Sınırlar OLUŞTURMA anında uygulanır — mevcut kayıtlar kırılmaz.

    Uçlar `list_owned` / `list_children` sayıp limitle karşılaştırıyor; hesaplama
    yolunda (kota havuzu) filtre YOK. Böylece plan düşen kullanıcının mevcut
    sınıfı/çocuğu sessizce yok olmaz, yalnız yenisini ekleyemez.
    """
    print("sınırlar oluşturma anında (sözleşme)")
    import inspect  # noqa: PLC0415

    from app.routers import classrooms, me  # noqa: PLC0415

    src_cls = inspect.getsource(classrooms.create_classroom)
    check("classroom_limit" in src_cls, "create_classroom sınırı kontrol ediyor")
    check("402" in src_cls or "status_code=402" in src_cls, "sınır aşımı 402 döndürüyor")

    src_link = inspect.getsource(me.link_child)
    check("family_children_limit" in src_link, "link_child sınırı kontrol ediyor")

    # Havuz hesabı sınıra göre KIRPILMAMALI (mevcut bağlar korunur).
    src_family = inspect.getsource(entitlements._family_tenants)
    check(
        "family_children_limit" not in src_family,
        "_family_tenants sınır uygulamıyor — mevcut bağlar korunur",
    )


def main() -> int:
    for fn in (
        test_classroom_ladder,
        test_family_children_ladder,
        test_paper_quota_ladder_unchanged,
        test_limits_are_enforced_at_creation,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: plan sınırı testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
