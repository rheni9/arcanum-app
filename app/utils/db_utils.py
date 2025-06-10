"""
Database utilities for the Arcanum Flask application.

Provides SQLite connection helpers, request-scoped and standalone
connections, context-managed usage, and database presence check.
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
    Resolve the SQLite database file path.

    Determines the path from Flask configuration
    or the DATABASE_URL environment variable.

    :return: Absolute path to SQLite database file.
    :raises ValueError: If the database path is invalid or missing.
    """
    db_url = (
        current_app.config.get("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
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
    Get a request-scoped SQLite connection.

    Opens a new connection for the current request context if needed,
    or reuses the existing one.

    :return: SQLite connection object.
    :raises ValueError: If the database path is invalid or missing.
    :raises sqlite3.DatabaseError: If the connection fails.
    """
    if "db_conn" not in g:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db_conn = conn
        logger.debug(
            "[DATABASE|REQUEST] Opened request-scoped connection to '%s'.",
            db_path
        )
    else:
        logger.debug("[DATABASE|REQUEST] Reusing existing request connection.")
    return g.db_conn


def close_request_connection(_exception: Exception | None = None) -> None:
    """
    Close the request-scoped SQLite connection after request ends.

    :param _exception: Exception from Flask teardown (ignored).
    """
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()
        logger.debug("[DATABASE|REQUEST] Closed request connection.")


def get_connection_standalone() -> sqlite3.Connection:
    """
    Get a standalone SQLite connection.

    This connection is not tied to a Flask request context.

    :return: SQLite connection object.
    :raises ValueError: If the database path is invalid or missing.
    :raises sqlite3.DatabaseError: If the connection fails.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    logger.debug(
        "[DATABASE|STANDALONE] Opened standalone connection to '%s'.", db_path
    )
    return conn


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Provide a context-managed standalone SQLite connection.

    Yields a connection with foreign keys enabled and Row factory set.

    :yields: SQLite connection object.
    :raises ValueError: If the database path is invalid or missing.
    :raises sqlite3.DatabaseError: If the connection fails.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    logger.debug(
        "[DATABASE|STANDALONE] Opened standalone connection to '%s'.",
        db_path
    )
    try:
        yield conn
    finally:
        conn.close()
        logger.debug(
            "[DATABASE|STANDALONE] Closed standalone connection to '%s'.",
            db_path
        )


def ensure_db_exists() -> None:
    """
    Check if the configured SQLite database file exists and is accessible.

    Logs a warning if the database is missing or inaccessible.
    Logs an info message if the file exists and is readable.

    :raises ValueError: If the database path is invalid or missing.
    :raises sqlite3.Error: If the database file is unreachable or broken.
    """
    db_path = get_db_path()
    if not os.path.isfile(db_path):
        logger.warning(
            "[DATABASE|CHECK] Database file '%s' does not exist.", db_path
        )
        return
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA schema_version;")
        conn.close()
    except sqlite3.Error as e:
        logger.warning(
            "[DATABASE|CHECK] Database '%s' is not accessible: %s", db_path, e
        )
        return
    logger.info(
        "[DATABASE|CHECK] Database '%s' exists and is accessible.", db_path
    )


def execute_and_commit(query: str, params: tuple) -> None:
    """
    Execute a parameterized query and commit the transaction.

    Rolls back and raises if execution fails.

    :param query: SQL query string.
    :param params: Query parameters.

    :raises ValueError: If the database path is invalid or missing.
    :raises sqlite3.DatabaseError: If the query fails and cannot be committed.
    """
    conn = get_connection_lazy()
    try:
        conn.execute(query, params)
        conn.commit()
        logger.debug("[DATABASE|EXECUTE] Query committed successfully.")
    except sqlite3.DatabaseError as e:
        conn.rollback()
        logger.error(
            "[DATABASE|ERROR] Failed to execute and commit query: %s", e
        )
        raise
