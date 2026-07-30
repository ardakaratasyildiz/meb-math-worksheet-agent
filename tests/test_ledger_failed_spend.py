"""Boşa giden harcamanın deftere yazılması — 2026-07-29 ölçümünün regresyonu.

ÖLÇÜLEN KUSUR: `usage_ledger` YALNIZ başarı yolunda yazılıyordu. Üretim tamamlanıp
tüm bedeli ödendikten SONRA istek 502 ile düşerse (filtrelerden geçen soru kalmadı,
mixed 500, kopan bağlantı) satır hiç atılmıyordu → Google faturasının %25-40'ı
hiçbir deftere düşmüyordu (26 Tem ₺22,5 · 28 Tem ₺10,9 · canlıda 23,6 sn süren
bedeli ödenmiş bir 502 defterde yoktu).

Kritik ikinci şart: `status='failed'` satırlar KOTADAN SAYILMAMALI. Kullanıcı
almadığı kağıdın kotasını ödemez; maliyeti biz üstlenir ama GÖRÜRÜZ.
"""
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

import pytest  # noqa: E402

from app.models.enums import Difficulty, QuestionType, SubjectId  # noqa: E402
from app.models.schemas import GenerateWorksheetRequest, Question  # noqa: E402
from app.services.usage_ledger import (  # noqa: E402
    STATUS_FAILED,
    STATUS_OK,
    UsageLedger,
)


@pytest.fixture
def ledger():
    """Geçici dosyaya bağlı taze defter — GERÇEK history.sqlite3'e DOKUNMAZ."""
    tmp = os.path.join(tempfile.gettempdir(), f"ledger_{uuid.uuid4().hex}.sqlite3")
    lg = UsageLedger(db_path=tmp)
    assert "history.sqlite3" not in tmp
    yield lg
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(tmp + suffix)
        except OSError:
            pass


# ─────────────────────────────────────────── şema migrasyonu


def test_status_column_added_to_existing_table():
    """Migrasyon: `status` kolonu OLMAYAN eski tabloya eklenir ve eski satırlar
    'ok' sayılır (defter zaten yalnız başarı yolunda yazıldığı için doğru geçmiş)."""
    import sqlite3

    tmp = os.path.join(tempfile.gettempdir(), f"ledger_old_{uuid.uuid4().hex}.sqlite3")
    conn = sqlite3.connect(tmp)
    conn.execute(
        "CREATE TABLE usage_ledger (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, "
        "model TEXT, prompt_tokens INTEGER DEFAULT 0, completion_tokens INTEGER DEFAULT 0, "
        "cost_usd REAL DEFAULT 0, grade INTEGER, topic TEXT, question_count INTEGER DEFAULT 0, "
        "cache_hit INTEGER DEFAULT 0, created_at REAL NOT NULL)"
    )
    conn.execute(
        "INSERT INTO usage_ledger (id, tenant_id, model, cost_usd, question_count, created_at) "
        "VALUES ('eski', 'user_1', 'gemini-2.5-flash', 0.05, 10, ?)",
        (time.time(),),
    )
    conn.commit()
    conn.close()

    lg = UsageLedger(db_path=tmp)  # migrasyon burada çalışır
    items = lg.recent(limit=5)
    assert len(items) == 1
    assert items[0]["status"] == STATUS_OK, "eski satır 'ok' sayılmalı"
    # Eski satır kotadan SAYILMALI (başarılı üretimdi).
    assert lg.worksheets_used_since("user_1", 0) == 1


# ─────────────────────────────────────────── kota izolasyonu (en kritik)


