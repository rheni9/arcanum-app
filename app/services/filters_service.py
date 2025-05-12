"""
Service module for resolving message search and filter actions in Arcanum.

Provides logic to:
- validate and normalize input filter data,
- route to full-text search or date-based filtering,
- operate globally or within a specific chat.

Depends on the MessageFilters model and delegates execution to
the message service layer.
"""

import logging
from typing import Optional, List, Tuple
from app.models.filters import MessageFilters
from app.services.messages_service import (
    search_messages_by_text,
    filter_messages,
)
from app.utils.filters_utils import validate_search_filters

logger = logging.getLogger(__name__)


def resolve_search_action(
    filters: MessageFilters,
    sort_by: str,
    order: str,
    chat_slug: Optional[str] = None
) -> Tuple[List[dict], Optional[str], MessageFilters]:
    """
    Resolve and dispatch a message query or filter operation.

    Validates user-supplied filter parameters and performs either full-text
    search or date-based filtering. Returns matched messages along with
    an optional info message for user feedback.

    :param filters: MessageFilters object with search or filter input.
    :type filters: MessageFilters
    :param sort_by: Field to sort messages by ('timestamp' or 'msg_id').
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str
    :param chat_slug: Optional slug to limit search to a single chat.
    :type chat_slug: Optional[str]
    :returns: Tuple containing:
             - list of matched messages (list[dict]),
             - optional user info message (str or None),
             - normalized filters object (MessageFilters).
    :rtype: tuple[list[dict], Optional[str], MessageFilters]
    """

    # Normalize inputs (e.g. blank → None, strip)
    filters.normalize()

    is_valid, info_message = validate_search_filters(
        action=filters.action,
        query=filters.query,
        mode=filters.date_mode,
        start=filters.start_date,
        end=filters.end_date,
    )

    if not is_valid:
        if filters.is_empty():
            logger.info("[FORM] No filters or search query applied.")
            info_message = "No filters or search query applied."
            return [], info_message, filters
        logger.warning(
            "[FILTER] Invalid filters: action=%s, query=%s, mode=%s",
            filters.action, filters.query, filters.date_mode
        )
        return [], info_message, filters

    if filters.action == "search" and filters.query:
        logger.debug("[SEARCH] Performing search: query='%s' in chat='%s'",
                     filters.query, chat_slug or "<all>")
        return (
            search_messages_by_text(
                filters=filters,
                sort_by=sort_by,
                order=order,
                chat_slug=chat_slug
            ),
            None,
            filters
        )

    if filters.action == "filter" and filters.start_date:
        logger.debug(
            "[FILTER] Performing filter: mode=%s, start=%s, end=%s "
            "in chat='%s'",
            filters.date_mode,
            filters.start_date,
            filters.end_date,
            chat_slug or "<all>"
        )
        return (
            filter_messages(
                filters=filters,
                sort_by=sort_by,
                order=order,
                chat_slug=chat_slug
            ),
            None,
            filters
        )

    logger.info("[FILTER] No valid action or parameters provided.")
    return [], info_message, filters
