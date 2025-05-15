"""
Sorting utilities for request query parameters.

Provides:
- normalize_sort_params() for validating and normalizing sort parameters.
- get_sort_order() as a wrapper for request-level usage with logging.
"""


import logging
from typing import Optional, Iterable, Tuple

logger = logging.getLogger(__name__)


def normalize_sort_params(
    sort_by: Optional[str],
    order: Optional[str],
    allowed_fields: Iterable[str],
    default_field: str,
    default_order: str = "desc"
) -> Tuple[str, str]:
    """
    Validate and normalize sorting parameters.

    Ensures that sort_by is among allowed_fields and order is 'asc'/'desc'.
    Falls back to defaults if invalid or missing. Used for SQL and API sorting.

    :param sort_by: Requested field to sort by (e.g., 'timestamp').
    :type sort_by: Optional[str]
    :param order: Requested sort direction ('asc' or 'desc').
    :type order: Optional[str]
    :param allowed_fields: Iterable of valid sortable fields.
    :type allowed_fields: Iterable[str]
    :param default_field: Fallback field if sort_by is invalid or missing.
    :type default_field: str
    :param default_order: Fallback direction if order is invalid or missing.
    :type default_order: str
    :return: Tuple of (validated sort_by, validated order).
    :rtype: Tuple[str, str]
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


def get_sort_order(
    sort_by: Optional[str],
    order: Optional[str],
    allowed_fields: Iterable[str],
    default_field: str,
    default_order: str = "desc"
) -> Tuple[str, str]:
    """
    Retrieve validated sort parameters for request-level usage.

    Wrapper around normalize_sort_params with additional logging.

    :param sort_by: Requested field to sort by (from request query).
    :type sort_by: Optional[str]
    :param order: Requested sort direction (from request query).
    :type order: Optional[str]
    :param allowed_fields: Iterable of valid sortable fields.
    :type allowed_fields: Iterable[str]
    :param default_field: Fallback field if sort_by is invalid or missing.
    :type default_field: str
    :param default_order: Fallback direction if order is invalid or missing.
    :type default_order: str
    :return: Tuple of (validated sort_by, validated order).
    :rtype: Tuple[str, str]
    """
    sort_by, order = normalize_sort_params(
        sort_by, order, allowed_fields, default_field, default_order
    )

    logger.debug(
        "[SORT|PARAMS] Using sort_by='%s', order='%s'.", sort_by, order
    )
    return sort_by, order
