"""
Sorting utilities for the Arcanum application.

Provides normalization and validation of sort parameters for use
in SQL queries and request handling.
"""


import logging

logger = logging.getLogger(__name__)


def get_sort_order(
    sort_by: str | None,
    order: str | None,
    allowed_fields: set[str],
    default_field: str,
    default_order: str = "desc"
) -> tuple[str, str]:
    """
    Normalize and validate sorting parameters.

    Ensures that sort_by is allowed and order is 'asc' or 'desc'.
    Falls back to defaults if parameters are missing or invalid.

    :param sort_by: Requested field to sort by.
    :param order: Requested sort direction.
    :param allowed_fields: Allowed fields for sorting.
    :param default_field: Fallback field if sort_by is invalid or missing.
    :param default_order: Fallback direction if order is invalid or missing.
    :return: Tuple (validated sort_by, validated order).
    """
    allowed_set = set(allowed_fields)

    if sort_by and sort_by not in allowed_set:
        logger.warning(
            "[SORT|PARAMS] Invalid sort field '%s'; defaulted to '%s'.",
            sort_by, default_field
        )
        sort_by = default_field
    elif not sort_by:
        sort_by = default_field

    if order:
        order = order.lower()
        if order not in {"asc", "desc"}:
            logger.warning(
                "[SORT|PARAMS] Invalid sort order '%s'; defaulted to '%s'.",
                order, default_order
            )
            order = default_order
    else:
        order = default_order

    return sort_by, order