def test_failed_rows_do_not_consume_quota(ledger):
    """`failed` satır kotadan SAYILMAZ — kullanıcı almadığı kağıdı ödemez."""
    common = dict(tenant_id="user_1", model="gemini-2.5-flash", prompt_tokens=1000,
                  completion_tokens=500, cost_usd=0.05, grade=5, topic="Kesirler")
    ledger.record(**common, question_count=10, status=STATUS_OK)
    ledger.record(**common, question_count=0, status=STATUS_FAILED)
    ledger.record(**common, question_count=0, status=STATUS_FAILED)

    assert ledger.worksheets_used_since("user_1", 0) == 1, "yalnız teslim edilen kağıt"
    assert ledger.questions_used_since("user_1", 0) == 10, "yalnız teslim edilen soru"


def test_failed_cost_is_still_visible(ledger):
    """Kotadan sayılmıyor AMA maliyet görünür olmalı — asıl amaç bu."""
    ledger.record(tenant_id="user_1", model="gemini-2.5-flash", prompt_tokens=1000,
                  completion_tokens=500, cost_usd=0.10, question_count=10, status=STATUS_OK)
    ledger.record(tenant_id="user_1", model="gemini-2.5-flash", prompt_tokens=2000,
                  completion_tokens=900, cost_usd=0.25, question_count=0, status=STATUS_FAILED)

    s = ledger.summary()
    assert s["total"]["generations"] == 2
    assert s["total"]["delivered_generations"] == 1
    assert s["total"]["failed_generations"] == 1
    assert s["total"]["cost_usd"] == pytest.approx(0.35), "toplam TÜM harcamayı içerir"
    assert s["total"]["failed_cost_usd"] == pytest.approx(0.25), "boşa giden ayrı görünür"


def test_cache_hit_and_failed_are_independent(ledger):
    """Cache-hit ve failed ayrı eksenler; ikisi de kotadan düşmez."""
    ledger.record(tenant_id="u", model="cache", cost_usd=0.0, question_count=10,
                  prompt_tokens=0, completion_tokens=0, cache_hit=True, status=STATUS_OK)
    ledger.record(tenant_id="u", model="gemini-2.5-flash", cost_usd=0.2, question_count=0,
                  prompt_tokens=100, completion_tokens=50, status=STATUS_FAILED)
    assert ledger.worksheets_used_since("u", 0) == 0
    assert ledger.summary()["total"]["failed_cost_usd"] == pytest.approx(0.2)


def test_zero_question_rows_do_not_consume_paper_quota(ledger):
    """ÖLÇÜLEN KOTA HATASI: quiz "yeniden üret" satırı (question_count=0) kağıt
    bazlı kotadan TAM BİR KAĞIT yiyordu.

    Koddaki yorum "question_count=0 geçerek kotayı şişirmez" diyordu ve kota SORU
    bazlıyken doğruydu; kota KAĞIT bazlıya (COUNT(*)) geçince sessizce bozuldu.
    """
    ledger.record(tenant_id="user_1", model="gemini-2.5-flash", prompt_tokens=900,
                  completion_tokens=400, cost_usd=0.02, grade=5,
                  topic="quiz-regenerate", question_count=0, cache_hit=False)
    assert ledger.questions_used_since("user_1", 0) == 0
    assert ledger.worksheets_used_since("user_1", 0) == 0, "yeniden-üret kağıt yememeli"
    # Maliyet yine görünür olmalı — amaç kaydı silmek değil, kotadan saymamak.
    assert ledger.summary()["total"]["cost_usd"] == pytest.approx(0.02)


def test_delivered_paper_still_counts(ledger):
    """YANLIŞ-DÜZELTME koruması: gerçek teslim edilen kağıt HÂLÂ kotadan düşmeli."""
    ledger.record(tenant_id="user_1", model="gemini-2.5-flash", prompt_tokens=900,
                  completion_tokens=400, cost_usd=0.05, grade=5, topic="Kesirler",
                  question_count=1, cache_hit=False)
    assert ledger.worksheets_used_since("user_1", 0) == 1


def test_unknown_status_falls_back_to_ok(ledger):
    """Beklenmeyen status değeri sessizce 'ok'a düşer (kota kaçağı olmasın)."""
    ledger.record(tenant_id="u", model="m", cost_usd=0.1, question_count=5,
                  prompt_tokens=1, completion_tokens=1, status="saçmalık")
    assert ledger.recent()[0]["status"] == STATUS_OK


