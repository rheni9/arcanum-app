"""
Database utilities facade for the Arcanum application.

Exposes a unified API for database helpers (connections, checks,
execute-and-commit) by re-exporting the backend-specific implementation.

The backend is selected based on the DB_BACKEND environment variable:
- "sqlite": uses app.utils.db_utils.db_utils_sqlite
- "postgres": uses app.utils.db_utils.db_utils_postgres
"""

import os
import logging

logger = logging.getLogger(__name__)

# Detect backend from environment
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()

if DB_BACKEND == "sqlite":
    logger.debug("[DB_UTILS] Selected SQLite backend.")
    from app.utils.db_utils.db_utils_sqlite import (  # re-export
        get_connection_lazy,
        close_request_connection,
        get_connection_standalone,
        get_connection,
        ensure_db_exists,
        execute_and_commit,
    )

elif DB_BACKEND == "postgres":
    logger.debug("[DB_UTILS] Selected PostgreSQL backend.")
    from app.utils.db_utils.db_utils_postgres import (  # re-export
        get_connection_lazy,
        close_request_connection,
        get_connection_standalone,
        get_connection,
        ensure_db_exists,
        execute_and_commit,
    )

else:
    raise RuntimeError(
        f"Unsupported DB_BACKEND: {DB_BACKEND}. "
        "Use 'sqlite' or 'postgres'."
    )

__all__ = [
    "get_connection_lazy",
    "close_request_connection",
    "get_connection_standalone",
    "get_connection",
    "ensure_db_exists",
    "execute_and_commit",
]
