"""
Message filter models for the Arcanum application.

Defines the message filtering data class with support for normalization,
validation, and generation of filter arguments for SQL and request contexts.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Literal
from flask import Request

from app.utils.time_utils import DEFAULT_TZ, get_utc_day_bounds

logger = logging.getLogger(__name__)


@dataclass
class MessageFilters():
    """
    Filter and search parameters for message entities.

    Supports global and local queries using full-text, tag-based,
    and date-based filtering options for messages.

    :param action: 'search' or 'filter' to define behavior.
    :param query: Full-text search string.
    :param tag: Tag-only search string.
    :param date_mode: Date filter mode: 'on', 'before', 'after', or 'between'.
    :param start_date: Start date (YYYY-MM-DD format).
    :param end_date: End date (only used in 'between' mode).
    :param chat_slug: Optional chat slug for chat-local filtering.
    """
    action: Literal["search", "filter"] | None = None
    query: str | None = None
    tag: str | None = None
    date_mode: Literal["on", "before", "after", "between"] | None = None
    start_date: str | None = None
    end_date: str | None = None
    chat_slug: str | None = None

    def normalize(self) -> None:
        """
        Normalize and sanitize filter fields in place.

        Strips whitespace from all string fields and replaces
        empty values with None for consistent processing.
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

    def to_dict(self) -> dict:
        """
        Convert all filter parameters to a dictionary.

        :return: Dictionary with filter fields.
        """
        return asdict(self)

    def to_query_args(self) -> dict:
        """
        Convert the filter to a dictionary of URL query arguments.

        :return: Dictionary of query arguments.
        """
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
        if self.chat_slug:
            args["chat_slug"] = self.chat_slug
        return args

    def is_valid(self) -> bool:
        """
        Check if the filter has a valid combination of fields.

        Text search requires query or tag.
        Date filter requires valid mode and date(s).

        :return: True if filter configuration is valid.
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

    def has_active(self) -> bool:
        """
        Check whether any filter fields are populated.

        :return: True if any filter condition is set.
        """
        return any([
            self.query,
            self.tag,
            self.date_mode,
            self.start_date,
            self.end_date,
        ])

    def is_empty(self) -> bool:
        """
        Check if the filter has no active fields set.

        :return: True if the filter is empty.
        """
        return not self.has_active()

    def is_tag_search(self) -> bool:
        """
        Check whether this is a tag-based search.

        :return: True if a tag is specified.
        """
        return bool(self.tag)

    def is_global(self) -> bool:
        """
        Check whether the filter is global (not chat-specific).

        :return: True if chat_slug is not set.
        """
        return not self.chat_slug

    def is_local(self) -> bool:
        """
        Check whether the filter is local (chat-specific).

        :return: True if chat slug is set.
        """
        return bool(self.chat_slug)

    def get_date_clause(self) -> str:
        """
        Generate SQL WHERE clause for the active date filter.

        :return: SQL clause fragment or empty string.
        """
        if self.date_mode == "on":
            return "m.timestamp >= :start_utc AND m.timestamp <= :end_utc"
        if self.date_mode == "before":
            return "m.timestamp < :start_utc"
        if self.date_mode == "after":
            return "m.timestamp >= :start_utc"
        if self.date_mode == "between":
            return "m.timestamp >= :start_utc AND m.timestamp <= :end_utc"
        return ""

    def get_date_params(self) -> list[str]:
        """
        Return parameters corresponding to the active date clause.

        :return: List of date strings or an empty list.
        """
        tz = DEFAULT_TZ

        if self.date_mode in {"on", "before", "after"} and self.start_date:
            start_utc, end_utc = get_utc_day_bounds(self.start_date, tz)
            if self.date_mode == "on":
                return {"start_utc": start_utc, "end_utc": end_utc}
            elif self.date_mode == "before":
                # before start of local day in UTC
                return {"start_utc": start_utc}
            elif self.date_mode == "after":
                # after or equal start of local day in UTC
                return {"start_utc": start_utc}
        if (
            self.date_mode == "between"
            and self.start_date
            and self.end_date
        ):
            start_utc_start, _ = get_utc_day_bounds(self.start_date, tz)
            _, end_utc_end = get_utc_day_bounds(self.end_date, tz)
            return {"start_utc": start_utc_start, "end_utc": end_utc_end}
        return {}

    @classmethod
    def from_request(cls, req: Request) -> "MessageFilters":
        """
        Create a MessageFilters instance from request parameters.

        :param req: Flask request object.
        :return: Populated MessageFilters instance.
        """
        chat_slug = (
            req.args.get("chat_slug")
            or req.args.get("chat")
            or (req.view_args.get("slug") if req.view_args else None)
        )

        filters = cls(
            action=req.args.get("action"),
            query=req.args.get("query"),
            tag=req.args.get("tag"),
            date_mode=req.args.get("date_mode"),
            start_date=req.args.get("start_date"),
            end_date=req.args.get("end_date"),
            chat_slug=chat_slug,
        )
        filters.normalize()

        if filters.has_active():
            logger.debug(
                "[FILTERS|REQUEST] Parsed filters from request: %s", filters
            )
        else:
            logger.debug("[FILTERS|REQUEST] No filters provided in request.")

        return filters

    def __repr__(self) -> str:
        """
        Compact debug representation of message filters.

        :return: Summary string.
        """
        return (
            f"<MessageFilters action='{self.action}' query='{self.query}' "
            f"tag='{self.tag}' date_mode='{self.date_mode}' "
            f"start_date='{self.start_date}' end_date='{self.end_date}' "
            f"chat_slug='{self.chat_slug}'>"
        )
