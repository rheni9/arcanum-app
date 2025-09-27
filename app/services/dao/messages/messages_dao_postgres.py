"""
PostgreSQL Data Access Object (DAO) for message operations
in the Arcanum application.

Implements BaseMessageDAO using SQLAlchemy Core, provides connection
handling, query execution and translation of integrity errors into
domain-specific exceptions.
"""
# pylint: disable=no-member

import logging

from psycopg2 import errors
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.message import Message
from app.utils.db_utils import get_connection_lazy
from app.errors import DuplicateMessageError
from .messages_dao_base import BaseMessageDAO

logger = logging.getLogger(__name__)


class PostgresMessageDAO(BaseMessageDAO):
    """
    PostgreSQL Data Access Object for message operations.

    Uses SQLAlchemy Core for execution and commits per statement.
    """

    # ---------- Backend typing / error classes ----------

    @property
    def db_error_class(self) -> type[Exception]:
        """PostgreSQL base database error class."""
        return SQLAlchemyError

    @property
    def integrity_error_class(self) -> type[Exception]:
        """PostgreSQL integrity error class."""
        return IntegrityError

    # ---------- Execution primitives ----------

    def _select_all(
        self,
        query: str,
        params: dict | None = None,
    ) -> list[dict]:
        """Execute a SELECT and return all rows."""
        conn = get_connection_lazy()
        try:
            result = conn.execute(text(query), params or {})
            rows = result.mappings().all()
            data = [dict(r) for r in rows]
            logger.debug(
                "[PG|MESSAGES|DAO] _select_all -> %d row(s).",
                len(data),
            )
            return data
        except SQLAlchemyError as exc:
            logger.error("[PG|MESSAGES|DAO] _select_all failed: %s", exc)
            raise

    def _select_one(
        self,
        query: str,
        params: dict | None = None,
    ) -> dict | None:
        """Execute a SELECT and return a single row."""
        conn = get_connection_lazy()
        try:
            result = conn.execute(text(query), params or {})
            row = result.mappings().fetchone()
            data = dict(row) if row else None
            logger.debug(
                "[PG|MESSAGES|DAO] _select_one -> %s",
                "hit" if data else "none",
            )
            return data
        except SQLAlchemyError as exc:
            logger.error("[PG|MESSAGES|DAO] _select_one failed: %s", exc)
            raise

    def _execute_dml(
        self,
        query: str,
        params: dict | None = None,
    ) -> int:
        """Execute INSERT/UPDATE/DELETE and commit."""
        conn = get_connection_lazy()
        try:
            result = conn.execute(text(query), params or {})
            conn.commit()
            logger.debug(
                "[PG|MESSAGES|DAO] _execute_dml committed. rowcount=%s",
                result.rowcount,
            )
            return int(result.rowcount or 0)
        except IntegrityError as exc:
            logger.debug(
                "[PG|MESSAGES|DAO] Integrity error in _execute_dml: %s",
                exc,
            )
            raise
        except SQLAlchemyError as exc:
            logger.error("[PG|MESSAGES|DAO] _execute_dml failed: %s", exc)
            raise

    def _execute_insert(
        self,
        query: str,
        params: dict,
    ) -> tuple[object, object | None]:
        """
        Execute INSERT and return the SQLAlchemy result.

        Appends ``RETURNING id`` to capture the primary key.
        """
        conn = get_connection_lazy()
        stmt = query.rstrip()
        if stmt.endswith(";"):
            stmt = stmt[:-1]
        returning_sql = f"{stmt} RETURNING id;"

        try:
            result = conn.execute(text(returning_sql), params or {})
            conn.commit()
            logger.debug("[PG|MESSAGES|DAO] _execute_insert committed.")
            return result, None
        except IntegrityError as exc:
            logger.debug(
                "[PG|MESSAGES|DAO] Integrity error in _execute_insert: %s",
                exc,
            )
            raise
        except SQLAlchemyError as exc:
            logger.error("[PG|MESSAGES|DAO] _execute_insert failed: %s", exc)
            raise

    def get_last_inserted_id(
        self,
        result: object,
        cursor: object | None = None,
    ) -> int | None:
        """
        Extract primary key from PostgreSQL INSERT result.

        :param result: SQLAlchemy Result.
        :param cursor: Unused for PostgreSQL.
        :return: Inserted primary key or ``None``.
        """
        row = result.mappings().fetchone()
        return int(row.get("id")) if row else None

    def handle_integrity_error(
        self,
        exc: IntegrityError,
        msg: Message,
    ) -> None:
        """
        Map IntegrityError to domain-specific exceptions.

        :param exc: SQLAlchemy IntegrityError.
        :param msg: Message instance involved in the operation.
        :raises DuplicateMessageError: If unique on (chat_ref_id, msg_id)
                                       is violated.
        """
        orig = getattr(exc, "orig", None)
        if orig and isinstance(orig, errors.UniqueViolation):
            constraint = getattr(orig.diag, "constraint_name", "") or ""
            if constraint == "idx_unique_msg_id":
                raise DuplicateMessageError(
                    chat_ref_id=msg.chat_ref_id,
                    msg_id=msg.msg_id,
                ) from exc
        raise exc
