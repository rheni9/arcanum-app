"""
Sorting utilities for request query parameters.

This module provides functions to extract, normalize, and validate
sorting-related parameters (`sort` and `order`) from Flask request queries.
"""


import logging
from typing import Optional, Iterable, Tuple

logger = logging.getLogger(__name__)


def get_sort_order(
    sort_by: Optional[str],
    order: Optional[str],
    allowed_fields: Iterable[str],
    default_field: str,
    default_order: str = "desc"
) -> Tuple[str, str]:
    """
    Extract and validate sorting parameters from the request query string.

    :param sort_by: Field to sort by (e.g., 'timestamp', 'name')
    :type sort_by: Optional[str]
    :param order: Sort direction ('asc' or 'desc')
    :type order: Optional[str]
    :param allowed_fields: Set of valid fields for sorting
    :type allowed_fields: Iterable[str]
    :param default_field: Fallback field if sort_by is invalid
    :type default_field: str
    :param default_order: Fallback order if order is invalid
    :type default_order: str
    :return: Tuple (sort_by, order)
    :rtype: Tuple[str, str]
    """
    allowed_set = set(allowed_fields)

    if sort_by and sort_by not in allowed_set:
        logger.warning(
            "Invalid sort field '%s'; defaulting to '%s'",
            sort_by, default_field
        )
    elif not sort_by:
        pass
    sort_by = sort_by if sort_by in allowed_set else default_field

    if order:
        order = order.lower()
        if order not in {"asc", "desc"}:
            logger.warning(
                "Invalid sort order '%s'; defaulting to '%s'",
                order, default_order
            )
            order = default_order
    else:
        order = default_order

    return sort_by, order
