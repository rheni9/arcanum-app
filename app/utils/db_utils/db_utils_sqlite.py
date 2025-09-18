"""
Database utilities for the Arcanum application using SQLite.

Provides PostgreSQL connection helpers, request-scoped and standalone
connections, context-managed usage, database reachability check,
and a unified execute-and-commit helper.
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

    Determines the path from the SQLITE_PATH environment variable
    or Flask configuration. Must be an absolute path.

    :return: Absolute path to SQLite database file.
    :raises ValueError: If the database path is invalid or missing.
    """
    raw = os.getenv("SQLITE_PATH") or current_app.config.get("SQLITE_PATH")
    if not raw:
        raise ValueError("SQLITE_PATH is not configured.")
    if raw.startswith("sqlite:"):
        parsed = urlparse(raw)
        if parsed.scheme != "sqlite":
            raise ValueError(
                f"Unsupported scheme in SQLITE_PATH: {parsed.scheme}"
            )
        path = parsed.path
    else:
        path = raw

    if not path:
        raise ValueError("SQLITE_PATH is empty or invalid.")

    db_path = os.path.abspath(os.path.expanduser(path))

    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if not os.path.isdir(db_dir):
        raise ValueError(
            f"Directory for SQLite database does not exist: {db_dir}"
        )

    return db_path


def _open_connection(db_path: str) -> sqlite3.Connection:
    """
    Open a new SQLite connection with standard configuration.

    Configures the connection to:
      - Use Row factory for dict-like row access.
      - Enforce foreign key constraints via PRAGMA.

    :param db_path: Absolute path to the SQLite database file.
    :return: SQLite connection object with configured settings.
    :raises sqlite3.Error: If the connection cannot be established.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
        g.db_conn = _open_connection(db_path)
        logger.debug(
            "[DATABASE|REQUEST] Opened request-scoped connection to '%s'.",
            db_path
        )
    else:
        logger.debug("[DATABASE|REQUEST] Reusing existing request connection.")
    return g.db_conn


def close_request_connection(_exception: BaseException | None = None) -> None:
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
    conn = _open_connection(db_path)
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
    conn = _open_connection(db_path)
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
    Check if the configured SQLite database is reachable

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


def execute_and_commit(query: str, params: tuple | dict | None = None) -> None:
    """
    Execute a parameterized query and commit the transaction.

    Rolls back and raises if execution fails.

    :param query: SQL query string.
    :param params: Query parameters (tuple, dictionary, or None).
    :raises ValueError: If the database path is invalid or missing.
    :raises sqlite3.DatabaseError: If the query fails and cannot be committed.
    """
    conn = get_connection_lazy()
    try:
        conn.execute(query, params or {})
        conn.commit()
        logger.debug(
            "[DATABASE|EXECUTE] Query committed successfully: %s",
            query
        )
    except sqlite3.DatabaseError as e:
        conn.rollback()
        logger.error(
            "[DATABASE|ERROR] Failed to execute and commit query: %s", e
        )
        raise
