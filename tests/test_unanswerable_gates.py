"""Cevaplanamaz soru kapıları — 2026-07-29 canlı kağıt bulgularının regresyonu.

Üç ölçülmüş kusur (7. sınıf Sosyal kağıtları, hepsi "denetimden geçti" etiketliydi):

1. TİP KAÇAĞI: model sosyal sorulara matematiğe özel `salt_islem` etiketi koydu.
   `salt_islem` `_MC_TYPES`'ta olmadığı için 4-şık kapısı ATLANDI → "…hangisi
   değildir?" soruları ŞIKSIZ teslim edildi (cevap anahtarında "A", şık yok).
2. KESİK KÖK: "…fethedilen yerlerdeki halka gösterilen" — cümle ortasında bitmiş.
   Kalite terazisinde `truncated_stem` 0/5 yakalanıyordu çünkü kontrol YOKTU.
3. HAM DİREKTİF: `{{table:...}}` içinde satır ayracı (`;;`) olmayınca
   `process_table_directives` no-op yapıp ham kodu ekrana bastı. Daha kötüsü:
   direktifin `|` işaretleri `_MD_TABLE_RE`'yi kandırdığı için
   `reference_integrity_issue`'nun "tablo atfı var ama tablo yok" kapısı da açıldı.

Bu dosyanın ASIL yükü YANLIŞ-ELEME testleri: her yanlış eleme, yedek havuzundan
bir soru yakar ve yedek tükenirse top-up turu = GERÇEK PARA. Kapılar dar olmalı.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

import pytest  # noqa: E402

from app.models.enums import Difficulty, QuestionType  # noqa: E402
from app.services.structured import (  # noqa: E402
    leftover_directive_issue,
    reference_integrity_issue,
    truncated_stem_issue,
)
from app.services.svg_utils import process_table_directives  # noqa: E402

# Canlı kağıttan BİREBİR alınan bozuk gövde (WhatsApp ekran görüntüsü, 19:01).
LIVE_LEAKED_TABLE = (
    "Aşağıdaki tabloda, bir ülkenin son 50 yıldaki teknolojik gelişmeleri ve bu "
    "gelişmelerin ekonomik büyümeye etkileri gösterilmiştir. Tabloya göre, teknolojik "
    "ilerlemenin ekonomik büyümeyi nasıl etkilediğini en iyi açıklayan ifade hangisidir?"
    "{{table:Yıl|Teknolojik Gelişme|Ekonomik Büyüme Oranı(%)|1970-1980|Televizyonun "
    "yaygınlaşması|2.5|1980-1990|Kişisel bilgisayarların ortaya çıkışı|3.8}}"
)
# Canlı kağıttan BİREBİR alınan kesik kök.
LIVE_TRUNCATED = (
    "Osmanlı Devleti'nin kuruluş ve yükselme dönemlerinde uyguladığı bazı politikalar, "
    "kısa sürede bir cihan devleti hâline gelmesinde etkili olmuştur. Bu politikalar "
    "arasında fethedilen yerlerdeki halka gösterilen"
)


# ────────────────────────────────── 3) ham direktif


def test_live_leaked_directive_is_caught():
    assert leftover_directive_issue(LIVE_LEAKED_TABLE) is not None


def test_malformed_directive_survives_table_conversion():
    """Kusurun ön koşulu: bozuk direktif çevrilmiyor, ham kalıyor (svg_utils no-op)."""
    assert "{{table" in process_table_directives(LIVE_LEAKED_TABLE)


def test_raw_directive_defeats_the_table_guard():
    """ÖLÇÜLEN ASIL TUZAK: ham direktifin `|`'ları tablo dedektörünü kandırıyor.

    Aynı kök direktifsiz verildiğinde tablo kapısı YAKALIYOR; direktifle
    YAKALAMIYOR. Bu yüzden `leftover_directive_issue` bu kapıdan ÖNCE çalışmalı.
    """
    assert reference_integrity_issue(LIVE_LEAKED_TABLE) is None
    stem_only = LIVE_LEAKED_TABLE.split("{{table")[0]
    assert reference_integrity_issue(stem_only) is not None


@pytest.mark.parametrize("directive", ["chart", "geo", "pattern", "TABLE"])
def test_other_directives_also_caught(directive):
    assert leftover_directive_issue(f"Soru kökü {{{{{directive}:bozuk}}}} mü?") is not None


def test_converted_table_is_not_flagged():
    """YANLIŞ-ELEME: düzgün (`;;` ayraçlı) direktif GFM tabloya dönüşür → temiz."""
    ok = (
        "Tabloya göre hangi ilin nüfusu en fazladır?\n\n"
        "{{table: Şehir | Nüfus ;; Ankara | 5.7 milyon ;; İzmir | 4.4 milyon}}"
    )
    rendered = process_table_directives(ok)
    assert "{{table" not in rendered
    assert leftover_directive_issue(rendered) is None
    assert reference_integrity_issue(rendered) is None


def test_plain_braces_not_flagged():
    """YANLIŞ-ELEME: küme parantezi kümesi/matematik gösteriminde geçebilir."""
    assert leftover_directive_issue("A = {{1, 2, 3}} kümesinin eleman sayısı kaçtır?") is None
    assert leftover_directive_issue("$$\\{x : x > 0\\}$$ kümesi nedir?") is None


# ────────────────────────────────── 2) kesik kök


def test_live_truncated_stem_is_caught():
    assert truncated_stem_issue(LIVE_TRUNCATED) is not None


@pytest.mark.parametrize(
    "text",
    [
        "Aşağıdakilerden hangisi doğrudur?",
        "Boşluğu doldurun: Türkiye'nin başkenti ____",
        "Cümleyi tamamlayın: Atatürk 1881 yılında Selanik'te doğmuştur.",
        "Hangisi yanlıştır:",
        "Şu ifadeyi değerlendirin: 'Bilim evrenseldir.'",
        "Aşağıdaki kavramları eşleştirin.\n\n| Kavram | Tanım |\n|---|---|\n| İklim | Uzun süreli |",
        "Aşağıdakilerden hangisi başkenttir?\n\nA) Ankara\nB) İzmir\nC) Bursa\nD) Konya",
        "Üçgenin alanı kaçtır?\n<svg width='10'><rect/></svg>",
        "Nüfus kaç kişidir? (2020 verisine göre)",
        # Aşağıdaki üçü test sırasında YAKALANAN yanlış-elemelerdir — kilitli kalsın:
        "Sıralayınız: I. Kuruluş II. Yükselme III. Gerileme",  # meşru öğe bitişi
        "$$12 + 7 = ?$$",  # LaTeX ayracı; bu haliyle TÜM matematik elenirdi
        "$$x^2 + 3x - 4 = 0$$",  # denklem, rakamla bitiyor
        "Bir karenin bir kenarının uzunluğu 5 cm",  # ölçü birimi (≤2 harf)
        "Aşağıdaki işlemin sonucunu bulunuz: 12 + 7",  # rakamla bitiyor
    ],
)
def test_valid_endings_not_flagged(text):
    """YANLIŞ-ELEME: meşru bitişler (soru işareti, iki nokta, boşluk yer tutucu,
    şık satırı, tablo satırı, SVG, parantez, tırnak) kusur SAYILMAMALI."""
    assert truncated_stem_issue(text) is None, text[:50]


@pytest.mark.parametrize(
    "text",
    [
        "Osmanlı Devleti'nin kuruluşunda etkili olan ve",
        "Aşağıdaki grafiğe göre en yüksek değeri gösteren",
        "Bu durumun temel nedeni aşağıdakilerden",
    ],
)
def test_truncated_variants_caught(text):
    assert truncated_stem_issue(text) is not None, text[:50]


def test_empty_input_is_safe():
    assert truncated_stem_issue("") is None
    assert truncated_stem_issue(None) is None
    assert leftover_directive_issue("") is None
    assert leftover_directive_issue(None) is None


# ────────────────────────────────── 1) tip kaçağı (_process_batch)


def _raw(qtype: QuestionType, question: str, options=None, answer="A"):
    from app.services.agent import GeneratedQuestion

    return GeneratedQuestion(
        question=question, answer=answer, solution_steps="adım",
        kazanim_kod="SB.7.2.2", question_type=qtype, options=options,
    )


def _run_batch(raws, allowed):
    from app.services.agent import GeminiAgent, GeneratedBatch
    from app.services.diversity import BatchDeduplicator

    return GeminiAgent._process_batch(
        GeneratedBatch(questions=raws),
        BatchDeduplicator(),
        {"SB.7.2.2"},
        "SB.7.2.2",
        allowed_types=allowed,
    )


_SOSYAL_ALLOWED = {
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
}


def test_live_salt_islem_leak_without_options_is_dropped():
    """CANLI KUSUR: sosyal soruya `salt_islem` etiketi + şık yok → elenmeli."""
    live_stem = (
        "Türkiye'nin bölgesel ve küresel sorunların çözümüne yönelik çabalarını "
        "gösteren örnekler düşünüldüğünde, aşağıdaki alanlardan hangisi bu çabaların "
        "bir parçası değildir?"
    )
    out = _run_batch([_raw(QuestionType.SALT_ISLEM, live_stem)], _SOSYAL_ALLOWED)
    assert out == [], "şıksız izinsiz tip teslim edilmemeliydi"


def test_type_leak_with_options_is_rescued_not_dropped():
    """BEDAVA KURTARMA: şıklar VARSA soru atılmaz, `coktan_secmeli`ye çevrilir.

    Eleme yedek havuzundan soru yakar; kurtarılabiliyorsa kurtarmak maliyet
    açısından her zaman daha iyidir.
    """
    out = _run_batch(
        [_raw(QuestionType.SALT_ISLEM, "Hangisi başkenttir?",
              options=["Ankara", "İzmir", "Bursa", "Konya"], answer="A")],
        _SOSYAL_ALLOWED,
    )
    assert len(out) == 1
    assert out[0].question_type == QuestionType.COKTAN_SECMELI
    assert out[0].options == ["Ankara", "İzmir", "Bursa", "Konya"]


def test_allowed_type_untouched():
    """YANLIŞ-ELEME: izinli tip aynen geçmeli."""
    out = _run_batch(
        [_raw(QuestionType.COKTAN_SECMELI, "Hangisi başkenttir?",
              options=["Ankara", "İzmir", "Bursa", "Konya"], answer="A")],
        _SOSYAL_ALLOWED,
    )
    assert len(out) == 1
    assert out[0].question_type == QuestionType.COKTAN_SECMELI


def test_no_allowed_set_skips_check():
    """Matematik yolu (allowed_types=None) DAVRANIŞ DEĞİŞTİRMEMELİ — salt_islem
    matematikte meşru bir tiptir ve şık istemez."""
    out = _run_batch([_raw(QuestionType.SALT_ISLEM, "$$12 + 7 = ?$$", answer="19")], None)
    assert len(out) == 1
    assert out[0].question_type == QuestionType.SALT_ISLEM


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
