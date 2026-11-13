"""SQLite connection management using the Python standard library."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol


class DatabaseConnectionManager(Protocol):
    """Protocol for database connection managers injected into repositories."""

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield an active SQLite connection within a transaction boundary."""
        ...


class SQLiteConnectionManager:
    """Manages SQLite connections with automatic transaction handling."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path: str = str(db_path)
        self._memory_conn: sqlite3.Connection | None = None

    @property
    def db_path(self) -> str:
        """Return the configured database path."""
        return self._db_path

    def _configure_connection(self, conn: sqlite3.Connection) -> sqlite3.Connection:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Provide a transactional SQLite connection context."""
        if self._db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = self._configure_connection(sqlite3.connect(":memory:"))
            conn = self._memory_conn
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            return

        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        conn = self._configure_connection(sqlite3.connect(self._db_path))
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close(self) -> None:
        """Close any persistent in-memory connection."""
        if self._memory_conn is not None:
            self._memory_conn.close()
            self._memory_conn = None
