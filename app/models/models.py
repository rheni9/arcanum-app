"""
Core data models for the Arcanum application.

Defines structured dataclasses for representing chats and messages,
ensuring consistent access, transfer, and validation of domain entities.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Chat:
    """
    Represents a chat record in the database.

    Used for storing, displaying, and filtering chat-level information.

    :param id: Primary key in the local database.
    :type id: int
    :param slug: Unique URL-friendly identifier.
    :type slug: str
    :param name: Human-readable chat name.
    :type name: str
    :param chat_id: Telegram chat ID (external identifier).
    :type chat_id: Optional[int]
    :param link: Optional public link to the chat.
    :type link: Optional[str]
    :param type: Chat type (group, channel, private).
    :type type: Optional[str]
    :param joined: Join date in 'YYYY-MM-DD' format.
    :type joined: Optional[str]
    :param is_active: Whether the chat is marked as active.
    :type is_active: bool
    :param is_member: Whether the user is currently a member of the chat.
    :type is_member: bool
    :param notes: Optional user-defined notes.
    :type notes: Optional[str]
    """
    id: int  # Database primary key
    slug: str
    name: str
    chat_id: Optional[int] = None  # Telegram chat id
    link: Optional[str] = None
    type: Optional[str] = None
    joined: Optional[str] = None
    is_active: bool = False
    is_member: bool = False
    notes: Optional[str] = None


@dataclass
class Message:
    """
    Represents a single message stored in the database.

    :param id: Primary key in the local database.
    :type id: int
    :param chat_ref_id: Foreign key linking to parent chat (Chat.id).
    :type chat_ref_id: int
    :param msg_id: Telegram message ID (external identifier).
    :type msg_id: Optional[int]
    :param timestamp: UTC ISO 8601 timestamp of the message.
    :type timestamp: str
    :param link: Optional permalink to the message.
    :type link: Optional[str]
    :param text: Textual content of the message.
    :type text: Optional[str]
    :param media: Path or URL to attached media.
    :type media: Optional[str]
    :param screenshot: Path or URL to associated screenshot.
    :type screenshot: Optional[str]
    :param tags: List of user-defined tags.
    :type tags: List[str]
    :param notes: Optional user notes.
    :type notes: Optional[str]
    """
    id: int  # Database primary key
    chat_ref_id: int  # FK to Chat.id
    msg_id: Optional[int] = None  # Telegram msg_id
    timestamp: str = ""
    link: Optional[str] = None
    text: Optional[str] = None
    media: Optional[str] = None
    screenshot: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
