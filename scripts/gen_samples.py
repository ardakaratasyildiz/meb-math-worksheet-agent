"""Landing page'ler için tek-seferlik ÖRNEK SORU veri seti üretir.

Neden: /calismalar/<slug> sayfaları build-time'da statik render ediliyor; Google
şu an gerçek soru göremiyor (boş kabuk → yüksek bounce, zayıf SEO). Bu script her
(sınıf, konu) için birkaç örnek soruyu agent pipeline'ıyla (critic+math denetimli)
üretip frontend/lib/sample-questions.json'a yazar. Frontend bunu server-render
eder → gerçek içerik HTML'de, login'siz, anında, 0 request-time maliyeti.

Tek seferlik çalışır; çıktı commit edilir. Müfredat değişince yeniden koşulur.
İnkremental yazar (her combo sonrası) → kesilirse ilerleme korunur, --resume ile
mevcut slug'lar atlanır.

Kullanım:
  PYTHONIOENCODING=utf-8 python scripts/gen_samples.py [--count 3] [--difficulty orta]
      [--limit N] [--resume] [--out frontend/lib/sample-questions.json]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data.curriculum import CURRICULUM  # noqa: E402
from app.models.enums import Difficulty, QuestionType  # noqa: E402
from app.services.agent import AgentError, GeminiAgent  # noqa: E402

# Landing önizlemesi için TEMİZ düz-metin tipler: LaTeX (salt_islem) ve görsel
# tipler (tablo/geometri/grafik/örüntü) hariç → server-render edilen HTML temiz
# ve indekslenebilir kalır.
# "islem" dahil edilmez: saf işlem soruları LaTeX ($$7+6=?$$) üretebiliyor,
# önizleme metnini kirletir. Saf sözel/kavramsal tipler temiz düz-metin verir.
OPEN_ENDED_TYPES = [
    "sozel_problem", "gunluk_hayat", "akil_yurutme",
    "kavram_sorusu", "modelleme",
]

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("gen_samples")
logger.setLevel(logging.INFO)


def _slug(grade: int, topic_id: str) -> str:
    # Frontend curriculum.ts ile aynı kural: "5-sinif-veri-isleme".
    return f"{grade}-sinif-{topic_id.replace('_', '-')}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3, help="combo başına örnek soru")
    ap.add_argument("--difficulty", default="orta", choices=["kolay", "orta", "zor"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--resume", action="store_true", help="mevcut çıktıdaki slug'ları atla")
    ap.add_argument("--types", default=",".join(OPEN_ENDED_TYPES),
                    help="izinli soru tipleri (virgülle). Varsayılan: açık-uçlu sözel.")
    ap.add_argument("--out", default=str(ROOT / "frontend" / "lib" / "sample-questions.json"))
    args = ap.parse_args()

    allowed_types = [QuestionType(t.strip()) for t in args.types.split(",") if t.strip()] or None

    out_path = Path(args.out)
    data: dict[str, dict] = {}
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}

    combos: list[tuple[int, str]] = []
    for grade in sorted(CURRICULUM.keys()):
        for topic_id in CURRICULUM[grade].keys():
            combos.append((grade, topic_id))
    if args.limit:
        combos = combos[: args.limit]

    diff = Difficulty(args.difficulty)
    agent = GeminiAgent()
    done = skipped = failed = 0

    print(f"# Örnek üretimi: {len(combos)} combo × {args.count} soru ({args.difficulty})\n")
    for i, (grade, topic_id) in enumerate(combos, 1):
        slug = _slug(grade, topic_id)
        if args.resume and slug in data and data[slug].get("questions"):
            skipped += 1
            print(f"  [{i}/{len(combos)}] atlandı (resume): {slug}")
            continue
        try:
            qs = agent.generate(
                grade=grade, topic_id=topic_id, kazanim_kod=None,
                difficulty=diff, question_count=args.count, tenant_id="__samples__",
                allowed_types=allowed_types,
            )
            data[slug] = {
                "grade": grade,
                "topic_id": topic_id,
                "difficulty": args.difficulty,
                "questions": [
                    {
                        "question": q.question,
                        "answer": q.answer,
                        "question_type": q.question_type.value,
                        "kazanim_kod": q.kazanim_kod,
                    }
                    for q in qs
                ],
            }
            # İnkremental yaz — kesilse de ilerleme korunur.
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            done += 1
            print(f"  [{i}/{len(combos)}] OK {slug}: {len(qs)} soru")
        except AgentError as exc:
            failed += 1
            logger.warning("HATA %s: %s", slug, exc)

    print(f"\n## Özet: üretildi={done} atlandı={skipped} hata={failed}")
    print(f"  çıktı: {out_path}  ({len(data)} slug)")


if __name__ == "__main__":
    main()
