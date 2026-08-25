"""Rate-limit kimliği (gerçek ziyaretçi IP'si) + quick-eval eşik profili.

Pytest gerektirmez — `python tests/test_ratelimit_identity_and_eval_gate.py`.
Ağ/LLM çağrısı yok.

A) RATE LIMIT: `_identifier` kimliği soket peer'ından türetiyor. Render uygulamaya
   kendi iç IP'siyle (10.x) bağlandığı ve uvicorn varsayılan olarak yalnız
   127.0.0.1'e güvendiği için `X-Forwarded-For` HİÇ okunmuyordu → anonim
   ziyaretçilerin TAMAMI aynı kovayı paylaşıyordu (5/dk + 30/saat). Kanıt: prod
   log'unda istemci `10.24.184.2`. Düzeltme `start.sh`'de bir başlatma bayrağı
   (`--forwarded-allow-ips 10.0.0.0/8`) olduğu için KODDAN GÖRÜNMEZ; bu test o
   bayrağın kaybolmasını ve yanlış (`*`) değere kaymasını engeller.

   "*" NEDEN YANLIŞ: uvicorn `always_trust` modunda XFF'in EN SOLUNDAKİ girdiyi
   alır — o girdi tamamen istemcinin yazdığı değerdir → saldırgan her istekte
   farklı IP uydurup sınırsız kova açar (maliyet-DoS). CIDR'de liste SAĞDAN
   taranır, Render'ın eklediği gerçek IP kazanır.

B) QUICK-EVAL: PR gate ile gece koşusu aynı eşiklere bakıyordu ama quick mod TEK
   üretimin soruları üzerinden ortalama alıyor. Ölçülen: 0.5960 / 0.5969 / bir
   geçen koşu — eşik 0.60'ta yazı-tura. `profiles.quick` PR gate'ini katastrofik
   regresyon kapısına çevirir; gece koşusu hassas kalır.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from uvicorn.middleware.proxy_headers import _TrustedHosts  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "eval"))
from check_regression import apply_profile, evaluate  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        _failures.append(msg)
        print(f"  FAIL {msg}")


# ── A) Rate limit kimliği ───────────────────────────────────────────────────
def test_start_command_trusts_render_network() -> None:
    print("\n[A1] start.sh gerçek ziyaretçi IP'sini çözecek şekilde başlatıyor")
    sh = io.open(ROOT / "start.sh", encoding="utf-8").read()
    check("--forwarded-allow-ips" in sh, "uvicorn --forwarded-allow-ips bayrağı var")
    check("10.0.0.0/8" in sh, "Render iç ağı (10.0.0.0/8) varsayılan güvenilen ağ")
    check(
        '--forwarded-allow-ips "*"' not in sh and "--forwarded-allow-ips *" not in sh,
        "wildcard '*' KULLANILMIYOR (spoof edilebilir kimlik)",
    )
    rj = io.open(ROOT / "render.yaml", encoding="utf-8").read()
    check("FORWARDED_ALLOW_IPS" in rj, "render.yaml'da env olarak da görünür")


def test_cidr_trust_resolves_real_client_and_blocks_spoof() -> None:
    print("\n[A2] CIDR güveni: gerçek IP çözülür, soldan uydurma yok sayılır")
    cidr = _TrustedHosts("10.0.0.0/8")
    check("10.24.184.2" in cidr, "Render iç IP'si güvenilir sayılıyor")
    check("85.100.1.1" not in cidr, "ziyaretçi IP'si güvenilir DEĞİL (doğru)")
    real = cidr.get_trusted_client_host("85.100.1.1, 10.24.184.2")
    check(real == "85.100.1.1", f"gerçek ziyaretçi çözüldü ({real})")
    spoofed = cidr.get_trusted_client_host("1.2.3.4, 85.100.1.1, 10.24.184.2")
    check(spoofed == "85.100.1.1", f"soldan uydurma IP yok sayıldı ({spoofed})")
    # Wildcard'ın NEDEN reddedildiğinin kanıtı (regresyon belgesi):
    star = _TrustedHosts("*")
    check(
        star.get_trusted_client_host("1.2.3.4, 85.100.1.1, 10.24.184.2") == "1.2.3.4",
        "'*' saldırganın yazdığı değeri alırdı → bu yüzden kullanılmıyor",
    )


def test_identifier_prefers_verified_session() -> None:
    print("\n[A3] doğrulanmış oturum varsa kimlik IP'ye DEĞİL kullanıcıya bağlanır")
    from app.security import _identifier

    class _Req:
        def __init__(self, headers: dict, ip: str) -> None:
            self.headers = headers
            self.client = type("C", (), {"host": ip})()

    ident = _identifier(_Req({}, "85.100.1.1"))
    check(ident == "ip:85.100.1.1", f"anonim → IP kovası ({ident})")


# ── B) quick-eval eşik profili ──────────────────────────────────────────────
def _thresholds() -> dict:
    return json.loads(
        io.open(ROOT / "scripts" / "eval" / "thresholds.json", encoding="utf-8").read()
    )


def _raw(alignment: float) -> dict:
    """check_regression'ın beklediği minimal ham çıktı."""
    return {
        "metrics": {
            "sprint2_full": {
                "avg_intra_batch_distance": 0.32,
                "avg_cross_batch_distance": 0.31,
                "avg_kazanim_alignment": alignment,
                "avg_delivered_ratio": 1.0,
                "avg_critic_pass_rate": 1.0,
                "successful_runs": 1,
                "total_runs": 1,
                "avg_duration_seconds": 45.0,
            }
        },
        "runs": {"sprint2_full": []},
    }


