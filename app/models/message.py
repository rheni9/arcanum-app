"""
Message models for the Arcanum application.

Defines data classes representing message entities, including
timestamp parsing, normalization, tag handling, and database integration.
"""

import logging
import re
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any

from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import to_utc_iso, parse_to_datetime

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    Represents a message entity.

    Stores message content, metadata, and user-defined fields
    for display, filtering, search, and persistent storage.

    :param id: Internal database ID.
    :param chat_ref_id: Foreign key to Chat.id.
    :param msg_id: Telegram message ID (if available).
    :param timestamp: UTC-aware datetime.
    :param link: Optional link to the message.
    :param text: Text content of the message.
    :param media: Media file path or reference.
    :param screenshot: Screenshot file path or reference.
    :param tags: List of tag strings.
    :param notes: Optional notes.
    """
    id: int
    chat_ref_id: int
    msg_id: int | None = None
    timestamp: datetime | None = None
    link: str | None = None
    text: str | None = None
    media: list[str] = field(default_factory=list)
    screenshot: str | None = None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        """
        Normalize text and tags after initialization.

        Strips whitespace from the text and ensures tags are stored
        as a clean list of non-empty strings.
        """
        self.normalize()

    def normalize(self) -> None:
        """
        Normalize text and tags fields in place.

        Strips leading/trailing whitespace from the text,
        and removes empty or invalid tags.
        """
        if self.text:
            self.text = self.text.strip()
        self.tags = [tag.strip() for tag in self.tags if tag.strip()]
        logger.debug("[MESSAGES|MODEL] Normalized Message: %s", self)

    @staticmethod
    def _parse_list(val: Any) -> list[str]:
        """
        Parse tags from list, JSON string, or CSV string.

        :param val: Raw tags input.
        :return: List of cleaned tag strings.
        """
        if isinstance(val, list):
            return Message._parse_list_from_list(val)
        if isinstance(val, str):
            return Message._parse_list_from_string(val)
        return []

    @staticmethod
    def _parse_list_from_list(items: list[Any]) -> list[str]:
        """
        Extract and clean tag strings from a list.

        :param items: List of tags.
        :return: Cleaned list of tag strings.
        """
        return [
                tag.strip()
                for tag in items
                if isinstance(tag, str) and tag.strip()
            ]

    @staticmethod
    def _parse_list_from_string(val: str) -> list[str]:
        """
        Try parsing tags from a JSON string first, then fallback to CSV.

        :param val: String with JSON array or CSV tags.
        :return: List of tag strings.
        """
        val = val.strip()
        if not val:
            return []

        try:
            tags = json.loads(val)
            return Message._parse_list_from_list(tags)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(
                "[MESSAGES|MODEL|TAGS] Fallback to CSV, could not parse JSON: "
                "%s | %s", val, e
            )
            return [tag.strip() for tag in val.split(",") if tag.strip()]

    @staticmethod
    def _parse_media(val: Any) -> list[str]:
        """
        Parse media from list, JSON string, or CSV string.

        :param val: Raw media input.
        :return: List of cleaned media paths or URLs.
        """
        if isinstance(val, list):
            return [item.strip() for item in val
                    if isinstance(item, str) and item.strip()]
        if isinstance(val, str):
            val = val.strip()
            if not val:
                return []
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return [s.strip() for s in val.split(",") if s.strip()]
        return []

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Message":
        """
        Create a Message instance from a database row.

        :param row: Dictionary with database columns.
        :return: Message instance.
        """
        msg = cls(
            id=row["id"],
            chat_ref_id=row["chat_ref_id"],
            msg_id=to_int_or_none(row.get("msg_id")),
            timestamp=parse_to_datetime(row.get("timestamp")),
            link=empty_to_none(row.get("link")),
            text=empty_to_none(row.get("text")),
            media=cls._parse_media(row.get("media")),
            screenshot=empty_to_none(row.get("screenshot")),
            tags=cls._parse_list(row.get("tags")),
            notes=empty_to_none(row.get("notes")),
        )
        logger.debug("[MESSAGES|MODEL] Parsed Message from DB row: %s", msg)
        return msg

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """
        Create a Message instance from a dictionary.

        :param data: Dictionary with message fields.
        :return: Message instance.
        """
        msg = cls(
            id=to_int_or_none(data.get("id", 0)),
            chat_ref_id=int(data["chat_ref_id"]),
            msg_id=to_int_or_none(data.get("msg_id")),
            timestamp=parse_to_datetime(data.get("timestamp")),
            link=empty_to_none(data.get("link")),
            text=empty_to_none(data.get("text")),
            media=cls._parse_media(data.get("media")),
            screenshot=empty_to_none(data.get("screenshot")),
            tags=cls._parse_list(data.get("tags")),
            notes=empty_to_none(data.get("notes"))
        )
        logger.debug("[MESSAGES|MODEL] Created Message from dict: %s", msg)
        return msg

    def to_dict(self) -> dict:
        """
        Convert the message to a dictionary representation.

        :return: Dictionary with message fields.
        """
        result = asdict(self)
        # Serialize datetime to ISO string for output (if present)
        if self.timestamp:
            result["timestamp"] = to_utc_iso(self.timestamp)
        return result

    def prepare_for_db(self) -> dict:
        """
        Prepare the message instance for database operations.

        Normalizes and serializes fields required for SQL INSERT/UPDATE.

        Field order:
        (chat_ref_id, msg_id, timestamp, link, text,
         media, screenshot, tags, notes)

        :return: Dictionary of normalized message field values.
        """
        timestamp_str = to_utc_iso(self.timestamp) if self.timestamp else None
        media_value = json.dumps(self.media if self.media is not None else [])
        tags_value = json.dumps(self.tags if self.tags is not None else [])
        return {
            "chat_ref_id": self.chat_ref_id,
            "msg_id": self.msg_id,
            "timestamp": timestamp_str,
            "link": self.link,
            "text": self.text,
            "media": media_value,
            "screenshot": self.screenshot,
            "tags": tags_value,
            "notes": self.notes
        }

    def get_short_text(self, limit: int = 50) -> str:
        """
        Return a shortened single-line preview of the message text.

        Collapses all whitespace characters (tabs, newlines, multiple spaces)
        into single spaces and truncates the result if it exceeds the limit.

        :param limit: Maximum number of characters to show.
        :return: Cleaned and truncated message text.
        """
        if not self.text:
            return ""
        cleaned = re.sub(r"\s+", " ", self.text).strip()
        return cleaned if len(cleaned) <= limit else cleaned[:limit] + "..."

    def __repr__(self) -> str:
        """
        Compact debug representation of a Message.

        :return: Summary string.
        """
        short = (self.text or "")
        short = short[:27] + "..." if len(short) > 30 else short
        return (
            f"<Message id={self.id} chat={self.chat_ref_id} "
            f"msg={self.msg_id} text='{short}'>"
        )