# ─────────────────────────────────────────── router: gerçek sızıntı yolları


def _req():
    return GenerateWorksheetRequest(
        subject=SubjectId.MATEMATIK, grade=5, topic_id="dogal_sayilar",
        question_count=10, difficulty=Difficulty.ORTA, difficulty_mode="single",
    )


def _trace(cost=0.1234):
    from app.models.schemas import GenerationTrace

    return GenerationTrace(
        few_shot_source="static", few_shot_count=0, textbook_count=0,
        model_used="gemini-2.5-flash", temperature=0.7, seed=1, retry_rounds=0,
        requested_count=10, delivered_count=0,
        prompt_tokens=31000, completion_tokens=45000, estimated_cost_usd=cost,
    )


def _patch_router(monkeypatch, ledger, *, generate, trace=None):
    from app.routers import worksheets as W
    from app.services.agent import GeminiAgent

    monkeypatch.setattr(W, "USAGE_LEDGER", ledger)
    monkeypatch.setattr(W.settings, "enable_worksheet_history", False)
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(GeminiAgent, "generate", generate)
    monkeypatch.setattr(
        GeminiAgent, "build_last_trace", lambda self: trace if trace else _trace()
    )
    return W


def test_empty_result_502_records_real_cost(monkeypatch, ledger):
    """CANLI KUSUR: üretim tamamlandı, bedeli ödendi, filtreden soru geçmedi →
    502 dönüyor ve ESKİDEN defter hiç yazılmıyordu. Artık GERÇEK maliyetle yazılır.
    """
    from fastapi import HTTPException

    W = _patch_router(monkeypatch, ledger, generate=lambda self, **kw: [],
                      trace=_trace(cost=0.1234))
    with pytest.raises(HTTPException) as ei:
        W._build_worksheet(_req())
    assert ei.value.status_code == 502

    items = ledger.recent()
    assert len(items) == 1, "boşa giden üretim deftere yazılmalıydı"
    row = items[0]
    assert row["status"] == STATUS_FAILED
    assert row["cost_usd"] == pytest.approx(0.1234), "GERÇEK maliyet yazılmalı"
    assert row["prompt_tokens"] == 31000 and row["completion_tokens"] == 45000
    assert row["question_count"] == 0, "teslim edilen soru yok"


def test_agent_error_records_row_with_unknown_cost(monkeypatch, ledger):
    """`generate()` içinde çökerse maliyet bu katmanda gözlenemiyor → 0 yazılır,
    ama satır atılır ki başarısızlık SIKLIĞI ölçülebilsin (dürüst kısmi çözüm)."""
    from fastapi import HTTPException

    from app.services.agent import AgentError

    def _boom(self, **kw):
        raise AgentError("Gemini patladı")

    W = _patch_router(monkeypatch, ledger, generate=_boom)
    with pytest.raises(HTTPException):
        W._build_worksheet(_req())

    items = ledger.recent()
    assert len(items) == 1
    assert items[0]["status"] == STATUS_FAILED
    assert items[0]["cost_usd"] == 0.0
    # Kotayı yemediğini de doğrula (anonim değil, tenant'lı senaryoda kritik).
    assert ledger.worksheets_used_since("anon", 0) == 0


def test_happy_path_writes_exactly_one_ok_row(monkeypatch, ledger):
    """YANLIŞ-KAYIT: başarılı üretimde TEK 'ok' satırı olmalı (çift kayıt yok)."""
    def _ok(self, **kw):
        return [
            Question(
                number=i + 1, question=f"Soru {i}?", answer="1", solution_steps="a",
                kazanim_kod="M.5.1.1", question_type=QuestionType.ISLEM,
                difficulty=Difficulty.ORTA,
            )
            for i in range(10)
        ]

    W = _patch_router(monkeypatch, ledger, generate=_ok)
    worksheet, meta = W._build_worksheet(_req())
    assert worksheet.question_count == 10

    items = ledger.recent()
    assert len(items) == 1
    assert items[0]["status"] == STATUS_OK
    assert items[0]["question_count"] == 10
    assert ledger.summary()["total"]["failed_generations"] == 0


