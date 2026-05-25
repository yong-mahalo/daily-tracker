import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import DATABASE_PATH

_MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_migrations():
    """Apply all .sql files in migrations/ in order. Safe to call on every startup."""
    if not _MIGRATIONS_DIR.exists():
        return
    migration_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _migrations (filename TEXT PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')))"
        )
        applied = {row[0] for row in conn.execute("SELECT filename FROM _migrations")}
        for path in migration_files:
            if path.name not in applied:
                sql = path.read_text()
                conn.executescript(sql)
                conn.execute("INSERT INTO _migrations (filename) VALUES (?)", (path.name,))
                print(f"[db] applied migration: {path.name}")


def fetchall(sql: str, params: tuple = ()) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    with get_db() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> int:
    """Execute a write statement; returns lastrowid."""
    with get_db() as conn:
        cur = conn.execute(sql, params)
    return cur.lastrowid
