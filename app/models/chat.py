"""
Chat models for the Arcanum application.

Defines data classes and methods for chat entities,
including conversion, normalization, and database integration.
"""

import logging
from datetime import date, datetime
from dataclasses import dataclass, asdict
from typing import Any

from app.utils.model_utils import empty_to_none, to_int_or_none

logger = logging.getLogger(__name__)


@dataclass
class Chat:
    """
    Represents a chat entity.

    Stores comprehensive chat metadata for internal management,
    display, and filtering operations.
    """
    id: int
    slug: str
    name: str
    chat_id: int | None = None
    link: str | None = None
    type: str | None = None
    joined: date | None = None
    is_active: bool = False
    is_member: bool = False
    is_public: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        """
        Normalize boolean fields and ensure correct
        date type after initialization.
        """
        self.is_active = bool(self.is_active)
        self.is_member = bool(self.is_member)
        self.is_public = bool(self.is_public)
        self.joined = self._parse_date(self.joined)

    @staticmethod
    def _parse_date(val: date | datetime | str | None) -> date | None:
        """
        Parse the joined date from various input types.

        Accepts date object, datetime object (uses date part), or ISO string.

        :param val: Date as date, datetime, ISO string, or None.
        :return: Date object or None.
        """
        result = None
        if val is None:
            result = None
        elif isinstance(val, date) and not isinstance(val, datetime):
            result = val
        elif isinstance(val, datetime):
            result = val.date()
        elif isinstance(val, str):
            s = val.strip()
            if not s:
                result = None
            else:
                # ISO format ('YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS')
                try:
                    result = date.fromisoformat(s.split("T")[0])
                except ValueError:
                    try:
                        result = datetime.strptime(s, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        result = None
        else:
            result = None
        return result

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Chat":
        """
        Create a Chat instance from a database row.

        Designed for use with SQL/ORM row mappings.

        :param row: Database row as mapping or tuple.
        :return: Chat instance.
        """
        chat = cls(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            chat_id=to_int_or_none(row.get("chat_id")),
            link=empty_to_none(row.get("link")),
            type=empty_to_none(row.get("type")),
            joined=cls._parse_date(row.get("joined")),
            is_active=row.get("is_active", False),
            is_member=row.get("is_member", False),
            is_public=row.get("is_public", False),
            notes=empty_to_none(row.get("notes"))
        )
        logger.debug("[CHATS|MODEL] Parsed Chat from DB row: %s", chat)
        return chat

    @classmethod
    def from_dict(cls, data: dict) -> "Chat":
        """
        Create a Chat instance from a generic dictionary.

        Intended for use with deserialized JSON or manual dicts.

        :param data: Dictionary of chat fields.
        :return: Chat instance.
        """
        chat = cls(
            id=to_int_or_none(data.get("id", 0)),
            slug=data["slug"],
            name=data["name"],
            chat_id=to_int_or_none(data.get("chat_id")),
            link=empty_to_none(data.get("link")),
            type=empty_to_none(data.get("type")),
            joined=cls._parse_date(data.get("joined")),
            is_active=data.get("is_active", False),
            is_member=data.get("is_member", False),
            is_public=data.get("is_public", False),
            notes=empty_to_none(data.get("notes"))
        )
        logger.debug("[CHATS|MODEL] Created Chat from dictionary: %s", chat)
        return chat

    def to_dict(self) -> dict:
        """
        Convert the chat to a dictionary.

        :return: Dictionary representation of the chat.
        """
        result = asdict(self)
        # Serialize date to ISO string for output (if present).
        if self.joined:
            result["joined"] = self.joined.isoformat()
        return result

    def prepare_for_db(self) -> tuple:
        """
        Prepare the chat data for database operations.

        Fields are returned in the following order:
        (chat_id, slug, name, link, type, joined,
        is_active, is_member, is_public, notes)

        :return: Tuple of normalized fields suitable for SQL INSERT/UPDATE.
        """
        joined_str = self.joined.isoformat() if self.joined else None
        return (
            self.chat_id,
            self.slug,
            self.name,
            self.link,
            self.type,
            joined_str,
            int(self.is_active),
            int(self.is_member),
            int(self.is_public),
            self.notes
        )

    def display_name(self) -> str:
        """
        Return the chat display name with slug.

        :return: String containing name and slug.
        """
        return f"{self.name} ({self.slug})"


@dataclass
class ChatInfo:
    """
    Represents minimal chat information.

    Stores essential fields for lightweight references.
    """
    id: int
    slug: str
    name: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ChatInfo":
        """
        Create a ChatInfo instance from a database row.

        :param row: Database row.
        :return: ChatInfo instance.
        """
        info = cls(
            id=row["id"],
            slug=row["slug"],
            name=row["name"]
        )
        logger.debug("[CHATS|MODEL] Parsed ChatInfo from row: %s", info)
        return info
