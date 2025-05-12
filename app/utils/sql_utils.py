"""
SQL utilities for safe and consistent query construction.

Provides reusable helpers for composing SQL clauses such as ORDER BY
with input validation to prevent injection and ensure consistency across
database operations.
The module also logs corrections of invalid sort parameters and
constructed ORDER BY clauses.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Set

logger = logging.getLogger(__name__)


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

    # Validate sort_by field
    if sort_by in config.allowed_fields:
        field = sort_by
    else:
        logger.warning(
            "[SQL] Invalid sort field '%s'; defaulted to '%s'.",
            sort_by, config.default_field
        )
        field = config.default_field

    # Validate sort direction
    if order and order.lower() in {"asc", "desc"}:
        direction = order.lower()
    else:
        if order:
            logger.warning(
                "[SQL] Invalid sort order '%s'; defaulted to '%s'.",
                order, config.default_order
            )
        direction = config.default_order

    # Compose field reference with prefix if any
    field_ref = f"{config.prefix}{field}" if config.prefix else field

    # Log final ORDER BY clause
    logger.debug(
        "[SQL] ORDER BY clause constructed: ORDER BY %s %s",
        field_ref, direction
    )

    return f"ORDER BY {field_ref} {direction}"
