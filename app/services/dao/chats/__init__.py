"""
DAO facade for chat database access.

Selects the appropriate backend-specific DAO implementation
based on the DB_BACKEND environment variable.
"""

import os

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()

if DB_BACKEND == "sqlite":
    from .chats_dao_sqlite import SQLiteChatDAO as ChatDAO
elif DB_BACKEND == "postgres":
    from .chats_dao_postgres import PostgresChatDAO as ChatDAO
else:
    raise RuntimeError(
        f"Unsupported DB_BACKEND: {DB_BACKEND}. "
        "Use 'sqlite' or 'postgres'."
    )

__all__ = ["ChatDAO"]
