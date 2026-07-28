"""Kalite terazisi (docs/COST_QUALITY_V2_PLAN.md §2) — regresyon testleri.

Dört şeyi doğrular:
  1. Mutasyon üreticileri GERÇEKTEN bozuyor (ör. wrong_answer_key sonrası cevap
     değişmiş, empty_matching_body sonrası structured_content_issue bir sorun
     DÖNÜYOR) ve DETERMİNİSTİK (aynı girdi → aynı çıktı).
  2. Altın set şemaya uyuyor (Question.model_validate) ve SENTETİK kaynak
     SIZMAMIŞ (synthetic*/manual/few_shot) — bu regresyon kilidi kritik: altın
     set "gerçek soru" iddiasının kanıtı.
  3. quality_bench.py `--no-llm` (Katman 1, LLM'siz) modda çalışabiliyor.
  4. FAIL-OPEN AYRIMI (2026-07-28 must-fix): critic.evaluate() sunucu hatasında
     (503/vb.) boş liste döndürdüğünde terazi bunu "yakalanmadı" (0/5) ile
     KARIŞTIRMAZ — `unmeasured`/"ölçülemedi" olarak ayrı sayar, critic paydasından
     düşürür. Critic'i boş liste döndürecek şekilde monkeypatch'leyip doğrulanır.

CI eval workflow'u bu dosyayı DOĞRUDAN çalıştırır (`python tests/test_x.py`) →
hem pytest hem `if __name__ == "__main__"` self-runner ile uyumlu (diğer
tests/test_*.py dosyalarındaki kalıp).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pytest  # noqa: E402

from app.models.enums import QuestionType  # noqa: E402
from app.models.schemas import Question  # noqa: E402
from app.services.structured import (  # noqa: E402
    reference_integrity_issue,
    structured_content_issue,
)
from scripts.eval.build_gold_set import build_gold_set  # noqa: E402
from scripts.eval.mutations import (  # noqa: E402
    MUTATORS,
    build_broken_set,
    mutate_dangling_reference,
    mutate_difficulty_mismatch,
    mutate_empty_matching_body,
    mutate_inline_duplicated_options,
    mutate_kazanim_mismatch,
    mutate_solution_contradicts_answer,
    mutate_truncated_stem,
    mutate_wrong_answer_key,
)
from scripts.eval import quality_bench as QB
from scripts.eval.quality_bench import det_issue, run_bench

GOLD_PATH = ROOT / "knowledge_base" / "eval" / "gold" / "gold_questions.json"
BROKEN_PATH = ROOT / "knowledge_base" / "eval" / "gold" / "broken_questions.json"

FORBIDDEN_SOURCE_PREFIXES = ("synthetic",)
FORBIDDEN_SOURCES_EXACT = {"manual/few_shot"}


# ── Ortak sabit girdi (testler arasında paylaşılır, yeniden hesaplanmaz) ──────

def _fresh_gold() -> list[dict]:
    records, _meta = build_gold_set(math_target=62)
    return records


_GOLD_CACHE: list[dict] | None = None


def _gold() -> list[dict]:
    global _GOLD_CACHE
    if _GOLD_CACHE is None:
        _GOLD_CACHE = _fresh_gold()
    return _GOLD_CACHE


def _by_source(gold: list[dict], gold_id: str) -> dict:
    return next(g for g in gold if g["gold_id"] == gold_id)


# ── 1) Altın set — şema + regresyon kilidi ───────────────────────────────────

def test_gold_set_min_count() -> None:
    gold = _gold()
    assert len(gold) >= 180, f"altın set >=180 olmalı, olan {len(gold)}"


def test_gold_set_no_synthetic_source() -> None:
    """Regresyon kilidi: synthetic*/manual/few_shot altın sete SIZMAMALI."""
    gold = _gold()
    for rec in gold:
        src = rec["source"]
        assert src not in FORBIDDEN_SOURCES_EXACT, f"{rec['gold_id']} sentetik kaynak: {src!r}"
        assert not src.startswith(FORBIDDEN_SOURCE_PREFIXES), (
            f"{rec['gold_id']} sentetik kaynak: {src!r}"
        )
        assert src, f"{rec['gold_id']} kaynak alanı boş olamaz"


def test_gold_set_validates_as_question_schema() -> None:
    """Her altın kayıt app.models.schemas.Question'a model_validate edilebilmeli
    (number alanı Question'da var ama altın kayıtta yok → eklenerek doğrulanır)."""
    gold = _gold()
    for rec in gold:
        q = Question.model_validate({**rec, "number": 1})
        assert q.question == rec["question"]
        assert q.kazanim_kod == rec["kazanim_kod"]


def test_gold_set_distribution_reported() -> None:
    _records, meta = build_gold_set(math_target=62)
    assert meta["total"] >= 180
    assert set(meta["by_subject"].keys()) == {"matematik", "fen", "turkce", "sosyal", "ingilizce"}
    assert sum(meta["by_subject"].values()) == meta["total"]


# ── 2) Mutasyonlar — deterministik + GERÇEKTEN bozuyor ───────────────────────

def test_mutations_are_deterministic() -> None:
    gold = _gold()
    run1, _ = build_broken_set(gold)
    run2, _ = build_broken_set(gold)
    # broken_id hariç tüm alanlar (soru içeriği + meta) birebir aynı olmalı.
    assert len(run1) == len(run2)
    for a, b in zip(run1, run2):
        a2, b2 = dict(a), dict(b)
        a2.pop("broken_id", None)
        b2.pop("broken_id", None)
        assert a2 == b2


def test_broken_set_min_count_and_defect_types() -> None:
    gold = _gold()
    records, meta = build_broken_set(gold)
    assert len(records) >= 40, f"bozuk set >=40 olmalı, olan {len(records)}"
    assert meta["total"] >= 40
    expected_types = {
        "empty_matching_body", "inline_duplicated_options", "wrong_answer_key",
        "solution_contradicts_answer", "kazanim_mismatch", "difficulty_mismatch",
        "truncated_stem", "dangling_reference",
    }
    assert set(meta["by_defect_type"].keys()) == expected_types
    for t in expected_types:
        assert meta["by_defect_type"][t] >= 5, f"{t} icin >=5 ornek bekleniyordu"


def test_empty_matching_body_triggers_structured_issue() -> None:
    gold = _gold()
    broken = mutate_empty_matching_body(gold)
    assert len(broken) == 5
    for rec in broken:
        qt = QuestionType(rec["question_type"])
        issue = structured_content_issue(qt, rec["question"])
        assert issue is not None, f"empty_matching_body sorunu yakalanmadi: {rec['question'][:80]!r}"


def test_dangling_reference_triggers_reference_issue() -> None:
    gold = _gold()
    broken = mutate_dangling_reference(gold)
    assert len(broken) == 5
    for rec in broken:
        issue = reference_integrity_issue(rec["question"])
        assert issue is not None, f"dangling_reference yakalanmadi: {rec['question'][:80]!r}"


def test_wrong_answer_key_changes_answer_consistently() -> None:
    gold = _gold()
    broken = mutate_wrong_answer_key(gold)
    assert len(broken) == 5
    for rec in broken:
        source = _by_source(gold, rec["source_gold_id"])
        assert rec["answer"] != source["answer"], "cevap degismemis"
        if rec.get("options") and rec.get("correct_index") is not None:
            # answer + correct_index TUTARLI olmalı (yanlış ama tutarlı).
            assert rec["options"][rec["correct_index"]] in rec["answer"]


def test_solution_contradicts_answer_keeps_answer_but_changes_solution() -> None:
    gold = _gold()
    broken = mutate_solution_contradicts_answer(gold)
    assert len(broken) == 5
    for rec in broken:
        source = _by_source(gold, rec["source_gold_id"])
        assert rec["answer"] == source["answer"], "answer degismemeliydi"
        assert rec["solution_steps"] != source["solution_steps"], "solution_steps degismemis"


def test_kazanim_mismatch_uses_sibling_valid_code() -> None:
    """§3g-1b: mutasyon artık ÜRETİMDE MÜMKÜN senaryoyu kurar — kod, aynı
    isteğin geçerli kazanım listesinden BAŞKA bir kodla değiştirilir (eskiden
    başka bir DERSTEN alınıyordu; `agent.py:1758` böyle bir kodu sessizce
    `kazanimlar[0]`'a çevirdiği için o senaryo canlıda hiç oluşamaz).
    Örneklem 5 → 15 (§3g-1e: 5 örnekle %80 ile %60 ayırt edilemez)."""
    gold = _gold()
    broken = mutate_kazanim_mismatch(gold)
    assert len(broken) == 15
    for rec in broken:
        source = _by_source(gold, rec["source_gold_id"])
        assert rec["kazanim_kod"] != source["kazanim_kod"]
        # Kardeş kod AYNI ders + AYNI sınıftan gelmeli (üretimde tek mümkün hâl).
        assert rec["subject"] == source["subject"]
        assert rec["grade"] == source["grade"]
        assert "same_unit" in rec, "kardeş kodun aynı üniteden mi geldiği işaretlenmeli"


def test_difficulty_mismatch_relabels_kolay_as_zor() -> None:
    gold = _gold()
    broken = mutate_difficulty_mismatch(gold)
    assert len(broken) == 5
    for rec in broken:
        source = _by_source(gold, rec["source_gold_id"])
        assert source["difficulty"] == "kolay"
        assert rec["difficulty"] == "zor"


def test_truncated_stem_is_shorter() -> None:
    gold = _gold()
    broken = mutate_truncated_stem(gold)
    assert len(broken) == 5
    for rec in broken:
        source = _by_source(gold, rec["source_gold_id"])
        assert len(rec["question"]) < len(source["question"])


def test_inline_duplicated_options_repeats_options_in_stem() -> None:
    gold = _gold()
    broken = mutate_inline_duplicated_options(gold)
    assert len(broken) == 5
    for rec in broken:
        source = _by_source(gold, rec["source_gold_id"])
        assert len(rec["question"]) > len(source["question"])
        # İlk şıkkın metni stem'de EN AZ iki kez geçmeli (orijinal + kopya).
        first_opt = rec["options"][0]
        assert rec["question"].count(first_opt) >= 2


def test_all_eight_mutators_registered() -> None:
    assert len(MUTATORS) == 8


# ── 3) Bench — LLM'siz koşabilmeli ───────────────────────────────────────────

def test_bench_runs_without_llm() -> None:
    gold = _gold()
    broken, _meta = build_broken_set(gold)
    result = run_bench(gold, broken, use_llm=False, limit=None)
    assert result["llm_enabled"] is False
    assert set(result["defect_types"].keys()) == {
        "empty_matching_body", "inline_duplicated_options", "wrong_answer_key",
        "solution_contradicts_answer", "kazanim_mismatch", "difficulty_mismatch",
        "truncated_stem", "dangling_reference",
    }
    fa = result["gold_false_alarm"]
    assert fa["total"] == len(gold)
    assert fa["critic_false"] is None  # LLM koşmadı


def test_bench_det_layer_catches_known_defects() -> None:
    """Regresyon kilidi: bu iki kusur tipi deterministik katmanla YAKALANMALI
    (structured_content_issue / reference_integrity_issue zaten kapsıyor)."""
    gold = _gold()
    broken, _meta = build_broken_set(gold)
    result = run_bench(gold, broken, use_llm=False, limit=None)
    assert result["defect_types"]["empty_matching_body"]["recall_pct"] >= 80
    assert result["defect_types"]["dangling_reference"]["recall_pct"] >= 80


def test_det_issue_is_none_for_most_gold_questions() -> None:
    """Altın set büyük çoğunlukla Katman 1'i TEMİZ geçmeli (yanlış-alarm düşük)."""
    gold = _gold()
    false_positives = sum(1 for rec in gold if det_issue(rec) is not None)
    rate = false_positives / len(gold)
    assert rate < 0.10, f"Katman 1 yanlış-alarm orani beklenenden yuksek: %{rate*100:.1f}"


# ── 4) FAIL-OPEN AYRIMI — must-fix (2026-07-28) ──────────────────────────────
# critic.evaluate() sunucu hatasında (503/vb.) İÇERİDE retry'ını tüketip BOŞ liste
# döner (bkz. app/services/critic.py). Bu terazi o boş listeyi "critic yakaladı,
# hepsi geçerli dedi" (0/n yakalanmadı) ile KARIŞTIRMAMALI — "ölçülemedi" olarak
# ayrı sayıp critic paydasından düşürmeli. Kanıt (gerçek koşu): aynı iki kusur
# tipi iki ayrı LLM'li koşu arasında oynadı (inline_duplicated_options 1/5→0/5,
# wrong_answer_key 0/5→5/5) — biri fail-open'dı, "yakalanmadı" sayılmıştı.

class _FakeVerdict:
    def __init__(self, i: int, is_valid: bool = False, confidence: float = 0.9) -> None:
        self.question_index = i
        self.is_valid = is_valid
        self.confidence = confidence
        self.issues: list[str] = ["fake"]


class _AlwaysEmptyCritic:
    """Her çağrıda boş liste döner (kalıcı fail-open simülasyonu — retry de kurtaramaz)."""

    def evaluate(self, questions, kazanimlar, difficulty, context=""):
        return []


class _FlakyOnceCritic:
    """İlk çağrıda boş (fail-open), 2. çağrıda (retry) başarılı döner."""

    def __init__(self) -> None:
        self.calls = 0

    def evaluate(self, questions, kazanimlar, difficulty, context=""):
        self.calls += 1
        if self.calls == 1:
            return []
        return [_FakeVerdict(i) for i in range(len(questions))]


def _some_resolvable_gold(n: int = 5) -> list[dict]:
    """kazanim_kod'u kendi dersinde ÇÖZÜLEBİLEN n altın kayıt (critic_flags'ın
    fail-open dalını unresolved'dan ayırmak için — matematik kayıtları güvenli)."""
    gold = _gold()
    math_qs = [q for q in gold if q["subject"] == "matematik"]
    return math_qs[:n]


def test_critic_flags_permanent_fail_open_marks_unmeasured_not_caught() -> None:
    """Kalıcı fail-open (retry de boş) → hiçbiri 'yakalanmadı' SAYILMAMALI,
    hepsi unmeasured'a düşmeli ve flags tümü False kalmalı."""
    records = _some_resolvable_gold(5)
    flags, unresolved, unmeasured, fail_open = QB.critic_flags(_AlwaysEmptyCritic(), records)
    assert fail_open is True
    assert unresolved == []
    assert sorted(unmeasured) == list(range(5)), "hepsi ölçülemedi sayılmalı"
    assert all(f is False for f in flags), "ölçülemeyen kayıt asla 'yakalandı' sayılmamalı"


def test_critic_flags_retries_once_and_recovers() -> None:
    """İlk deneme fail-open, tek retry KURTARIYORSA unmeasured BOŞ kalmalı ama
    fail_open_detected yine de True (bu koşuda semptom GÖRÜLDÜ)."""
    records = _some_resolvable_gold(5)
    critic = _FlakyOnceCritic()
    flags, unresolved, unmeasured, fail_open = QB.critic_flags(critic, records)
    assert critic.calls == 2, "tam olarak bir retry yapılmalı"
    assert fail_open is True, "ilk denemede eksik vardı — semptom raporlanmalı"
    assert unmeasured == [], "retry kurtardı → ölçülemeyen kalmamalı"
    assert all(flags), "retry sonrası dönen verdict'ler is_valid=False → hepsi yakalanmalı"


def test_run_bench_separates_unmeasured_from_not_caught(monkeypatch) -> None:
    """run_bench düzeyinde: kalıcı fail-open'da defect-type satırı 'critic_caught'ı
    None (ölçülemedi) göstermeli, 0 (yakalanmadı) DEĞİL — ve bunu ayrı bir sayaçta
    (critic_unmeasured_fail_open) + üst düzey fail_open_batches/unmeasured_ids'te
    raporlamalı."""
    monkeypatch.setattr(QB.settings, "gemini_api_key", "fake-key-for-test")
    monkeypatch.setattr(QB, "_get_critic", lambda: _AlwaysEmptyCritic())

    gold = _gold()
    broken, _meta = build_broken_set(gold)
    result = run_bench(gold, broken, use_llm=True, limit=10)

    assert result["llm_enabled"] is True
    assert result["fail_open_batches"] > 0
    assert len(result["unmeasured_ids"]) > 0

    for defect_type, row in result["defect_types"].items():
        if row["critic_skipped_fully_det_caught"]:
            continue  # zaten det. ile yakalanmış (empty_matching_body/dangling_reference)
        # Kalıcı fail-open: hiç ölçülemedi → critic_caught None OLMALI, 0 DEĞİL
        # ("0" = "critic baktı, yakalamadı" anlamına gelir; bu YANLIŞ olurdu).
        assert row["critic_caught"] is None, (
            f"{defect_type}: fail-open'da critic_caught None olmalı (ölçülemedi), "
            f"olan {row['critic_caught']!r}"
        )
        assert row["critic_unmeasured_fail_open"] == row["n"] - row["critic_unresolved_kazanim"]

    fa = result["gold_false_alarm"]
    assert fa["critic_unmeasured_fail_open"] > 0
    # Rapor metninde "ölçülemedi" notu görünmeli (kullanıcıya AÇIKÇA gösterilmeli).
    report = QB.format_report(result)
    assert "ölçülemedi" in report
    assert "KISMİ" in report


def test_run_bench_does_not_confuse_genuine_miss_with_fail_open(monkeypatch) -> None:
    """Critic GERÇEKTEN yanıt verip 'hepsi geçerli' derse (is_valid=True, fail-open
    DEĞİL) bu durum unmeasured'a değil, gerçek '0/n yakalanmadı'ya düşmeli."""

    class _AllValidCritic:
        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            return [_FakeVerdict(i, is_valid=True) for i in range(len(questions))]

    monkeypatch.setattr(QB.settings, "gemini_api_key", "fake-key-for-test")
    monkeypatch.setattr(QB, "_get_critic", lambda: _AllValidCritic())

    gold = _gold()
    broken, _meta = build_broken_set(gold)
    result = run_bench(gold, broken, use_llm=True, limit=10)

    for defect_type, row in result["defect_types"].items():
        if row["critic_skipped_fully_det_caught"]:
            continue
        assert row["critic_unmeasured_fail_open"] == 0, f"{defect_type}: gerçek yanıt fail-open sayılmamalı"
        assert row["critic_caught"] == 0, f"{defect_type}: gerçek 'hepsi geçerli' verdict'i 0 yakalama olmalı"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
