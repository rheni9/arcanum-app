"""
Database utilities for the Arcanum application using PostgreSQL.

Provides SQLAlchemy connection helpers, request-scoped and standalone
connections, context-managed usage, database connectivity check,
and a unified execute-and-commit helper.
"""

import logging
import time
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import text
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
    Close the request-scoped SQLAlchemy connection after request ends.

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
    Provide a context-managed standalone SQLAlchemy connection.

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


def ensure_db_exists(retries: int = 5, delay: float = 2.0) -> None:
    """
    Check if the configured PostgreSQL database is reachable.

    Executes 'SELECT 1' to verify connectivity.
    Retries multiple times with delay if the database is not reachable.

    :param retries: Number of times to retry connection.
    :param delay: Delay in seconds between retries.
    :raises RuntimeError: If database is unreachable after all retries.
    """
    attempt = 0
    while attempt <= retries:
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1")).scalar()
            logger.info("[DATABASE|CHECK] Database connection successful.")
            return
        except SQLAlchemyError as e:
            attempt += 1
            logger.warning(
                "[DATABASE|CHECK] Database not reachable (attempt %d/%d): %s",
                attempt, retries, e
            )
            if attempt > retries:
                logger.error(
                    "[DATABASE|CHECK] Could not connect to database after %d "
                    "attempts.", retries
                )
                raise RuntimeError("Database is not available.") from e
            time.sleep(delay)


def execute_and_commit(query: str, params: dict | None = None) -> None:
    """
    Execute a parameterized query and commit the transaction.

    Rolls back and raises if execution fails.

    :param query: SQL query string.
    :param params: Query parameters (dictionary or None).
    :raises SQLAlchemyError: If the query fails and cannot be committed.
    """
    try:
        if params:
            db.session.execute(text(query), params)
        else:
            db.session.execute(text(query))
        db.session.commit()
        logger.debug(
            "[DATABASE|EXECUTE] Query committed successfully: %s",
            query
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(
            "[DATABASE|ERROR] Failed to execute and commit query %s:", e
        )
        raise
