"""
SQLite persistence for Dib user profile, focus sessions, and to-do items.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from core import BASE_DIR, calculate_session_xp

DB_PATH = BASE_DIR / "data" / "dib.db"


def get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                companion TEXT NOT NULL DEFAULT 'coruja',
                total_xp INTEGER NOT NULL DEFAULT 0,
                total_minutes INTEGER NOT NULL DEFAULT 0,
                sessions_completed INTEGER NOT NULL DEFAULT 0,
                focus_duration INTEGER NOT NULL DEFAULT 25,
                break_duration INTEGER NOT NULL DEFAULT 5
            );
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO profile (
                id, companion, total_xp, total_minutes, sessions_completed, focus_duration, break_duration
            )
            VALUES (1, 'coruja', 0, 0, 0, 25, 5);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )


def get_profile(db_path: Path = DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with get_conn(db_path) as conn:
        row = conn.execute("SELECT * FROM profile WHERE id = 1;").fetchone()
        return dict(row)


def update_companion(companion_key: str, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE profile SET companion = ? WHERE id = 1;",
            (companion_key,),
        )


def update_durations(focus_min: int, break_min: int, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE profile SET focus_duration = ?, break_duration = ? WHERE id = 1;",
            (int(focus_min), int(break_min)),
        )


def record_focus_session(minutes: int, db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Increment total focus minutes, completed session counter, and XP."""
    init_db(db_path)
    earned_xp = calculate_session_xp(minutes)
    with get_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE profile
            SET total_xp = total_xp + ?,
                total_minutes = total_minutes + ?,
                sessions_completed = sessions_completed + 1
            WHERE id = 1;
            """,
            (earned_xp, int(minutes)),
        )
    return get_profile(db_path)


def list_tasks(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT id, title, done, created_at FROM tasks ORDER BY done ASC, id DESC;"
        ).fetchall()
        return [dict(r) for r in rows]


def add_task(title: str, db_path: Path = DB_PATH) -> None:
    cleaned = title.strip()
    if not cleaned:
        return
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO tasks (title, done, created_at) VALUES (?, 0, ?);",
            (cleaned, datetime.now().isoformat(timespec="seconds")),
        )


def toggle_task(task_id: int, done: bool, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE tasks SET done = ? WHERE id = ?;",
            (1 if done else 0, int(task_id)),
        )


def clear_completed_tasks(db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM tasks WHERE done = 1;")
