"""
Utility functions for the Arcanum application.

Provides reusable helpers and wrappers for:

- Database access:
  - Lazy connection handling.
  - Centralized error handling.

- SQL construction:
  - Sorting logic.
  - WHERE clause building.
  - Safe parameter substitution.

- Time and date parsing:
  - ISO/UTC formatting.
  - Local timezone conversion.
  - Date normalization and comparison.

- Message and filter processing:
  - Message grouping by chat.
  - Filter validation and normalization.
  - Query clause resolution.

- Logging setup:
  - Unified formatter and file handler.
  - Streamlined logger initialization.

- Data handling:
  - Model hydration from row dicts.
  - Slug generation and sanitization.

Used across DAO, services, routes, and templates to ensure consistent behavior
and reduce code duplication.
"""
