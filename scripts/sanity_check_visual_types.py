"""Sanity check: yeni görsel/yapısal tiplerin tüm bileşenlerini doğrula."""
from app.data.few_shot.grade_5 import EXAMPLES as e5
from app.data.few_shot.grade_6 import EXAMPLES as e6
from app.data.few_shot.grade_7 import EXAMPLES as e7
from app.models.enums import QuestionType as QT
from app.services.diversity import (
    TOPIC_VISUAL_BIAS,
    distribute_question_types,
)
from app.models.enums import Difficulty

NEW_TYPES = {
    QT.SALT_ISLEM,
    QT.TABLO_SORUSU,
    QT.GORSEL_GEOMETRI,
    QT.GRAFIK_OKUMA,
    QT.ORUNTU_SEKIL,
}

print("=== Few-shot örneklerin yeni-tip dağılımı ===")
all_examples = {"grade_5": e5, "grade_6": e6, "grade_7": e7}
for grade_name, exs in all_examples.items():
    by_type: dict[QT, list[str]] = {}
    for kazanim, items in exs.items():
        for ex in items:
            t = ex["type"]
            if t in NEW_TYPES:
                by_type.setdefault(t, []).append(kazanim)
    print(f"\n{grade_name}:")
    if not by_type:
        print("  - (yeni tip yok)")
    for t, kazanimlar in by_type.items():
        print(f"  {t.value}: {len(kazanimlar)} örnek -> {kazanimlar}")

print("\n=== Topic-aware distribution (zorluk = orta, n = 10) ===")
for topic in TOPIC_VISUAL_BIAS:
    d = distribute_question_types(10, Difficulty.ORTA, topic_id=topic)
    pretty = {k.value: v for k, v in d.items()}
    print(f"  {topic:18} -> {pretty}")

print("\n=== Sınır durumlar ===")
print("  veri_isleme + zor + 3 ->", {k.value: v for k, v in distribute_question_types(3, Difficulty.ZOR, topic_id="veri_isleme").items()})
print("  geometri + kolay + 1 ->", {k.value: v for k, v in distribute_question_types(1, Difficulty.KOLAY, topic_id="geometri").items()})
print("  bilinmeyen topic ->", {k.value: v for k, v in distribute_question_types(10, Difficulty.ORTA, topic_id="UNKNOWN").items()})

print("\nOK")
