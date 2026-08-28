"""Ders (subject) registry — çok-ders ekseninin tek giriş noktası.

Kullanım:
    from app.models.enums import SubjectId
    from app.subjects import get_subject, subject_enabled, available_subjects, get_content_module

`get_subject()` varsayılan matematik döner → subject verilmeyen eski çağrılar aynen çalışır.
`subject_enabled()` feature-flag'i SETTINGS'TEN CANLI okur (import-time snapshot değil) →
env/flag flip'i yeniden import gerektirmez. Router'lar kapalı derse 4xx döndürmeli.
`get_content_module()` non-math dersin içerik modülünü (prompt/critic/few-shot/curriculum +
select_kazanimlar/collect_few_shot/DEFAULT_TYPES uniform arayüzü) döner; matematik → None
(matematik akışı kendi klasik yolunu kullanır).

Yeni ders eklemek: paket oluştur (uniform arayüzle) → burada SUBJECTS + SUBJECT_FLAGS +
_CONTENT'e kaydet. Gerisi (agent/router/frontend) otomatik.

bkz. docs/FEN_BILIMLERI_PLAN.md, docs/SOZEL_DERSLER_PLAN.md.
"""
from __future__ import annotations

from types import ModuleType

from app.config import settings
from app.models.enums import QuestionType, SubjectId
from app.subjects import fen as _fen_mod
from app.subjects import ingilizce as _ing_mod
from app.subjects import sosyal as _sos_mod
from app.subjects import turkce as _tr_mod
from app.subjects.base import SubjectPlugin
from app.subjects.fen import FEN
from app.subjects.ingilizce import INGILIZCE
from app.subjects.matematik import MATEMATIK
from app.subjects.sosyal import SOSYAL
from app.subjects.turkce import TURKCE

SUBJECTS: dict[SubjectId, SubjectPlugin] = {
    SubjectId.MATEMATIK: MATEMATIK,
    SubjectId.FEN: FEN,
    SubjectId.INGILIZCE: INGILIZCE,
    SubjectId.SOSYAL: SOSYAL,
    SubjectId.TURKCE: TURKCE,
}

# Ders → Settings feature-flag alan adı (matematik her zaman açık, flag yok).
SUBJECT_FLAGS: dict[SubjectId, str] = {
    SubjectId.FEN: "fen_enabled",
    SubjectId.TURKCE: "turkce_enabled",
    SubjectId.SOSYAL: "sosyal_enabled",
    SubjectId.INGILIZCE: "ingilizce_enabled",
}

# Ders → içerik modülü (uniform arayüz: SYSTEM_PROMPT/CRITIC_SYSTEM_PROMPT/
# YENI_NESIL_BLOCK/DEFAULT_TYPES/EXAMPLES + select_kazanimlar/collect_few_shot +
# get_units_for_grade/get_unit/find_unit_by_kazanim). Matematik yok (klasik yol).
_CONTENT: dict[SubjectId, ModuleType] = {
    SubjectId.FEN: _fen_mod,
    SubjectId.INGILIZCE: _ing_mod,
    SubjectId.SOSYAL: _sos_mod,
    SubjectId.TURKCE: _tr_mod,
}


# ── Ders ↔ soru tipi uyumu (2026-08-24 saha bulgusu) ─────────────────────────
# ÖLÇÜLDÜ (canlı, api.soruatolyesi.com): Türkçe bir isteğe `question_types`
# ["islem","salt_islem","sozel_problem","gunluk_hayat",...] gönderildiğinde backend
# bunu OLDUĞU GİBİ kabul ediyor, prompt'a "salt_islem: 2 adet" yazıyor ve model
# Türkçe kazanım koduyla (TR.5.OKA.1) ETİKETLİ MATEMATİK soruları üretiyordu
# ("Bir kütüphanede 5 katlı rafın her katında 12 kitap…"). Kaynak: istemcilerdeki
# soru-tipi grupları MATEMATİĞE GÖRE sabit yazılmış ve her ders için aynı liste
# gönderiliyordu (apps/mobile generator-setup.tsx, frontend/lib/types.ts).
#
# Kapı SUNUCUDA: istemci ne gönderirse göndersin, bir dersin desteklemediği tip
# üretime GİRMEZ. Eski/başka istemciler kırılmasın diye hata değil FİLTRE uygulanır;
# hepsi düşerse dersin kendi varsayılan dağılımına dönülür (bkz. filter_types_for_subject).

# Sözel derslere özgü tipler — matematikte anlamsız (matematik prompt'u tanımlamaz).
_VERBAL_ONLY_TYPES: frozenset[QuestionType] = frozenset({
    QuestionType.OKUMA_PASAJI,
    QuestionType.DIYALOG_TAMAMLAMA,
    QuestionType.KELIME_BILGISI,
    QuestionType.HARITA_YORUMLAMA,
    QuestionType.KAYNAK_METIN,
    QuestionType.DIL_BILGISI,
    QuestionType.YAZIM_NOKTALAMA,
    QuestionType.GORSEL_YORUMLAMA,
})

# Ders-NÖTR format tipleri: cevap biçimini belirler, içeriği DEĞİL → her derste
# anlamlı (dersin DEFAULT_TYPES'ında olmasa da kullanıcı açıkça isteyebilir).
_NEUTRAL_TYPES: frozenset[QuestionType] = frozenset({
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
    QuestionType.ESLESTIRME,
    QuestionType.SIRALAMA,
})
# NOT: `kavram_sorusu` bilinçli olarak NÖTR sayılmadı. İstemcilerin "Açık uçlu"
# grubu matematik tiplerinden oluşuyor ve içinde kavram_sorusu da var; nötr sayılsaydı
# Türkçe için o grubun TEK hayatta kalanı olur ve kağıt %100 kavram sorusuna düşerdi.
# Düşsün: hepsi düşünce dersin KENDİ varsayılan dağılımı devreye girer (daha iyi kağıt).

