"""
SQL utilities for safe and consistent query construction.

Provides:
- OrderConfig dataclass for configuring sort behavior.
- build_order_clause() for composing validated SQL ORDER BY clauses.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Set

from app.utils.sort_utils import normalize_sort_params

logger = logging.getLogger(__name__)


@dataclass
class OrderConfig:
    """
    Configuration for sorting logic used in SQL clause construction.

    :param allowed_fields: Set of allowed fields for sorting.
    :type allowed_fields: Set[str]
    :param default_field: Fallback field if sort_by is invalid.
    :type default_field: str
    :param default_order: Fallback direction if order is invalid.
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
    Construct a validated SQL ORDER BY clause.

    Normalizes sort_by and order parameters based on config,
    and returns a safe SQL ORDER BY clause string.

    :param sort_by: Requested sort field.
    :type sort_by: Optional[str]
    :param order: Requested sort direction ('asc' or 'desc').
    :type order: Optional[str]
    :param config: Sorting configuration object.
    :type config: OrderConfig
    :return: SQL ORDER BY clause (e.g., 'ORDER BY c.name asc').
    :rtype: str
    """
    sort_by, order = normalize_sort_params(
        sort_by, order, config.allowed_fields,
        config.default_field, config.default_order
    )

    field_ref = f"{config.prefix}{sort_by}" if config.prefix else sort_by

    logger.debug(
        "[SQL|ORDER] Final ORDER BY clause: ORDER BY %s %s",
        field_ref, order
    )

    return f"ORDER BY {field_ref} {order}"
