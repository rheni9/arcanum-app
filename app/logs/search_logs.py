"""
Centralized logging for search/filter operations in the Arcanum application.

Handles logging of global and per-chat search operations including
text queries, tag-based lookups, and message filtering by date.
Ensures consistent log formatting across routes.
"""

import logging

from app.models.filters import MessageFilters

logger = logging.getLogger(__name__)


def log_search_outcome(
    status: str,
    filters: MessageFilters,
    context: dict
) -> None:
    """
    Log the outcome of a resolved search or filter operation.

    :param status: Status of the query resolution.
    :param filters: MessageFilters object containing search parameters.
    :param context: Dictionary with result metadata.
    """
    if status == "cleared":
        logger.info(
            "[SEARCH|ROUTER] Filters cleared — no operation performed."
        )
    elif status == "invalid":
        logger.warning(
            "[SEARCH|ROUTER] Invalid filter input — no search performed."
        )
    elif status == "error":
        logger.error(
            "[SEARCH|ROUTER] Query failed: %s", context.get("info_message")
        )
    elif status == "valid":
        scope = (
            f"Chat '{filters.chat_slug}', " if filters.chat_slug else "Global "
        )
        logger.info(
            "[SEARCH|ROUTER] %ssearch: %d message(s), filters: %s",
            scope, context["count"], filters.to_dict()
        )
