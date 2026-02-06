import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data.sqlite3"
DB_PATH = Path(os.environ.get("APP_DB_PATH", DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                summary TEXT NOT NULL,
                position INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_applications_position ON applications(position)"
        )
        conn.commit()
    finally:
        conn.close()


def fetch_all_applications() -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, summary, position FROM applications ORDER BY position ASC"
        ).fetchall()
        return rows
    finally:
        conn.close()


def get_application_by_id(application_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, summary, position FROM applications WHERE id = ?",
            (application_id,),
        ).fetchone()
        return row
    finally:
        conn.close()


def get_max_position(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(position) AS max_pos FROM applications").fetchone()
    if row is None or row["max_pos"] is None:
        return 0
    return int(row["max_pos"])


def insert_application_at_position(name: str, summary: str, position: int) -> int:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE applications SET position = position + 1 WHERE position >= ?",
            (position,),
        )
        cursor = conn.execute(
            "INSERT INTO applications (name, summary, position) VALUES (?, ?, ?)",
            (name, summary, position),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def insert_application_start(name: str, summary: str) -> int:
    return insert_application_at_position(name, summary, 1)


def insert_application_end(name: str, summary: str) -> int:
    conn = get_connection()
    try:
        position = get_max_position(conn) + 1
        cursor = conn.execute(
            "INSERT INTO applications (name, summary, position) VALUES (?, ?, ?)",
            (name, summary, position),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def insert_application_between(
    name: str, summary: str, before_id: int, after_id: int
) -> int:
    conn = get_connection()
    try:
        before_row = conn.execute(
            "SELECT position FROM applications WHERE id = ?", (before_id,)
        ).fetchone()
        after_row = conn.execute(
            "SELECT position FROM applications WHERE id = ?", (after_id,)
        ).fetchone()
        if before_row is None or after_row is None:
            raise ValueError("before_id or after_id not found")

        before_pos = int(before_row["position"])
        after_pos = int(after_row["position"])
        if before_pos >= after_pos:
            raise ValueError("before_id must be ranked before after_id")

        insert_pos = before_pos + 1
        conn.execute(
            "UPDATE applications SET position = position + 1 WHERE position >= ?",
            (insert_pos,),
        )
        cursor = conn.execute(
            "INSERT INTO applications (name, summary, position) VALUES (?, ?, ?)",
            (name, summary, insert_pos),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def delete_application(application_id: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT position FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if row is None:
            raise ValueError("application not found")
        position = int(row["position"])
        conn.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        conn.execute(
            "UPDATE applications SET position = position - 1 WHERE position > ?",
            (position,),
        )
        conn.commit()
    finally:
        conn.close()


def move_application(application_id: int, new_position: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT position FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if row is None:
            raise ValueError("application not found")

        current_position = int(row["position"])
        max_position = get_max_position(conn)
        if new_position < 1 or new_position > max_position:
            raise ValueError("new_position out of range")

        if new_position == current_position:
            return

        if new_position < current_position:
            conn.execute(
                "UPDATE applications SET position = position + 1 "
                "WHERE position >= ? AND position < ?",
                (new_position, current_position),
            )
        else:
            conn.execute(
                "UPDATE applications SET position = position - 1 "
                "WHERE position > ? AND position <= ?",
                (current_position, new_position),
            )

        conn.execute(
            "UPDATE applications SET position = ? WHERE id = ?",
            (new_position, application_id),
        )
        conn.commit()
    finally:
        conn.close()
