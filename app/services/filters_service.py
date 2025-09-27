"""
Message filter and search service operations for the Arcanum application.

Provides business logic for searching and filtering messages:
- Normalizing and validating filters (search, tag, date).
- Retrieving filtered messages with ordering.
- Grouping results by chat.
- Returning structured result objects with status and user message.

This class is backend-agnostic. The actual DAO implementation
(PostgreSQL or SQLite) is selected via the FiltersDAO facade.
"""

import logging

from app.models.filters import MessageFilters
from app.services.dao.filters.filters_dao_base import BaseFiltersDAO
from app.utils.i18n_utils import TranslatableMsg
from app.utils.filters_utils import (
    normalize_filter_action,
    validate_search_filters,
)
from app.utils.messages_utils import group_messages_by_chat

logger = logging.getLogger(__name__)


class FilterService:
    """
    Service layer for message filtering operations.

    Encapsulates filter validation, query orchestration,
    and result structuring, delegating persistence to the DAO.
    """

    def __init__(self, dao: BaseFiltersDAO) -> None:
        """
        Initialize the service with a given DAO.

        :param dao: Concrete filter DAO (Postgres or SQLite).
        """
        self.dao = dao

    # ---------- Public API ----------

    def resolve_message_query(
        self,
        filters: MessageFilters,
        sort_by: str,
        order: str,
    ) -> tuple[str, dict]:
        """
        Retrieve messages based on normalized filters.

        Executes global or chat-local query and groups results by chat.
        Returns structured output including status and user message.

        :param filters: Validated message filters.
        :param sort_by: Field to sort by (``msg_id`` or ``timestamp``).
        :param order: Sort direction (``'asc'`` or ``'desc'``).
        :return: Result tuple with status and metadata.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        status, msg = self._preprocess_filters(filters)

        if status == "cleared":
            logger.info(
                "[FILTERS|SERVICE] No filters to apply — skipping execution."
            )
            return self._result_cleared(filters)

        if status == "invalid":
            logger.warning("[FILTERS|SERVICE] Invalid filters.")
            return self._result_invalid(filters, msg)

        try:
            messages = self.dao.fetch_filtered_messages(
                filters, sort_by, order
            )
            count = len(messages)
            grouped = group_messages_by_chat(messages)

            logger.info(
                "[FILTERS|SERVICE] Retrieved %d message(s) | scope=%s",
                count,
                "global" if filters.is_global() else filters.chat_slug,
            )
            return self._result_valid(filters, messages, grouped, count)

        except self.dao.db_error_class as exc:
            logger.error("[FILTERS|SERVICE] Query failed: %s", exc)
            return self._result_error(filters, exc)

    # ---------- Filter preprocessing ----------

    def _preprocess_filters(
        self, filters: MessageFilters
    ) -> tuple[str, str | None]:
        """
        Normalize and validate message filters.

        Distinguishes between 'search', 'tag', and 'filter' modes.
        Returns a status and optional localized message.

        :param filters: Filter parameters to process.
        :return: Tuple of validation status and message (if any).
        """
        normalize_filter_action(filters)
        status, msg = self._route_validation(filters)

        logger.debug(
            "[FILTERS|PRE] status=%s | chat=%s | has_active=%s | action=%s "
            "| query=%r | tag=%r | mode=%r | start=%r | end=%r",
            status,
            filters.chat_slug or "<all>",
            filters.has_active(),
            filters.action,
            filters.query,
            filters.tag,
            filters.date_mode,
            filters.start_date,
            filters.end_date,
        )

        return status, msg

    def _route_validation(
        self, filters: MessageFilters
    ) -> tuple[str, str | None]:
        """Route filters to the appropriate validation logic."""
        if filters.action == "search":
            return self._validate_search_query(filters)
        if filters.action == "tag":
            return self._validate_tag_search(filters)
        if filters.action == "filter":
            return self._validate_date_filter(filters)
        if not filters.has_active() and not filters.action:
            return "cleared", None

        valid, msg = validate_search_filters(filters)
        return ("valid", None) if valid else ("invalid", msg)

    def _validate_search_query(
        self, filters: MessageFilters
    ) -> tuple[str, str | None]:
        """Validate text search or convert '#tag' queries into tag search."""
        if filters.query and filters.query.strip().startswith("#"):
            filters.tag = filters.query.strip().lstrip("#")
            filters.query = None
            filters.action = "tag"
            return self._validate_tag_search(filters)

        valid, msg = validate_search_filters(filters)
        return ("valid", None) if valid else ("invalid", msg)

    def _validate_tag_search(
        self, filters: MessageFilters
    ) -> tuple[str, str | None]:
        """Validate tag-based search."""
        valid, msg = validate_search_filters(filters)
        return ("valid", None) if valid else ("invalid", msg)

    def _validate_date_filter(
        self, filters: MessageFilters
    ) -> tuple[str, str | None]:
        """Validate date-based filter."""
        valid, msg = validate_search_filters(filters)
        return ("valid", None) if valid else ("invalid", msg)

    # ---------- Result helpers ----------

    def _result_valid(
        self,
        filters: MessageFilters,
        messages: list[dict],
        grouped: dict,
        count: int,
    ) -> tuple[str, dict]:
        """Return the result of a successful message query."""
        return "valid", {
            "messages": messages,
            "count": count,
            "grouped": grouped,
            "info_message": None,
            "filters": filters,
            "cleared": False,
        }

    def _result_invalid(
        self,
        filters: MessageFilters,
        msg: str,
    ) -> tuple[str, dict]:
        """Return an empty result for invalid filters."""
        return "invalid", {
            "messages": [],
            "count": 0,
            "grouped": {},
            "info_message": msg,
            "filters": filters,
            "cleared": False,
        }

    def _result_cleared(
        self,
        filters: MessageFilters,
    ) -> tuple[str, dict]:
        """Return an empty result when no filters are applied."""
        msg = TranslatableMsg(
            "Use the search bar or date filters above to find messages."
        ).ui
        return "cleared", {
            "messages": [],
            "count": 0,
            "grouped": {},
            "info_message": msg,
            "filters": filters,
            "cleared": True,
        }

    def _result_error(
        self,
        filters: MessageFilters,
        error: Exception,
    ) -> tuple[str, dict]:
        """Return an error result when the DAO query fails."""
        msg = TranslatableMsg(
            "Database error: %(err)s", {"err": str(error)}
        ).ui
        return "error", {
            "messages": [],
            "count": 0,
            "grouped": {},
            "info_message": msg,
            "filters": filters,
            "cleared": False,
        }