# AÇIK UÇLU tipler — istenirse üretilir (2026-08-28). Sözel derslerin DEFAULT
# dağılımı şıklı tiplerden oluşuyordu; arayüzde "Açık uçlu" seçeneği bu yüzden hiç
# yoktu ve kullanıcı şıksız soru isteyemiyordu. Bu tipler dersin VARSAYILAN
# dağılımına GİRMEZ (kağıdın karakteri değişmesin) ama kullanıcı açıkça seçerse
# üretilir; her dersin prompt'unda tip-spesifik format tanımı vardır.
_OPEN_ENDED_ON_REQUEST: dict[SubjectId, frozenset[QuestionType]] = {
    SubjectId.FEN: frozenset({
        QuestionType.KAVRAM_SORUSU,
        QuestionType.SOZEL_PROBLEM,
        QuestionType.AKIL_YURUTME,
        QuestionType.GUNLUK_HAYAT,
    }),
    SubjectId.SOSYAL: frozenset({
        QuestionType.KAVRAM_SORUSU,
        QuestionType.AKIL_YURUTME,
    }),
    SubjectId.TURKCE: frozenset({QuestionType.KAVRAM_SORUSU}),
    SubjectId.INGILIZCE: frozenset({QuestionType.KAVRAM_SORUSU}),
}

# Matematik: sözel-ders tipleri hariç HEPSİ (islem/salt_islem/gorsel_geometri/…).
_MATH_SUPPORTED_TYPES: frozenset[QuestionType] = (
    frozenset(QuestionType) - _VERBAL_ONLY_TYPES
)


def supported_types(subject_id: SubjectId) -> frozenset[QuestionType]:
    """Dersin ÜRETEBİLECEĞİ soru tipleri (istemciden gelen filtrenin üst sınırı).

    Non-math derste = dersin `DEFAULT_TYPES`'ı + ders-nötr format tipleri.
    Matematikte = sözel-ders tipleri dışındaki her şey.
    """
    if subject_id == SubjectId.MATEMATIK:
        return _MATH_SUPPORTED_TYPES
    content = _CONTENT.get(subject_id)
    defaults = frozenset(getattr(content, "DEFAULT_TYPES", ()) or ())
    if not defaults:  # tanımsız ders → kısıtlama uygulamayacak kadar bilgi yok
        return frozenset(QuestionType)
    return defaults | _NEUTRAL_TYPES | _OPEN_ENDED_ON_REQUEST.get(subject_id, frozenset())


def filter_types_for_subject(
    subject_id: SubjectId, requested: list[QuestionType] | None
) -> tuple[list[QuestionType] | None, list[QuestionType]]:
    """İstenen tipleri derse göre süzer → (kalanlar, düşenler).

    Dönen `kalanlar`:
      - None  → kısıt YOK (istemci hiç tip göndermedi ya da HEPSİ düştü). Çağıran
        bu durumda dersin varsayılan dağılımını kullanır — böylece "Türkçe istedim,
        matematik geldi" yerine "Türkçe istedim, Türkçe geldi" olur.
      - liste → derse uygun, sıra korunmuş tipler.
    `düşenler` yalnız loglama/gözlemlenebilirlik için.
    """
    if not requested:
        return None, []
    allowed = supported_types(subject_id)
    kept = [t for t in requested if t in allowed]
    dropped = [t for t in requested if t not in allowed]
    # Kalan ARTIK KIRPINTI ise (istenenin yarısından azı) filtreyi tümden bırak:
    # böyle bir istek ders-farkında OLMAYAN bir istemciden gelmiştir (matematik
    # grupları her derse gönderiliyor). Kırpıntıya uymak kağıdı tek tipe düşürürdü
    # (ör. Sosyal'de "yalnızca tablo_sorusu"); dersin varsayılan dağılımı daha iyi.
    # Gerçekten dar ama GEÇERLİ seçimler (ör. yalnız `coktan_secmeli`) hiç düşmediği
    # için bu eşiğe takılmaz.
    if dropped and len(kept) * 2 < len(requested):
        return None, dropped
    return (kept or None), dropped


def get_subject(subject_id: SubjectId = SubjectId.MATEMATIK) -> SubjectPlugin:
    return SUBJECTS.get(subject_id, MATEMATIK)


def subject_enabled(subject_id: SubjectId) -> bool:
    """Ders canlıda açık mı — feature-flag SETTINGS'ten CANLI okunur. Matematik hep açık."""
    if subject_id == SubjectId.MATEMATIK:
        return True
    flag = SUBJECT_FLAGS.get(subject_id)
    return bool(flag and getattr(settings, flag, False))


def is_enabled(subject_id: SubjectId) -> bool:
    """subject_enabled ile aynı (geriye uyum adı)."""
    return subject_enabled(subject_id)


def get_content_module(subject_id: SubjectId) -> ModuleType | None:
    """Non-math dersin içerik modülü; matematik/tanımsız → None."""
    return _CONTENT.get(subject_id)


def available_subjects(include_disabled: bool = False) -> list[SubjectPlugin]:
    """Aktif dersler (varsayılan, flag canlı). include_disabled=True → hepsi."""
    return [
        s
        for sid, s in SUBJECTS.items()
        if include_disabled or subject_enabled(sid)
    ]


__all__ = [
    "SubjectPlugin",
    "SUBJECTS",
    "SUBJECT_FLAGS",
    "get_subject",
    "subject_enabled",
    "is_enabled",
    "get_content_module",
    "available_subjects",
    "supported_types",
    "filter_types_for_subject",
]
