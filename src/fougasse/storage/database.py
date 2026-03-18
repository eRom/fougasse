"""SQLite database connection and migration management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import sqlite_vec

_MIGRATIONS_DIR = Path(__file__).parent.parent.parent.parent / "migrations"


def get_connection(db_path: Path | str = ":memory:") -> sqlite3.Connection:
    """Create a SQLite connection with WAL mode, FK, and sqlite-vec loaded."""
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row

    # Enable WAL mode for concurrent reads
    db.execute("PRAGMA journal_mode=WAL")
    # Enable foreign keys
    db.execute("PRAGMA foreign_keys=ON")
    # Reasonable busy timeout (5 seconds)
    db.execute("PRAGMA busy_timeout=5000")

    # Load sqlite-vec extension
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    return db


def get_current_version(db: sqlite3.Connection) -> int:
    """Get the current schema version, or 0 if no migrations applied."""
    try:
        row = db.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0 if row else 0
    except sqlite3.OperationalError:
        return 0


def run_migrations(db: sqlite3.Connection, migrations_dir: Path | None = None) -> int:
    """Apply pending SQL migrations in order. Returns number of migrations applied."""
    mdir = migrations_dir or _MIGRATIONS_DIR
    if not mdir.exists():
        return 0

    current = get_current_version(db)
    applied = 0

    # Find and sort migration files
    migration_files = sorted(mdir.glob("*.sql"))

    for mfile in migration_files:
        # Extract version number from filename (e.g., 001_init.sql -> 1)
        try:
            version = int(mfile.stem.split("_")[0])
        except (ValueError, IndexError):
            continue

        if version <= current:
            continue

        # Apply migration
        sql = mfile.read_text(encoding="utf-8")
        db.executescript(sql)
        applied += 1

    return applied


def init_database(
    db_path: Path | str = ":memory:", migrations_dir: Path | None = None
) -> sqlite3.Connection:
    """Initialize database: connect, run migrations, return connection."""
    db = get_connection(db_path)
    run_migrations(db, migrations_dir)
    return db
