"""
SQL utilities for safe and consistent query construction.

Provides reusable helpers for composing SQL clauses such as ORDER BY
with input validation to prevent injection and ensure consistency across
database operations.
"""

from dataclasses import dataclass
from typing import Optional, Set


@dataclass
class OrderConfig:
    """
    Configuration for sorting logic used in SQL clause construction.

    :param allowed_fields: Set of allowed fields for sorting.
    :type allowed_fields: Set[str]
    :param default_field: Field to sort by if sort_by is invalid.
    :type default_field: str
    :param default_order: Direction to sort if order is invalid.
    :type default_order: str
    :param prefix: Optional table alias or prefix (e.g., 'c.' or 'm.').
    :type prefix: Optional[str]
    """
    allowed_fields: Set[str]
    default_field: str = "timestamp"
    default_order: str = "desc"
    prefix: Optional[str] = None


def build_order_clause(
    sort_by: Optional[str],
    order: Optional[str],
    config: OrderConfig
) -> str:
    """
    Construct a validated SQL ORDER BY clause from config parameters.

    :param sort_by: Requested sort field.
    :type sort_by: Optional[str]
    :param order: Requested sort direction ('asc' or 'desc').
    :type order: Optional[str]
    :param config: Order configuration.
    :type config: OrderConfig
    :return: SQL ORDER BY clause string.
    :rtype: str
    """
    field = sort_by if sort_by in config.allowed_fields \
        else config.default_field
    direction = order.lower() \
        if order and order.lower() in {"asc", "desc"} \
        else config.default_order
    field_ref = f"{config.prefix}{field}" if config.prefix else field
    return f"ORDER BY {field_ref} {direction}"
