"""
Reusable data model for message filtering in the Arcanum application.

Encapsulates user-defined parameters for full-text search and
date-based filtering, supporting all message-related views and routes.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MessageFilters:
    """
    Represents message filtering parameters for search and date filters.

    Used in search queries, filtering operations, and UI display logic.

    :param action: Type of filtering action ('search' or 'filter').
    :type action: Optional[str]
    :param query: Full-text search query.
    :type query: Optional[str]
    :param date_mode: Date filter mode ('on', 'before', 'after', 'between').
    :type date_mode: Optional[str]
    :param start_date: Start date (YYYY-MM-DD).
    :type start_date: Optional[str]
    :param end_date: End date (YYYY-MM-DD).
    :type end_date: Optional[str]
    """
    action: Optional[str] = None
    query: Optional[str] = None
    date_mode: str = "on"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def normalize(self, verbose: bool = False) -> None:
        """
        Normalize all fields: strip whitespace, convert blanks to None.

        :param verbose: If True, log normalized values.
        :type verbose: bool
        """
        self.query = self.query.strip() or None if self.query else None
        self.date_mode = self.date_mode.strip() if self.date_mode else "on"
        self.start_date = (
            self.start_date.strip() or None if self.start_date else None
        )
        self.end_date = (
            self.end_date.strip() or None if self.end_date else None
        )

        if verbose:
            logger.debug(
                "[FILTERS|NORMALIZE] Normalized: action='%s', query='%s', "
                "date_mode='%s', start_date='%s', end_date='%s'.",
                self.action, self.query, self.date_mode,
                self.start_date, self.end_date
            )

    def has_active(self) -> bool:
        """
        Check if any filter is active (query or date filters).

        :return: True if query, start_date, or end_date is set.
        :rtype: bool
        """
        return any([self.query, self.start_date, self.end_date])

    def is_empty(self) -> bool:
        """
        Check if no filters are applied.

        :return: True if query, start_date, and end_date are all unset.
        :rtype: bool
        """
        return not self.has_active()
