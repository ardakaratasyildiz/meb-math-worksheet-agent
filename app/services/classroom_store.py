"""Sınıf / ödev kalıcılığı (Faz 3.5 — Sınıf modeli, PR 1).

Öğretmen/veli sınıf açar → katılma kodu ile öğrenciler katılır → (PR 2) çözülebilir
quiz ödev atanır → öğrenci çözer → (PR 3) öğretmen sonuçları görür.

WORKSHEET_HISTORY / QUIZ_STORE ile AYNI SQLite/Turso dosyasını paylaşır ama AYRI
tablolar:
    classrooms          → sınıf (sahip = öğretmen tenant, katılma kodu)
    classroom_members   → sınıfa katılan öğrenciler (üye Clerk hesabı şart)
    assignments         → sınıfa atanan ödevler (PR 2'de kullanılır; tablo şimdi oluşur)

Thread-safe (threading.Lock + db_connection deseni). Singleton: CLASSROOM_STORE.
"""
from __future__ import annotations

import json
import logging
import secrets
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)

# Katılma kodu alfabesi — karışan karakterler (0/O, 1/I/L) çıkarıldı (okunabilirlik).
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LEN = 6
_MAX_CODE_TRIES = 12


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


class ClassroomStore:
    """SQLite/Turso tabanlı sınıf deposu."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.history_db_path
        self._lock = threading.Lock()
        self._db = None
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS classrooms (
                id TEXT PRIMARY KEY,
                owner_tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                join_code TEXT NOT NULL UNIQUE,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_classrooms_owner "
            "ON classrooms(owner_tenant_id, created_at DESC)"
        )
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS classroom_members (
                classroom_id TEXT NOT NULL,
                student_tenant_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                joined_at REAL NOT NULL,
                PRIMARY KEY (classroom_id, student_tenant_id)
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_members_student "
            "ON classroom_members(student_tenant_id, joined_at DESC)"
        )
        # assignments — PR 2'de kullanılır; tablo şimdi oluşturulur (quiz_store deseni).
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id TEXT PRIMARY KEY,
                classroom_id TEXT NOT NULL,
                quiz_id TEXT NOT NULL,
                title TEXT NOT NULL,
                due_at REAL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_assignments_classroom "
            "ON assignments(classroom_id, created_at DESC)"
        )
        self._db.commit()

    def _member_count(self, classroom_id: str) -> int:
        assert self._db is not None
        row = self._db.execute(
            "SELECT COUNT(*) FROM classroom_members WHERE classroom_id = ?",
            (classroom_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def _gen_unique_code(self) -> str:
        """Tahmin edilemez + benzersiz katılma kodu üretir (çakışmada yeniden dener)."""
        assert self._db is not None
        for _ in range(_MAX_CODE_TRIES):
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LEN))
            exists = self._db.execute(
                "SELECT 1 FROM classrooms WHERE join_code = ?", (code,)
            ).fetchone()
            if not exists:
                return code
        # Aşırı düşük olasılık — yine de güvenli fallback.
        return uuid.uuid4().hex[:_CODE_LEN].upper()

    def create_classroom(self, *, owner_tenant_id: str, name: str) -> dict:
        """Sınıf oluşturur. {id, name, join_code} döner."""
        cid = uuid.uuid4().hex
        now = time.time()
        with self._lock:
            assert self._db is not None
            code = self._gen_unique_code()
            self._db.execute(
                "INSERT INTO classrooms (id, owner_tenant_id, name, join_code, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (cid, owner_tenant_id, name, code, now),
            )
            self._db.commit()
        return {"id": cid, "name": name, "join_code": code}

    def get_classroom_by_code(self, code: str) -> dict | None:
        """Katılma kodundan sınıfı çözer (büyük harf normalize). Yoksa None."""
        if not code:
            return None
        code = code.strip().upper()
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT id, owner_tenant_id, name FROM classrooms WHERE join_code = ?",
                (code,),
            ).fetchone()
        if not row:
            return None
        return {"id": row[0], "owner_tenant_id": row[1], "name": row[2]}

    def join_classroom(
        self, *, code: str, student_tenant_id: str, display_name: str
    ) -> dict | None:
        """Öğrenciyi katılma koduyla sınıfa ekler (idempotent UPSERT).

        Geçersiz kod → None. Sahibin kendi sınıfına 'öğrenci' olarak katılması
        engellenir (öğretmen zaten sahip). Dönüş: {classroom_id, name}.
        """
        classroom = self.get_classroom_by_code(code)
        if classroom is None:
            return None
        if classroom["owner_tenant_id"] == student_tenant_id:
            # Sahip zaten erişebilir; üye olarak eklemeye gerek yok.
            return {"classroom_id": classroom["id"], "name": classroom["name"]}
        now = time.time()
        label = (display_name or "").strip()[:80] or "Öğrenci"
        with self._lock:
            assert self._db is not None
            self._db.execute(
                """
                INSERT INTO classroom_members (classroom_id, student_tenant_id, display_name, joined_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(classroom_id, student_tenant_id) DO UPDATE SET
                    display_name = excluded.display_name
                """,
                (classroom["id"], student_tenant_id, label, now),
            )
            self._db.commit()
        return {"classroom_id": classroom["id"], "name": classroom["name"]}

    def list_owned(self, owner_tenant_id: str) -> list[dict]:
        """Öğretmenin sahibi olduğu sınıflar (en yeni önce) + üye sayısı."""
        if not owner_tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                """
                SELECT c.id, c.name, c.join_code, c.created_at, COUNT(m.student_tenant_id)
                FROM classrooms c
                LEFT JOIN classroom_members m ON m.classroom_id = c.id
                WHERE c.owner_tenant_id = ?
                GROUP BY c.id
                ORDER BY c.created_at DESC
                """,
                (owner_tenant_id,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "join_code": r[2],
                "created_at": _iso(r[3]),
                "member_count": int(r[4] or 0),
                "role": "owner",
            }
            for r in rows
        ]

    def list_joined(self, student_tenant_id: str) -> list[dict]:
        """Öğrencinin katıldığı (sahibi olmadığı) sınıflar + üye sayısı."""
        if not student_tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                """
                SELECT c.id, c.name, c.created_at,
                       (SELECT COUNT(*) FROM classroom_members m2 WHERE m2.classroom_id = c.id)
                FROM classroom_members m
                JOIN classrooms c ON c.id = m.classroom_id
                WHERE m.student_tenant_id = ?
                ORDER BY m.joined_at DESC
                """,
                (student_tenant_id,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "created_at": _iso(r[2]),
                "member_count": int(r[3] or 0),
                "role": "student",
            }
            for r in rows
        ]

    def get_classroom(self, classroom_id: str, requester_tenant_id: str) -> dict | None:
        """Sınıf detayı — yalnız sahip veya üye erişir. Erişim yoksa None.

        Sahip: join_code + tam üye listesi görür. Üye: ad + üye sayısı (kod yok).
        """
        if not classroom_id or not requester_tenant_id:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT id, owner_tenant_id, name, join_code, created_at "
                "FROM classrooms WHERE id = ?",
                (classroom_id,),
            ).fetchone()
            if not row:
                return None
            is_owner = row[1] == requester_tenant_id
            is_member = False
            if not is_owner:
                is_member = (
                    self._db.execute(
                        "SELECT 1 FROM classroom_members "
                        "WHERE classroom_id = ? AND student_tenant_id = ?",
                        (classroom_id, requester_tenant_id),
                    ).fetchone()
                    is not None
                )
            if not is_owner and not is_member:
                return None
            members: list[dict] = []
            if is_owner:
                mrows = self._db.execute(
                    "SELECT student_tenant_id, display_name, joined_at "
                    "FROM classroom_members WHERE classroom_id = ? "
                    "ORDER BY joined_at ASC",
                    (classroom_id,),
                ).fetchall()
                members = [
                    {
                        "student_tenant_id": m[0],
                        "display_name": m[1],
                        "joined_at": _iso(m[2]),
                    }
                    for m in mrows
                ]
            member_count = self._member_count(classroom_id)
        return {
            "id": row[0],
            "name": row[2],
            "join_code": row[3] if is_owner else None,
            "created_at": _iso(row[4]),
            "is_owner": is_owner,
            "member_count": member_count,
            "members": members,  # yalnız sahip için dolu
        }

    # ── Ödevler (Faz 3.5 PR 2) ───────────────────────────────────────────────

    def is_member(self, classroom_id: str, tenant_id: str) -> bool:
        """tenant sınıfın sahibi VEYA üyesi mi (ödev erişim kontrolü)."""
        if not classroom_id or not tenant_id:
            return False
        with self._lock:
            assert self._db is not None
            owner = self._db.execute(
                "SELECT 1 FROM classrooms WHERE id = ? AND owner_tenant_id = ?",
                (classroom_id, tenant_id),
            ).fetchone()
            if owner:
                return True
            member = self._db.execute(
                "SELECT 1 FROM classroom_members "
                "WHERE classroom_id = ? AND student_tenant_id = ?",
                (classroom_id, tenant_id),
            ).fetchone()
        return member is not None

    def create_assignment(
        self,
        *,
        classroom_id: str,
        owner_tenant_id: str,
        quiz_id: str,
        title: str,
        due_at: float | None = None,
    ) -> dict | None:
        """Sınıfa ödev (quiz) atar — yalnız sınıf sahibi. Sahip değilse None.

        quiz'in sahibe ait olduğu doğrulaması ÇAĞIRANA aittir (router QUIZ_STORE ile).
        due_at: opsiyonel son teslim epoch'u (çağıran YYYY-MM-DD'den çevirir).
        """
        with self._lock:
            assert self._db is not None
            owns = self._db.execute(
                "SELECT 1 FROM classrooms WHERE id = ? AND owner_tenant_id = ?",
                (classroom_id, owner_tenant_id),
            ).fetchone()
            if not owns:
                return None
            aid = uuid.uuid4().hex
            now = time.time()
            self._db.execute(
                "INSERT INTO assignments (id, classroom_id, quiz_id, title, due_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (aid, classroom_id, quiz_id, title, due_at, now),
            )
            self._db.commit()
        return {"id": aid, "created_at": _iso(now)}

    def get_assignment(self, assignment_id: str) -> dict | None:
        """Ödevi getirir (erişim kontrolü çağırana ait: is_member)."""
        if not assignment_id:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT id, classroom_id, quiz_id, title, created_at "
                "FROM assignments WHERE id = ?",
                (assignment_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "classroom_id": row[1],
            "quiz_id": row[2],
            "title": row[3],
            "created_at": _iso(row[4]),
        }

    def list_assignments(self, classroom_id: str) -> list[dict]:
        """Sınıfa atanmış ödevler (en yeni önce). Öğretmen sınıf detayında görür."""
        if not classroom_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT id, quiz_id, title, created_at, due_at FROM assignments "
                "WHERE classroom_id = ? ORDER BY created_at DESC",
                (classroom_id,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "quiz_id": r[1],
                "title": r[2],
                "created_at": _iso(r[3]),
                "due_at": _iso(r[4]) if r[4] is not None else None,
            }
            for r in rows
        ]

    def list_my_assignments(self, student_tenant_id: str) -> list[dict]:
        """Öğrencinin katıldığı sınıflardaki ödevler + çözüldü durumu/skor.

        attempts (quiz_store tablosu, aynı DB) ile LEFT JOIN — solved = deneme var mı.
        Çok denemede en iyi skor gösterilir.
        """
        if not student_tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                """
                SELECT a.id, a.classroom_id, c.name, a.quiz_id, a.title, a.created_at,
                       COUNT(att.id), MAX(att.score), MAX(att.total), a.due_at
                FROM classroom_members m
                JOIN assignments a ON a.classroom_id = m.classroom_id
                JOIN classrooms c ON c.id = a.classroom_id
                LEFT JOIN attempts att
                       ON att.assignment_id = a.id AND att.solver_tenant_id = ?
                WHERE m.student_tenant_id = ?
                GROUP BY a.id
                ORDER BY a.created_at DESC
                """,
                (student_tenant_id, student_tenant_id),
            ).fetchall()
        out: list[dict] = []
        for r in rows:
            solved = int(r[6] or 0) > 0
            out.append(
                {
                    "assignment_id": r[0],
                    "classroom_id": r[1],
                    "classroom_name": r[2],
                    "quiz_id": r[3],
                    "title": r[4],
                    "created_at": _iso(r[5]),
                    "solved": solved,
                    "score": int(r[7]) if (solved and r[7] is not None) else None,
                    "total": int(r[8]) if (solved and r[8] is not None) else None,
                    "due_at": _iso(r[9]) if r[9] is not None else None,
                }
            )
        return out

    def assignment_results(
        self, assignment_id: str, owner_tenant_id: str
    ) -> dict | None:
        """Bir ödevin sonuç panosu (sınıf sahibi-only). Sahip değilse None.

        Sınıf roster'ı bazlı: her ÜYE bir satır (çözmeyen de görünür → kimin yapmadığı
        belli). Dönüş: {title, question_count, member_count, solved_count,
        items:[{student_tenant_id, display_name, solved, score, total, completed_at}]}.
        """
        if not assignment_id or not owner_tenant_id:
            return None
        with self._lock:
            assert self._db is not None
            a = self._db.execute(
                "SELECT a.classroom_id, a.quiz_id, a.title, c.owner_tenant_id "
                "FROM assignments a JOIN classrooms c ON c.id = a.classroom_id "
                "WHERE a.id = ?",
                (assignment_id,),
            ).fetchone()
            if not a or a[3] != owner_tenant_id:
                return None
            classroom_id, quiz_id, title = a[0], a[1], a[2]
            qrow = self._db.execute(
                "SELECT questions_json FROM quizzes WHERE id = ?", (quiz_id,)
            ).fetchone()
            rows = self._db.execute(
                """
                SELECT m.student_tenant_id, m.display_name,
                       COUNT(att.id), MAX(att.score), MAX(att.total), MAX(att.completed_at)
                FROM classroom_members m
                LEFT JOIN attempts att
                       ON att.assignment_id = ? AND att.solver_tenant_id = m.student_tenant_id
                WHERE m.classroom_id = ?
                GROUP BY m.student_tenant_id
                ORDER BY m.display_name
                """,
                (assignment_id, classroom_id),
            ).fetchall()
        question_count = 0
        if qrow and qrow[0]:
            try:
                question_count = len(json.loads(qrow[0]).get("questions", []))
            except json.JSONDecodeError:
                question_count = 0
        items: list[dict] = []
        solved_count = 0
        for r in rows:
            solved = int(r[2] or 0) > 0
            if solved:
                solved_count += 1
            items.append(
                {
                    "student_tenant_id": r[0],
                    "display_name": r[1],
                    "solved": solved,
                    "score": int(r[3]) if (solved and r[3] is not None) else None,
                    "total": int(r[4]) if (solved and r[4] is not None) else None,
                    "completed_at": _iso(r[5]) if (solved and r[5] is not None) else None,
                }
            )
        return {
            "title": title,
            "question_count": question_count,
            "member_count": len(items),
            "solved_count": solved_count,
            "items": items,
        }

    def close(self) -> None:
        with self._lock:
            if self._db is not None:
                try:
                    self._db.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("ClassroomStore close hatası: %s", exc)
                self._db = None


CLASSROOM_STORE = ClassroomStore()
