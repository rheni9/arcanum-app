"""
Reusable data model for message filtering in the Arcanum application.

Encapsulates user-defined parameters for full-text search and
date-based filtering, supporting all message-related views and routes.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MessageFilters:
    """
    Represents user-defined filters for searching and filtering messages.

    Supports both full-text queries and date-based filters, such as filtering
    messages on a specific date, before/after a date, or between two dates.

    :param action: Type of filtering action ('search' or 'filter').
    :type action: Optional[str]
    :param query: Full-text search query string.
    :type query: Optional[str]
    :param date_mode: Filtering mode: 'on', 'before', 'after', or 'between'.
    :type date_mode: Optional[str]
    :param start_date: Start date in 'YYYY-MM-DD' format.
    :type start_date: Optional[str]
    :param end_date: End date in 'YYYY-MM-DD' format (for 'between' mode).
    :type end_date: Optional[str]
    """
    action: Optional[str] = None
    query: Optional[str] = None
    date_mode: str = "on"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def normalize(self) -> None:
        """
        Normalize all filter values for consistent processing.

        Strips whitespace from all string fields and converts empty strings
        to None. Ensures compatibility with validation and filtering logic.
        """
        self.query = self.query.strip() or None if self.query else None
        self.date_mode = self.date_mode or "on"
        self.start_date = (
            self.start_date.strip() or None if self.start_date else None
        )
        self.end_date = (
            self.end_date.strip() or None if self.end_date else None
        )

    def has_active(self) -> bool:
        """
        Check if any filter field is currently active.

        :return: True if at least one of query, start_date, or end_date is set.
        :rtype: bool
        """
        return bool([self.query, self.start_date, self.end_date])

    def is_empty(self) -> bool:
        """
        Check whether all filter parameters are empty.

        :return: True if query, start_date, and end_date are all unset.
        :rtype: bool
        """
        return not any([self.query, self.start_date, self.end_date])
