"""
Message models for the Arcanum application.

Defines data classes and methods for message entities,
including conversion, normalization, and database integration.
"""

import logging
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any

from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import to_utc_iso, from_utc_iso

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    Represents message entity.

    Stores message content, metadata, and user data
    for display, filtering, and storage.
    """
    id: int
    chat_ref_id: int  # FK to Chat.id
    msg_id: int | None = None
    timestamp: datetime | None = None  # Timezone-aware UTC datetime
    link: str | None = None
    text: str | None = None
    media: str | None = None
    screenshot: str | None = None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None

    @staticmethod
    def _parse_tags(val: Any) -> list[str]:
        """
        Parse tags from JSON, CSV string, or list.

        :param val: Tags as list, JSON string, or CSV string.
        :return: List of stripped tag strings.
        """
        if isinstance(val, list):
            return Message._parse_tags_from_list(val)
        if isinstance(val, str):
            return Message._parse_tags_from_string(val)
        return []

    @staticmethod
    def _parse_tags_from_list(items: list[Any]) -> list[str]:
        """
        Extract and clean tags from a list.
        """
        return [
                tag.strip()
                for tag in items
                if isinstance(tag, str) and tag.strip()
            ]

    @staticmethod
    def _parse_tags_from_string(val: str) -> list[str]:
        """
        Try parsing tags from JSON string first, then fallback to CSV.
        """
        val = val.strip()
        if not val:
            return []

        try:
            tags = json.loads(val)
            return [
                tag.strip()
                for tag in tags
                if isinstance(tag, str) and tag.strip()
            ]
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(
                "[MESSAGES|MODEL|TAGS] Fallback to CSV, could not parse JSON: "
                "%s | %s", val, e
            )
            return [tag.strip() for tag in val.split(",") if tag.strip()]

    @staticmethod
    def _parse_timestamp(val: str | datetime | None) -> datetime | None:
        """
        Parse UTC timestamp from various input types.

        Accepts a datetime object (aware or naive), an ISO 8601 string
        (with or without 'Z'), or None. Returns a timezone-aware UTC
        datetime object or None.

        :param val: Datetime as ISO string, datetime object, or None.
        :return: Timezone-aware UTC datetime object or None.
        """
        result = None
        if val is None:
            result = None
        elif isinstance(val, datetime):
            if val.tzinfo is not None:
                # Already timezone-aware, bring to UTC
                result = val.astimezone(timezone.utc)
            else:
                # Naive datetime, assume UTC
                result = val.replace(tzinfo=timezone.utc)
        elif isinstance(val, str):
            val = val.strip()
            if not val:
                result = None
            else:
                try:
                    # Parse via time_utils (handles Z, etc.)
                    result = from_utc_iso(val, "UTC")
                except (ValueError, TypeError) as e:
                    logger.warning(
                        "[MESSAGES|MODEL|TIMESTAMP] Failed to parse timestamp "
                        "'%s': %s", val, e
                    )
                    result = None
        return result

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Message":
        """
        Create a Message instance from a database row.

        Designed for use with SQL/ORM row mappings.

        :param row: Database row as mapping or tuple.
        :return: Message instance.
        """
        msg = cls(
            id=row["id"],
            chat_ref_id=row["chat_ref_id"],
            msg_id=to_int_or_none(row.get("msg_id")),
            timestamp=cls._parse_timestamp(row.get("timestamp")),
            link=empty_to_none(row.get("link")),
            text=empty_to_none(row.get("text")),
            media=empty_to_none(row.get("media")),
            screenshot=empty_to_none(row.get("screenshot")),
            tags=cls._parse_tags(row.get("tags")),
            notes=empty_to_none(row.get("notes")),
        )
        logger.debug("[MESSAGES|MODEL] Parsed Message from row: %s", msg)
        return msg

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """
        Create a Message instance from a generic dictionary.

        Intended for use with deserialized JSON or manual dicts.

        :param data: Dictionary of message fields.
        :return: Message instance.
        """
        msg = cls(
            id=to_int_or_none(data.get("id", 0)),
            chat_ref_id=int(data["chat_ref_id"]),
            msg_id=to_int_or_none(data.get("msg_id")),
            timestamp=cls._parse_timestamp(data.get("timestamp")),
            link=empty_to_none(data.get("link")),
            text=empty_to_none(data.get("text")),
            media=empty_to_none(data.get("media")),
            screenshot=empty_to_none(data.get("screenshot")),
            tags=cls._parse_tags(data.get("tags")),
            notes=empty_to_none(data.get("notes"))
        )
        logger.debug("[MESSAGES|MODEL] Created Message from dict: %s", msg)
        return msg

    def normalize(self) -> None:
        """
        Normalize text and tags fields.

        Trims text and tags, removing empty tags.
        """
        if self.text:
            self.text = self.text.strip()
        self.tags = [tag.strip() for tag in self.tags if tag.strip()]
        logger.debug("[MESSAGES|MODEL] Normalized Message: %s", self)

    def to_dict(self) -> dict:
        """
        Return the message as a dictionary.

        :return: Message as dictionary.
        """
        result = asdict(self)
        # Serialize datetime to ISO string for output (if present)
        if self.timestamp:
            result["timestamp"] = to_utc_iso(self.timestamp)
        return result

    def prepare_for_db(self) -> tuple:
        """
        Prepare the message data for database operations.

        Normalize the message and return a tuple of values
        for SQL insert or update.

        :return: Tuple of normalized message fields for SQL operations.
        """
        self.normalize()
        timestamp_str = to_utc_iso(self.timestamp) if self.timestamp else None
        tags_value = json.dumps(self.tags if self.tags is not None else [])
        return (
            self.chat_ref_id,
            self.msg_id,
            timestamp_str,
            self.link,
            self.text,
            self.media,
            self.screenshot,
            tags_value,
            self.notes
        )

    def get_short_text(self, limit: int = 50) -> str:
        """
        Return a shortened, single-line version of the message text.

        :param limit: Character limit.
        :return: Shortened message text without linebreaks.
        """
        if not self.text:
            return ""
        text = self.text.replace("\r", " ").replace("\n", " ")
        text = " ".join(text.split())
        if len(text) <= limit:
            return text
        return text[:limit] + "..."
