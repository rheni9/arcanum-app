"""
Message filter models for the Arcanum application.

Defines a base filter class and a message filter class for searching
and filtering messages. Provides normalization, validation, and SQL
clause helpers with full PEP257-style documentation and unified style.
"""

import logging
from dataclasses import dataclass, asdict
from flask import Request

logger = logging.getLogger(__name__)


@dataclass
class MessageFilters():
    """
    Filter and search parameters for message entities.

    Supports global and local (per chat) queries, including text
    search and date range filtering.

    :param action: Optional filter action: 'search' (by text/tags)
                   or 'filter' (by date).
    :param query: Search text for message content.
    :param tag: Search text for message tags.
    :param date_mode: Date filter mode: 'on', 'before', 'after', or 'between'.
    :param start_date: Start date (YYYY-MM-DD).
    :param end_date: End date (YYYY-MM-DD, used for 'between').
    :param chat_slug: Restrict filter to this chat if set.
    """
    action: str | None = None  # "search", "filter"
    query: str | None = None
    tag: str | None = None
    date_mode: str | None = None  # "on", "before", "after", "between"
    start_date: str | None = None
    end_date: str | None = None
    chat_slug: str | None = None

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the filter fields.

        :return: Dictionary of filter fields.
        """
        return asdict(self)

    def normalize(self) -> None:
        """
        Normalize and sanitize filter fields in place.
        """
        if self.query is not None:
            self.query = self.query.strip() or None
        if self.tag is not None:
            self.tag = self.tag.strip() or None
        if self.date_mode:
            self.date_mode = self.date_mode.strip() or None
        if self.start_date is not None:
            self.start_date = self.start_date.strip() or None
        if self.end_date is not None:
            self.end_date = self.end_date.strip() or None
        if self.chat_slug is not None:
            self.chat_slug = self.chat_slug.strip() or None

    def is_valid(self) -> bool:
        """
        Validate minimal filter structure for action-specific logic.

        Determines if the filter contains the minimal required fields
        to perform either a text search or a date-based filter.

        Note: For full validation, use `validate_search_filters()`
        from the utilities module.

        :return: True if the filter is structurally valid for its action.
        """
        if self.action == "search" and (self.query or self.tag):
            return True
        if self.action == "filter":
            if self.date_mode in {"on", "before", "after"} and self.start_date:
                return True
            if (
                self.date_mode == "between"
                and self.start_date
                and self.end_date
            ):
                return True
        return False

    @classmethod
    def from_request(cls, req: Request) -> "MessageFilters":
        """
        Create a MessageFilters instance from a Flask request.

        :param req: Flask request object.
        :return: MessageFilters instance populated from request args.
        """
        filters = cls(
            action=req.args.get("action"),
            query=req.args.get("query"),
            tag=req.args.get("tag"),
            date_mode=req.args.get("date_mode"),
            start_date=req.args.get("start_date"),
            end_date=req.args.get("end_date"),
            chat_slug=(
                req.args.get("chat_slug")
                or req.args.get("chat")
                or req.view_args.get("slug")
            ),
        )
        filters.normalize()
        if filters.has_active():
            logger.debug(
                "[FILTERS|REQUEST] Created filters from request: %s", filters
            )
        else:
            logger.debug("[FILTERS|REQUEST] No filters provided in request.")
        return filters

    def is_tag_search(self) -> bool:
        """
        Determine whether the filter is a tag-only search.

        :return: True if searching by tag only.
        """
        return bool(self.tag)

    def has_active(self) -> bool:
        """
        Check if any filter field is set.

        :return: True if any filter is active.
        """
        return any([self.query, self.tag, self.start_date, self.end_date])

    def is_empty(self) -> bool:
        """
        Check if all filter fields are empty.

        :return: True if no filters are set.
        """
        return not self.has_active()

    def is_global(self) -> bool:
        """
        Check if the filter is global (not restricted to a chat).

        :return: True if global filter.
        """
        return not self.chat_slug

    def is_local(self) -> bool:
        """
        Check if the filter is local (restricted to a specific chat).

        :return: True if local filter.
        """
        return bool(self.chat_slug)

    def get_date_clause(self) -> str:
        """
        Return the SQL clause for the current date filter.

        Constructs a SQL WHERE clause for date filtering based on the
        current `date_mode` and date values.
        Returns an empty string if filtering is not applicable.

        :return: SQL WHERE clause snippet for date filtering.
        """
        if self.date_mode == "on" and self.start_date:
            return "DATE(m.timestamp) = DATE(?)"
        if self.date_mode == "before" and self.start_date:
            return "DATE(m.timestamp) < DATE(?)"
        if self.date_mode == "after" and self.start_date:
            return "DATE(m.timestamp) >= DATE(?)"
        if self.date_mode == "between" and self.start_date and self.end_date:
            return "DATE(m.timestamp) BETWEEN DATE(?) AND DATE(?)"
        return ""

    def get_date_params(self) -> list[str]:
        """
        Return the SQL parameter values for the current date filter.

        :return: List of date parameters for the SQL query.
        """
        if self.date_mode in {"on", "before", "after"} and self.start_date:
            return [self.start_date]
        if (
            self.date_mode == "between"
            and self.start_date
            and self.end_date
        ):
            return [self.start_date, self.end_date]
        return []

    def to_query_args(self) -> dict:
        """Return dict of filters for query string, skipping empty values."""
        args = {}
        if self.query:
            args["query"] = self.query
        if self.tag:
            args["tag"] = self.tag
        if self.action:
            args["action"] = self.action
        if self.date_mode:
            args["date_mode"] = self.date_mode
        if self.start_date:
            args["start_date"] = self.start_date
        if self.end_date:
            args["end_date"] = self.end_date
        return args
