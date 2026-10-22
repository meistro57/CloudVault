import sqlite3
from pathlib import Path

SCHEMA = """CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    remote_path TEXT NOT NULL,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn
