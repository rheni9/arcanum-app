"""
Database utilities for the Arcanum application using PostgreSQL.

Provides SQLAlchemy connection helpers, request-scoped and standalone
connections, context-managed usage, and database presence check.

Function names and signatures match the SQLite version for backward
compatibility.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Connection
from flask import g
from app.extensions import db  # SQLAlchemy instance

logger = logging.getLogger(__name__)


def get_connection_lazy() -> Connection:
    """
    Get a request-scoped SQLAlchemy connection.

    Opens a new connection for the current request context if needed,
    or reuses the existing one.

    :return: SQLAlchemy Connection object.
    """
    if "db_conn" not in g:
        conn = db.engine.connect()
        g.db_conn = conn
        logger.debug("[DATABASE|REQUEST] Opened request-scoped connection.")
    else:
        logger.debug("[DATABASE|REQUEST] Reusing existing request connection.")
    return g.db_conn


def close_request_connection(_exception: Exception | None = None) -> None:
    """
    Close the request-scoped connection after request ends.

    :param _exception: Exception from Flask teardown (ignored).
    """
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()
        logger.debug("[DATABASE|REQUEST] Closed request connection.")


def get_connection_standalone() -> Connection:
    """
    Get a standalone SQLAlchemy connection.

    This connection is not tied to a Flask request context.

    :return: SQLAlchemy Connection object.
    """
    conn = db.engine.connect()
    logger.debug("[DATABASE|STANDALONE] Opened standalone connection.")
    return conn


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """
    Provide a context-managed standalone connection.

    Yields a connection object which should be closed after use.

    :yields: SQLAlchemy Connection object.
    """
    conn = db.engine.connect()
    logger.debug("[DATABASE|STANDALONE] Opened standalone connection.")
    try:
        yield conn
    finally:
        conn.close()
        logger.debug("[DATABASE|STANDALONE] Closed standalone connection.")


def ensure_db_exists() -> None:
    """
    Check if the PostgreSQL database is reachable.

    Executes 'SELECT 1' to verify connectivity.

    Logs info if reachable, warning if not.
    """
    try:
        with db.engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("[DATABASE|CHECK] Database connection successful.")
    except SQLAlchemyError as e:
        logger.warning("[DATABASE|CHECK] Database not reachable: %s", e)


def execute_and_commit(query: str, params: tuple) -> None:
    """
    Execute a parameterized query and commit the transaction.

    Rolls back and raises if execution fails.

    :param query: SQL query string.
    :param params: Query parameters as tuple.
    :raises SQLAlchemyError: If the query fails and cannot be committed.
    """
    # Convert tuple params to dict with positional keys for SQLAlchemy
    params_dict = None
    if params:
        params_dict = {f"param{i+1}": val for i, val in enumerate(params)}

    try:
        if params_dict:
            db.session.execute(query, params_dict)
        else:
            db.session.execute(query)
        db.session.commit()
        logger.debug("[DATABASE|EXECUTE] Query committed successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(
            "[DATABASE|ERROR] Failed to execute and commit query %s:", e
        )
        raise
