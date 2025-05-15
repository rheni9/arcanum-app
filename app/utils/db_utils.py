"""
Database utilities for Arcanum SQLite connections.

Handles:
- Request-scoped lazy connections via g.
- Standalone connections for services.
- Context-managed connections for scripts.
- Database existence checks.
"""

import os
import logging
import sqlite3
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Generator
from flask import g, current_app

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """
    Resolve SQLite database file path from DATABASE_URL or config.

    :return: Absolute path to SQLite database file.
    :rtype: str
    :raises ValueError: If DATABASE_URL is invalid.
    """
    db_url = (
        os.getenv("DATABASE_URL")
        or current_app.config.get("SQLALCHEMY_DATABASE_URI")
    )
    if not db_url:
        raise ValueError("DATABASE_URL is not configured.")

    parsed = urlparse(db_url)
    if parsed.scheme != "sqlite":
        raise ValueError(
            f"Unsupported scheme in DATABASE_URL: {parsed.scheme}"
        )

    path = parsed.path
    if not path:
        raise ValueError("DATABASE_URL path is empty.")

    if path.startswith("//"):
        path = path[1:]

    return path


def get_connection_lazy() -> sqlite3.Connection:
    """
    Get request-level SQLite connection (lazy-loaded).

    Opens a new connection only if needed for current request.
    Reuses existing connection within the same request context.

    :return: SQLite connection object.
    :rtype: sqlite3.Connection
    """
    if "db_conn" not in g:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        g.db_conn = conn

        logger.debug(
            "[DB|REQUEST] Lazily opened request connection to '%s'.", db_path
        )
    else:
        logger.debug("[DB|REQUEST] Reusing existing request connection.")

    return g.db_conn


def close_request_connection(_exception=None):
    """
    Close request-level SQLite connection after request ends.

    :param _error: Optional exception info from Flask teardown.
    :type _error: Exception | None
    """
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()
        logger.debug("[DB|REQUEST] Closed request connection.")


def get_connection_standalone() -> sqlite3.Connection:
    """
    Get standalone SQLite connection (not request-bound).

    :return: SQLite connection.
    :rtype: sqlite3.Connection
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    logger.debug(
        "[DB|STANDALONE] Opened standalone connection to '%s'.", db_path
    )
    return conn


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context-managed standalone SQLite connection (for scripts/tasks).

    Enables foreign keys and dict row access. Ensures proper closure.

    :yields: SQLite connection.
    :rtype: Generator[sqlite3.Connection, None, None]
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    logger.debug(
        "[DB|STANDALONE] Opened standalone connection to '%s'.", db_path
    )

    try:
        yield conn
    finally:
        conn.close()
        logger.debug(
            "[DB|STANDALONE] Closed standalone connection to '%s'.", db_path
        )


def ensure_db_exists() -> None:
    """
    Ensure that the configured SQLite database file exists and is accessible.

    Logs warning if file is missing or inaccessible.
    Logs info if file exists.
    """
    db_path = get_db_path()

    if not os.path.isfile(db_path):
        logger.warning(
            "[DB|CHECK] Database file '%s' does not exist.", db_path
        )
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA schema_version;")
        conn.close()
    except sqlite3.Error as e:
        logger.warning(
            "[DB|CHECK] Database '%s' is not accessible: %s", db_path, e
        )
        return

    logger.info(
        "[DB|CHECK] Database '%s' exists and is accessible.", db_path
    )
