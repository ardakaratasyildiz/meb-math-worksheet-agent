"""Sınıf deposu testleri (Faz 3.5 PR 1) — create/join/list/detay + erişim kontrolü.

Pytest gerektirmez — `python tests/test_classroom.py`. LLM/ağ çağrısı yok.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.services.classroom_store import ClassroomStore  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def test_create_and_code() -> None:
    print("create_classroom + benzersiz kod")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = ClassroomStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            c = store.create_classroom(owner_tenant_id="teacher-1", name="5/A Matematik")
            check(bool(c["id"]), "sınıf id döndü")
            check(len(c["join_code"]) == 6, f"6 haneli kod: {c['join_code']}")
            check(c["join_code"].isupper() or c["join_code"].isalnum(), "kod alfanumerik")
            # kod ile çözülebiliyor (büyük/küçük harf toleransı)
            resolved = store.get_classroom_by_code(c["join_code"].lower())
            check(resolved is not None and resolved["id"] == c["id"], "kod (lowercase) çözüldü")
            check(store.get_classroom_by_code("ZZZZZZ") is None, "geçersiz kod None")
        finally:
            store.close()


def test_join() -> None:
    print("join_classroom — geçerli/geçersiz/idempotent/sahip")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = ClassroomStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            c = store.create_classroom(owner_tenant_id="teacher-1", name="Sınıf")
            code = c["join_code"]
            # Geçerli katılım
            r = store.join_classroom(code=code, student_tenant_id="stu-1", display_name="Ali")
            check(r is not None and r["classroom_id"] == c["id"], "öğrenci katıldı")
            # Geçersiz kod
            check(
                store.join_classroom(code="NOPE12", student_tenant_id="stu-2", display_name="X") is None,
                "geçersiz kod None",
            )
            # İdempotent (aynı öğrenci tekrar → ad güncellenir, çift kayıt yok)
            store.join_classroom(code=code, student_tenant_id="stu-1", display_name="Ali Veli")
            detail = store.get_classroom(c["id"], "teacher-1")
            check(detail["member_count"] == 1, f"idempotent: tek üye: {detail['member_count']}")
            check(detail["members"][0]["display_name"] == "Ali Veli", "ad güncellendi")
            # İkinci öğrenci
            store.join_classroom(code=code, student_tenant_id="stu-2", display_name="Ayşe")
            check(store.get_classroom(c["id"], "teacher-1")["member_count"] == 2, "2 üye")
            # Sahip kendi sınıfına 'öğrenci' olarak eklenmez
            store.join_classroom(code=code, student_tenant_id="teacher-1", display_name="Öğretmen")
            check(
                store.get_classroom(c["id"], "teacher-1")["member_count"] == 2,
                "sahip üye olarak eklenmedi",
            )
        finally:
            store.close()


def test_lists() -> None:
    print("list_owned + list_joined")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = ClassroomStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            a = store.create_classroom(owner_tenant_id="teacher-1", name="A")
            store.create_classroom(owner_tenant_id="teacher-1", name="B")
            store.join_classroom(code=a["join_code"], student_tenant_id="stu-1", display_name="Ali")

            owned = store.list_owned("teacher-1")
            check(len(owned) == 2, f"öğretmenin 2 sınıfı: {len(owned)}")
            check(all(o["role"] == "owner" and o["join_code"] for o in owned), "owned: role+kod var")

            joined = store.list_joined("stu-1")
            check(len(joined) == 1 and joined[0]["id"] == a["id"], "öğrenci 1 sınıfa katılı")
            check(joined[0]["role"] == "student", "joined: role student")
            # Öğretmen kendi sınıfına list_joined'de görünmez
            check(store.list_joined("teacher-1") == [], "sahip list_joined'de yok")
        finally:
            store.close()


def test_access_control() -> None:
    print("get_classroom erişim kontrolü (sahip / üye / yabancı)")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = ClassroomStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            c = store.create_classroom(owner_tenant_id="teacher-1", name="Sınıf")
            store.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")
            # Sahip: kod + üye listesi görür
            owner_view = store.get_classroom(c["id"], "teacher-1")
            check(owner_view["is_owner"] is True, "sahip is_owner True")
            check(owner_view["join_code"] is not None, "sahip kodu görür")
            check(len(owner_view["members"]) == 1, "sahip üyeleri görür")
            # Üye: kod GÖRMEZ, üye listesi boş, ama erişebilir
            member_view = store.get_classroom(c["id"], "stu-1")
            check(member_view is not None and member_view["is_owner"] is False, "üye erişti, is_owner False")
            check(member_view["join_code"] is None, "üye kodu GÖRMEZ")
            check(member_view["members"] == [], "üyeye üye listesi sızmaz")
            check(member_view["member_count"] == 1, "üye sayıyı görür")
            # Yabancı: erişemez
            check(store.get_classroom(c["id"], "stranger") is None, "yabancı erişemez (None)")
        finally:
            store.close()


def test_delete_and_leave() -> None:
    print("sınıf silme (sahip, cascade) + sınıftan ayrılma (üye)")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = ClassroomStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            c = store.create_classroom(owner_tenant_id="teacher-1", name="Sınıf")
            store.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")
            store.join_classroom(code=c["join_code"], student_tenant_id="stu-2", display_name="Ece")

            # --- Ayrılma ---
            check(store.leave_classroom(c["id"], "stu-1") is True, "stu-1 ayrıldı")
            check(store.get_classroom(c["id"], "stu-1") is None, "ayrılan artık erişemez")
            check(store.get_classroom(c["id"], "teacher-1")["member_count"] == 1, "üye sayısı 1'e düştü")
            check(store.leave_classroom(c["id"], "stu-1") is False, "üye olmayan ayrılamaz (False)")

            # --- Silme yetkisi ---
            check(store.delete_classroom(c["id"], "stu-2") is False, "üye sınıfı silemez")
            check(store.delete_classroom(c["id"], "stranger") is False, "yabancı silemez")
            check(store.get_classroom(c["id"], "teacher-1") is not None, "yetkisiz denemeler sınıfı silmedi")

            # --- Sahip siler (cascade) ---
            check(store.delete_classroom(c["id"], "teacher-1") is True, "sahip sildi")
            check(store.get_classroom(c["id"], "teacher-1") is None, "silinen sınıf yok")
            check(store.get_classroom(c["id"], "stu-2") is None, "üye de erişemez (cascade)")
            check(len(store.list_owned("teacher-1")) == 0, "öğretmen listesinden düştü")
            check(len(store.list_joined("stu-2")) == 0, "öğrenci listesinden düştü (üyelik cascade)")
        finally:
            store.close()


def test_app_imports() -> None:
    print("uygulama import — classrooms router kayıtlı")
    from app.main import app  # noqa: PLC0415

    paths = {r.path for r in app.routes}
    check("/api/classrooms" in paths, "POST/GET /api/classrooms kayıtlı")
    check("/api/classrooms/join" in paths, "POST /api/classrooms/join kayıtlı")
    check("/api/classrooms/{classroom_id}" in paths, "GET/DELETE /api/classrooms/{id} kayıtlı")
    check("/api/classrooms/{classroom_id}/leave" in paths, "POST /api/classrooms/{id}/leave kayıtlı")


def main() -> int:
    for fn in (
        test_create_and_code,
        test_join,
        test_lists,
        test_access_control,
        test_delete_and_leave,
        test_app_imports,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: sınıf testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
