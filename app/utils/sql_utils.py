"""
SQL utilities for the Arcanum application.

Provides safe ORDER BY clause generation using validated parameters
and sorting configuration objects.
"""

import logging
from dataclasses import dataclass

from app.utils.sort_utils import get_sort_order

logger = logging.getLogger(__name__)


@dataclass
class OrderConfig:
    """
    Configuration for sorting logic used in SQL clause construction.

    :param allowed_fields: Allowed fields for sorting.
    :param default_field: Fallback field if sort_by is invalid or missing.
    :param default_order: Fallback direction if order is invalid or missing.
    :param prefix: Optional prefix or table alias (e.g., 'm.').
    """
    allowed_fields: set[str]
    default_field: str = "timestamp"
    default_order: str = "desc"
    prefix: str | None = None


def build_order_clause(
    sort_by: str | None,
    order: str | None,
    config: OrderConfig
) -> str:
    """
    Construct a safe SQL ORDER BY clause from validated inputs.

    :param sort_by: Requested field to sort by.
    :param order: Requested sort direction.
    :param config: Sorting configuration.
    :return: SQL ORDER BY clause string.
    """
    sort_by, order = get_sort_order(
        sort_by, order,
        config.allowed_fields,
        config.default_field,
        config.default_order
    )

    field_ref = f"{config.prefix}{sort_by}" if config.prefix else sort_by

    logger.debug(
        "[SQL|ORDER] Final ORDER BY clause: ORDER BY %s %s",
        field_ref, order
    )

    nulls = "NULLS LAST" if sort_by == "last_message" else ""

    return f"{field_ref} {order} {nulls}".strip()