def test_quick_profile_overlays_only_quick_gate() -> None:
    print("\n[B1] profil yalnız PR gate'ini gevşetir, taban eşik DEĞİŞMEZ")
    base = _thresholds()
    check(
        base["quality"]["avg_kazanim_alignment_min"] == 0.60,
        "taban (gece koşusu) eşiği 0.60'ta KALDI — sapma gizlenmiyor",
    )
    quick = apply_profile(base, "quick")
    check(
        quick["quality"]["avg_kazanim_alignment_min"] == 0.50,
        "quick profili eşiği 0.50'ye çekiyor",
    )
    check(
        base["quality"]["avg_kazanim_alignment_min"] == 0.60,
        "taban sözlük mutasyona uğramadı (derin kopya)",
    )
    check(
        apply_profile(base, None)["quality"]["avg_kazanim_alignment_min"] == 0.60,
        "profil verilmezse davranış eskisi gibi",
    )
    check(
        apply_profile(base, "olmayan")["quality"]["avg_kazanim_alignment_min"] == 0.60,
        "bilinmeyen profil tabanla devam eder (CI'ı kırmaz)",
    )


def test_observed_values_pass_quick_but_catastrophe_still_fails() -> None:
    print("\n[B2] ölçülen değerler geçer, ÇÖKÜŞ hâlâ yakalanır")
    base = _thresholds()
    quick = apply_profile(base, "quick")
    for observed in (0.5960, 0.5969):
        ok, _ = evaluate(_raw(observed), quick, "sprint2_full")
        check(ok, f"quick gate: gerçekte ölçülen {observed} artık GEÇİYOR")
        ok_base, _ = evaluate(_raw(observed), base, "sprint2_full")
        check(not ok_base, f"taban gate: {observed} hâlâ FAIL (gece koşusu hassas)")
    ok, lines = evaluate(_raw(0.35), quick, "sprint2_full")
    check(not ok, "quick gate: 0.35 (çöküş) YAKALANIYOR")
    check(
        any("kazanım_alignment" in ln and "FAIL" in ln for ln in lines),
        "çöküşte hata satırı kazanım_alignment'ı işaret ediyor",
    )


def test_quick_sample_size_raised() -> None:
    print("\n[B3] quick mod örneklemi 3 → 8 soru (salınım düşsün)")
    src = io.open(ROOT / "scripts" / "eval" / "ab_runner.py", encoding="utf-8").read()
    check("args.question_count = 8" in src, "quick mod 8 soru üretiyor")
    wf = io.open(ROOT / ".github" / "workflows" / "eval.yml", encoding="utf-8").read()
    # Yalnız GERÇEK çağrı satırlarına bak (yorumlarda da geçiyor).
    calls = [ln for ln in wf.splitlines()
             if "check_regression.py" in ln and not ln.strip().startswith("#")]
    with_profile = [ln for ln in calls if "--profile quick" in ln]
    check(len(calls) == 2, f"iki gate çağrısı var (quick + gece) — bulundu: {len(calls)}")
    check(
        len(with_profile) == 1,
        "profil YALNIZ bir çağrıda (gece koşusu tabanı kullanmaya devam ediyor)",
    )


def test_gate_runs_end_to_end() -> None:
    print("\n[B4] gate gerçekten çalışıyor (alt süreçte, CI'daki gibi)")
    with tempfile.TemporaryDirectory() as d:
        raw_path = Path(d) / "ab_raw_test.json"
        raw_path.write_text(json.dumps(_raw(0.5969)), encoding="utf-8")
        script = str(ROOT / "scripts" / "eval" / "check_regression.py")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r_quick = subprocess.run(
            [sys.executable, script, "--raw", str(raw_path),
             "--config", "sprint2_full", "--profile", "quick"],
            capture_output=True, text=True, env=env,
        )
        check(r_quick.returncode == 0, f"--profile quick → exit 0 (oldu: {r_quick.returncode})")
        r_base = subprocess.run(
            [sys.executable, script, "--raw", str(raw_path), "--config", "sprint2_full"],
            capture_output=True, text=True, env=env,
        )
        check(r_base.returncode == 1, f"profilsiz → exit 1 (oldu: {r_base.returncode})")


def main() -> int:
    for fn in (
        test_start_command_trusts_render_network,
        test_cidr_trust_resolves_real_client_and_blocks_spoof,
        test_identifier_prefers_verified_session,
        test_quick_profile_overlays_only_quick_gate,
        test_observed_values_pass_quick_but_catastrophe_still_fails,
        test_quick_sample_size_raised,
        test_gate_runs_end_to_end,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: rate-limit kimliği + quick-eval profili yerinde")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
