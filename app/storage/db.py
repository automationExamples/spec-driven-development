"""
Database - SQLite storage for specs, generations, and runs.

Simple, lightweight storage using Python's built-in sqlite3.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


@dataclass
class Spec:
    """Stored OpenAPI specification"""

    id: str
    name: str
    raw_content: str
    title: str
    version: str
    endpoint_count: int
    created_at: datetime = field(default_factory=_utc_now)


@dataclass
class Generation:
    """Test generation record"""

    id: str
    spec_id: str
    test_dir: str
    files: list[str]
    status: str = "pending"  # pending, completed, failed
    error: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)


@dataclass
class Run:
    """Test run record"""

    id: str
    generation_id: str
    target_url: str
    status: str = "pending"  # pending, running, completed, failed
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total: int = 0
    duration: float = 0.0
    junit_xml_path: Optional[str] = None
    results_json: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None


class Database:
    """SQLite database for the test generator"""

    def __init__(self, db_path: Path = Path("./data/app.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS specs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    raw_content TEXT NOT NULL,
                    title TEXT NOT NULL,
                    version TEXT NOT NULL,
                    endpoint_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY,
                    spec_id TEXT NOT NULL,
                    test_dir TEXT NOT NULL,
                    files TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (spec_id) REFERENCES specs(id)
                );

                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    generation_id TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    passed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    skipped INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    total INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0,
                    junit_xml_path TEXT,
                    results_json TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (generation_id) REFERENCES generations(id)
                );

                CREATE INDEX IF NOT EXISTS idx_generations_spec_id ON generations(spec_id);
                CREATE INDEX IF NOT EXISTS idx_runs_generation_id ON runs(generation_id);
            """)

    # Spec operations
    def create_spec(
        self, name: str, raw_content: str, title: str, version: str, endpoint_count: int
    ) -> Spec:
        """Create a new spec record"""
        spec = Spec(
            id=str(uuid.uuid4()),
            name=name,
            raw_content=raw_content,
            title=title,
            version=version,
            endpoint_count=endpoint_count,
            created_at=_utc_now(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO specs (id, name, raw_content, title, version, endpoint_count, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    spec.id,
                    spec.name,
                    spec.raw_content,
                    spec.title,
                    spec.version,
                    spec.endpoint_count,
                    spec.created_at.isoformat(),
                ),
            )

        return spec

    def get_spec(self, spec_id: str) -> Optional[Spec]:
        """Get a spec by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM specs WHERE id = ?", (spec_id,)
            ).fetchone()

            if row:
                return Spec(
                    id=row["id"],
                    name=row["name"],
                    raw_content=row["raw_content"],
                    title=row["title"],
                    version=row["version"],
                    endpoint_count=row["endpoint_count"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            return None

    def list_specs(self) -> list[Spec]:
        """List all specs"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM specs ORDER BY created_at DESC"
            ).fetchall()

            return [
                Spec(
                    id=row["id"],
                    name=row["name"],
                    raw_content=row["raw_content"],
                    title=row["title"],
                    version=row["version"],
                    endpoint_count=row["endpoint_count"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    def delete_spec(self, spec_id: str) -> bool:
        """Delete a spec by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM specs WHERE id = ?", (spec_id,))
            return cursor.rowcount > 0

    # Generation operations
    def create_generation(
        self, spec_id: str, test_dir: str, files: list[str]
    ) -> Generation:
        """Create a new generation record"""
        generation = Generation(
            id=str(uuid.uuid4()),
            spec_id=spec_id,
            test_dir=test_dir,
            files=files,
            status="completed",
            created_at=_utc_now(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO generations (id, spec_id, test_dir, files, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    generation.id,
                    generation.spec_id,
                    generation.test_dir,
                    json.dumps(files),
                    generation.status,
                    generation.created_at.isoformat(),
                ),
            )

        return generation

    def get_generation(self, generation_id: str) -> Optional[Generation]:
        """Get a generation by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM generations WHERE id = ?", (generation_id,)
            ).fetchone()

            if row:
                return Generation(
                    id=row["id"],
                    spec_id=row["spec_id"],
                    test_dir=row["test_dir"],
                    files=json.loads(row["files"]),
                    status=row["status"],
                    error=row["error"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            return None

    def list_generations(self, spec_id: Optional[str] = None) -> list[Generation]:
        """List generations, optionally filtered by spec_id"""
        with self._get_connection() as conn:
            if spec_id:
                rows = conn.execute(
                    "SELECT * FROM generations WHERE spec_id = ? ORDER BY created_at DESC",
                    (spec_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM generations ORDER BY created_at DESC"
                ).fetchall()

            return [
                Generation(
                    id=row["id"],
                    spec_id=row["spec_id"],
                    test_dir=row["test_dir"],
                    files=json.loads(row["files"]),
                    status=row["status"],
                    error=row["error"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    def update_generation_status(
        self, generation_id: str, status: str, error: Optional[str] = None
    ) -> bool:
        """Update generation status"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE generations SET status = ?, error = ? WHERE id = ?",
                (status, error, generation_id),
            )
            return cursor.rowcount > 0

    # Run operations
    def create_run(self, generation_id: str, target_url: str) -> Run:
        """Create a new run record"""
        run = Run(
            id=str(uuid.uuid4()),
            generation_id=generation_id,
            target_url=target_url,
            status="pending",
            created_at=_utc_now(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO runs (id, generation_id, target_url, status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    run.id,
                    run.generation_id,
                    run.target_url,
                    run.status,
                    run.created_at.isoformat(),
                ),
            )

        return run

    def get_run(self, run_id: str) -> Optional[Run]:
        """Get a run by ID"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()

            if row:
                return Run(
                    id=row["id"],
                    generation_id=row["generation_id"],
                    target_url=row["target_url"],
                    status=row["status"],
                    passed=row["passed"],
                    failed=row["failed"],
                    skipped=row["skipped"],
                    errors=row["errors"],
                    total=row["total"],
                    duration=row["duration"],
                    junit_xml_path=row["junit_xml_path"],
                    results_json=row["results_json"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None,
                )
            return None

    def list_runs(self, generation_id: Optional[str] = None) -> list[Run]:
        """List runs, optionally filtered by generation_id"""
        with self._get_connection() as conn:
            if generation_id:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE generation_id = ? ORDER BY created_at DESC",
                    (generation_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM runs ORDER BY created_at DESC"
                ).fetchall()

            return [
                Run(
                    id=row["id"],
                    generation_id=row["generation_id"],
                    target_url=row["target_url"],
                    status=row["status"],
                    passed=row["passed"],
                    failed=row["failed"],
                    skipped=row["skipped"],
                    errors=row["errors"],
                    total=row["total"],
                    duration=row["duration"],
                    junit_xml_path=row["junit_xml_path"],
                    results_json=row["results_json"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None,
                )
                for row in rows
            ]

    def update_run(
        self,
        run_id: str,
        status: str,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        errors: int = 0,
        total: int = 0,
        duration: float = 0.0,
        junit_xml_path: Optional[str] = None,
        results_json: Optional[str] = None,
    ) -> bool:
        """Update run with results"""
        completed_at = (
            _utc_now().isoformat() if status in ("completed", "failed") else None
        )

        with self._get_connection() as conn:
            cursor = conn.execute(
                """UPDATE runs SET
                   status = ?, passed = ?, failed = ?, skipped = ?, errors = ?,
                   total = ?, duration = ?, junit_xml_path = ?, results_json = ?,
                   completed_at = ?
                   WHERE id = ?""",
                (
                    status,
                    passed,
                    failed,
                    skipped,
                    errors,
                    total,
                    duration,
                    junit_xml_path,
                    results_json,
                    completed_at,
                    run_id,
                ),
            )
            return cursor.rowcount > 0


# Global database instance
_db: Optional[Database] = None


def get_database(db_path: Optional[Path] = None) -> Database:
    """Get or create the global database instance"""
    global _db
    if _db is None or db_path is not None:
        _db = Database(db_path or Path("./data/app.db"))
    return _db
