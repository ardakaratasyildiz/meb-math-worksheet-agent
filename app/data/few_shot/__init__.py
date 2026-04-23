"""Few-shot örnek havuzlarının sınıf bazlı toplandığı modül."""
from app.data.few_shot import (
    grade_1,
    grade_2,
    grade_3,
    grade_4,
    grade_5,
    grade_6,
    grade_7,
)

EXAMPLES_BY_GRADE: dict[int, dict[str, list[dict]]] = {
    1: grade_1.EXAMPLES,
    2: grade_2.EXAMPLES,
    3: grade_3.EXAMPLES,
    4: grade_4.EXAMPLES,
    5: grade_5.EXAMPLES,
    6: grade_6.EXAMPLES,
    7: grade_7.EXAMPLES,
}