# ───────────────────── `status` kolonu YOKKEN dereceli yetenek kaybı
#
# CANLI INCIDENT (2026-07-30): kolon varlığı `PRAGMA table_info` ile yoklanıyordu.
# Turso/libSQL yolunda PRAGMA beklenen satırları vermeyince migrasyon sessizce
# atlandı ve `status`'a bakan HER sorgu hataya düştü. Fonksiyonlar fail-open
# olduğu için `/admin/costs/summary` HTTP 200 ile boş `{}` döndü — yani arıza
# görünmez kaldı. Aşağıdaki testler o senaryoyu kilitliyor: kolon olmasa da
# defter YAZAR, OKUR ve kotayı DOĞRU sayar; yalnız failed/ok ayrımı düşer.


@pytest.fixture
def ledger_no_status(ledger):
    """`status` kolonu sorgulanamıyor gibi davranan defter."""
    ledger._has_status = False
    return ledger


def test_record_works_without_status_column(ledger_no_status):
    """En kritik: kolon yoksa INSERT ona DOKUNMAMALI. Aksi halde `record()`
    best-effort olduğu için TÜM maliyet kaydı sessizce düşerdi."""
    ledger_no_status.record(
        tenant_id="user_1", model="gemini-2.5-flash", prompt_tokens=100,
        completion_tokens=50, cost_usd=0.03, grade=5, topic="Kesirler",
        question_count=10, status=STATUS_FAILED,
    )
    items = ledger_no_status.recent()
    assert len(items) == 1, "kolon yokken kayıt düştü — canlı incident bu"
    assert items[0]["cost_usd"] == pytest.approx(0.03)
    assert items[0]["status"] == STATUS_OK, "ayrım yapılamıyor → 'ok' varsayılır"


def test_summary_not_empty_without_status_column(ledger_no_status):
    """INCIDENT REGRESYONU: summary() boş `{}` DÖNMEMELİ (endpoint 200 verip
    boş gövde döndürdüğü için arıza fark edilmemişti)."""
    ledger_no_status.record(tenant_id="u", model="m", prompt_tokens=10,
                            completion_tokens=5, cost_usd=0.5, question_count=3)
    s = ledger_no_status.summary()
    assert s["total"], "summary boş döndü — fail-open sessiz arızası"
    assert s["total"]["generations"] == 1
    assert s["total"]["cost_usd"] == pytest.approx(0.5)
    assert s["total"]["failed_cost_usd"] == 0.0, "ayrım yok → 0"
    assert s["by_model"] and s["by_day"]


def test_quota_still_correct_without_status_column(ledger_no_status):
    """Kolon olmasa bile kota doğru sayılmalı: `question_count>0` şartı
    başarısız/yeniden-üret satırlarını zaten dışarıda tutuyor."""
    ledger_no_status.record(tenant_id="u", model="m", prompt_tokens=1,
                            completion_tokens=1, cost_usd=0.1, question_count=10)
    ledger_no_status.record(tenant_id="u", model="m", prompt_tokens=1,
                            completion_tokens=1, cost_usd=0.1, question_count=0,
                            status=STATUS_FAILED)
    assert ledger_no_status.worksheets_used_since("u", 0) == 1
    assert ledger_no_status.questions_used_since("u", 0) == 10


def test_status_probe_does_not_rely_on_pragma(ledger):
    """`_status_available` kolonu DOĞRUDAN okuyarak yoklar (PRAGMA'ya güvenmez) —
    incident'in kök nedeni PRAGMA'ya güvenmekti."""
    assert ledger._has_status is True
    assert ledger._status_available() is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
