"""
Database connection utilities.

This module provides a reusable and consistent interface for connecting
to the SQLite database used by the Arcanum application.

The exported `get_connection()` function is a context manager that ensures:
- `PRAGMA foreign_keys = ON` is enabled,
- results can be accessed as dictionaries via `sqlite3.Row`,
- connections are properly closed after use.
"""

import os
import logging
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional

logger = logging.getLogger(__name__)

#  Default database path from PROJECT_ROOT or module location
BASE_DIR = Path(
    os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parent.parent))
)
DEFAULT_DB_PATH = BASE_DIR / "data" / "chatvault.sqlite"


@contextmanager
def get_connection(
    path: Optional[Path] = None
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager to create a configured SQLite connection.

    Enables foreign key constraints and sets row factory for dict-like rows.

    :param path: Optional custom database path (default: production DB)
    :type path: Optional[Path]
    :yields: Configured SQLite3 connection
    :rtype: Generator[sqlite3.Connection, None, None]
    """
    db_path = path or DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        logger.debug("[DB] Opened connection to '%s'.", db_path)
        yield conn
    finally:
        logger.debug("[DB] Closed connection to '%s'.", db_path)
        conn.close()
