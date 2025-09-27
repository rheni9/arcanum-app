"""
DAO facade for filter database access.

Selects the appropriate backend-specific DAO implementation
based on the DB_BACKEND environment variable.
"""

import os

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()

if DB_BACKEND == "sqlite":
    from .filters_dao_sqlite import SQLiteFiltersDAO as FiltersDAO
elif DB_BACKEND == "postgres":
    from .filters_dao_postgres import PostgresFiltersDAO as FiltersDAO
else:
    raise RuntimeError(
        f"Unsupported DB_BACKEND: {DB_BACKEND}. "
        "Use 'sqlite' or 'postgres'."
    )

__all__ = ["FiltersDAO"]
