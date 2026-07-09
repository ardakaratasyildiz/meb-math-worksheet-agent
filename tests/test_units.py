"""MEB TYMM ünite (tema) katmanı + legacy topic köprüsü testleri."""
import re

from fastapi.testclient import TestClient

from app.data.curriculum import CURRICULUM
from app.data.units import (
    UNITS,
    find_unit_by_kazanim,
    get_unit,
    get_units_for_grade,
    resolve_legacy_topic,
)
from app.main import app
from app.models.schemas import GenerateWorksheetRequest

client = TestClient(app)

_KOD_RE = re.compile(r"^MAT\.(\d)\.\d+\.\d+")


def test_all_grades_have_units():
    for grade in range(1, 9):
        units = get_units_for_grade(grade)
        assert units, f"{grade}. sınıfta ünite yok"


def test_kazanim_kod_format_and_grade_match():
    for grade, units in UNITS.items():
        for u in units:
            assert u["kazanimlar"], f"{u['unit_id']} kazanımsız"
            for k in u["kazanimlar"]:
                m = _KOD_RE.match(k["kod"])
                assert m, f"kod formatı bozuk: {k['kod']}"
                assert int(m.group(1)) == grade, (
                    f"{k['kod']} sınıf {grade} ile uyuşmuyor"
                )


def test_crosswalk_targets_exist_in_legacy_for_grade():
    """Her kazanımın legacy_topic_id'si o sınıfın legacy müfredatında bulunmalı
    (RAG boş bir topic'e filtrelemesin)."""
    for grade, units in UNITS.items():
        legacy_topics = set(CURRICULUM.get(grade, {}).keys())
        for u in units:
            assert u["legacy_topic_id"] in legacy_topics, (
                f"{u['unit_id']} → {u['legacy_topic_id']} sınıf {grade}'te yok"
            )
            for k in u["kazanimlar"]:
                assert k["legacy_topic_id"] in legacy_topics, (
                    f"{k['kod']} → {k['legacy_topic_id']} sınıf {grade}'te yok"
                )


def test_resolve_and_find_helpers():
    u = get_units_for_grade(7)[0]
    kod = u["kazanimlar"][0]["kod"]
    # ünite geneli
    assert resolve_legacy_topic(7, u["unit_id"]) == u["legacy_topic_id"]
    # kazanım bazlı
    assert resolve_legacy_topic(7, u["unit_id"], kod) == u["kazanimlar"][0][
        "legacy_topic_id"
    ]
    g, found = find_unit_by_kazanim(kod)
    assert g == 7 and found["unit_id"] == u["unit_id"]
    assert find_unit_by_kazanim("MAT.9.99.99") is None


def test_get_unit_none_for_unknown():
    assert get_unit(7, "yok-boyle-bir-unite") is None


def test_request_unit_xor_topic():
    u = get_units_for_grade(5)[0]
    # unit_id ile geçerli
    GenerateWorksheetRequest(grade=5, unit_id=u["unit_id"], question_count=5)
    # topic_id ile geçerli (geriye-uyum)
    GenerateWorksheetRequest(grade=5, topic_id="cebir", question_count=5)
    # ikisi de yoksa hata
    try:
        GenerateWorksheetRequest(grade=5, question_count=5)
        assert False, "unit/topic yokken geçmemeliydi"
    except Exception:
        pass


def test_api_list_units_and_kazanimlar():
    r = client.get("/api/curriculum/grades/7/units")
    assert r.status_code == 200
    data = r.json()
    assert data["grade"] == 7
    assert len(data["units"]) == len(get_units_for_grade(7))
    unit_id = data["units"][0]["unit_id"]

    r2 = client.get(f"/api/curriculum/grades/7/units/{unit_id}/kazanimlar")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["unit_id"] == unit_id
    assert d2["kazanimlar"]
    assert d2["kazanimlar"][0]["kod"].startswith("MAT.7.")

    # bilinmeyen ünite → 404
    r3 = client.get("/api/curriculum/grades/7/units/yok/kazanimlar")
    assert r3.status_code == 404
