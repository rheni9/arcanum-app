"""
Chat models for the Arcanum application.

Defines data classes representing chat entities, including methods
for normalization, conversion from data sources, database integration,
and lightweight reference generation.
"""

import logging
from datetime import date
from dataclasses import dataclass, asdict
from typing import Any

from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import parse_to_date

logger = logging.getLogger(__name__)


@dataclass
class Chat:
    """
    Represents a full chat entity with metadata.

    Stores comprehensive chat metadata used for display,
    filtering, internal management, and database storage.

    :param id: Internal database ID.
    :param slug: Unique chat slug.
    :param name: Display name.
    :param chat_id: Telegram chat ID (if available).
    :param link: Optional link to the chat.
    :param type: Chat type (e.g., 'group', 'channel').
    :param joined: Date the user joined the chat.
    :param is_active: Whether the chat is currently active.
    :param is_member: Whether the user is a member.
    :param is_public: Whether the chat is publicly visible.
    :param notes: Optional notes.
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
        Normalize boolean flags and parse the joined date after initialization.

        Ensures that is_active, is_member, and is_public are strict booleans,
        and converts the joined field to a date object if needed.
        """
        self.is_active = bool(self.is_active)
        self.is_member = bool(self.is_member)
        self.is_public = bool(self.is_public)
        self.joined = parse_to_date(self.joined)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Chat":
        """
        Create a Chat instance from a database row.

        :param row: Dictionary with database columns.
        :return: Chat instance.
        """
        chat = cls(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            chat_id=to_int_or_none(row.get("chat_id")),
            link=empty_to_none(row.get("link")),
            type=empty_to_none(row.get("type")),
            joined=parse_to_date(row.get("joined")),
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
        Create a Chat instance from a dictionary.

        :param data: Dictionary with chat fields.
        :return: Chat instance.
        """
        chat = cls(
            id=to_int_or_none(data.get("id", 0)),
            slug=data["slug"],
            name=data["name"],
            chat_id=to_int_or_none(data.get("chat_id")),
            link=empty_to_none(data.get("link")),
            type=empty_to_none(data.get("type")),
            joined=parse_to_date(data.get("joined")),
            is_active=data.get("is_active", False),
            is_member=data.get("is_member", False),
            is_public=data.get("is_public", False),
            notes=empty_to_none(data.get("notes"))
        )
        logger.debug("[CHATS|MODEL] Created Chat from dictionary: %s", chat)
        return chat

    def to_dict(self) -> dict:
        """
        Convert the chat to a dictionary representation.

        :return: Dictionary with chat fields.
        """
        result = asdict(self)
        # Serialize date to ISO string for output (if present).
        if self.joined:
            result["joined"] = self.joined.isoformat()
        return result

    def prepare_for_db(self) -> tuple:
        """
        Prepare the chat instance for database operations.

        Normalizes and serializes fields required for SQL INSERT/UPDATE.

        Field order:
        (chat_id, slug, name, link, type, joined,
         is_active, is_member, is_public, notes)

        :return: Tuple of normalized chat field values.
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
        Return a display-friendly name including the chat slug.

        :return: Chat name with slug in parentheses.
        """
        return f"{self.name} ({self.slug})"

    def __repr__(self) -> str:
        """
        Compact debug representation of a Chat.

        :return: Summary string.
        """
        return (
            f"<Chat id={self.id} slug='{self.slug}' name='{self.name}' "
            f"is_active={self.is_active} is_member={self.is_member}>"
        )


@dataclass
class ChatInfo:
    """
    Represents a lightweight reference to a chat.

    :param id: Chat database ID.
    :param slug: Unique slug.
    :param name: Chat name.
    """
    id: int
    slug: str
    name: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ChatInfo":
        """
        Create a ChatInfo instance from a database row.

        :param row: Dictionary with 'id', 'slug', and 'name' fields.
        :return: ChatInfo instance.
        """
        info = cls(
            id=row["id"],
            slug=row["slug"],
            name=row["name"]
        )
        logger.debug("[CHATS|MODEL] Parsed ChatInfo from row: %s", info)
        return info

    def __repr__(self) -> str:
        """
        Compact debug representation of ChatInfo.

        :return: Summary string.
        """
        return f"<ChatInfo id={self.id} slug='{self.slug}' name='{self.name}'>"
