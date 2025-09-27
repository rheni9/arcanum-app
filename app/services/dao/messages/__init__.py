"""
DAO facade for message database access.

Selects the appropriate backend-specific DAO implementation
based on the DB_BACKEND environment variable.
"""

import os

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()

if DB_BACKEND == "sqlite":
    from .messages_dao_sqlite import SQLiteMessageDAO as MessageDAO
elif DB_BACKEND == "postgres":
    from .messages_dao_postgres import PostgresMessageDAO as MessageDAO
else:
    raise RuntimeError(
        f"Unsupported DB_BACKEND: {DB_BACKEND}. "
        "Use 'sqlite' or 'postgres'."
    )

__all__ = ["MessageDAO"]
