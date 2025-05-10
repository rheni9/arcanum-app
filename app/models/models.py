"""
Core data models for the Arcanum application.

Defines structured dataclasses for representing domain entities,
such as chats and messages. These models enable consistent access,
validation, and transfer of data between application layers.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Chat:
    """
    Represents a chat entity with metadata and user-defined attributes.

    Used throughout the application for storing, displaying, and filtering
    chat-level information.

    :param slug: Unique identifier for the chat.
    :type slug: str
    :param name: Display name of the chat.
    :type name: str
    :param chat_id: External platform-specific ID (e.g., Telegram ID).
    :type chat_id: Optional[str]
    :param link: Optional public link to the chat.
    :type link: Optional[str]
    :param type: Chat type (e.g., group, channel, private).
    :type type: Optional[str]
    :param joined: Join date in 'YYYY-MM-DD' format (optional).
    :type joined: Optional[str]
    :param is_active: Whether the chat is considered currently active.
    :type is_active: bool
    :param is_member: Whether the user is a current member of the chat.
    :type is_member: bool
    :param notes: Optional notes or comments about the chat.
    :type notes: Optional[str]
    """
    slug: str
    name: str
    chat_id: Optional[str] = None
    link: Optional[str] = None
    type: Optional[str] = None
    joined: Optional[str] = None
    is_active: bool = False
    is_member: bool = False
    notes: Optional[str] = None


@dataclass
class Message:
    """
    Represents an individual message within a specific chat.

    Stores message metadata, content, timestamp, media references,
    and user annotations.

    :param chat_slug: Slug of the chat to which the message belongs.
    :type chat_slug: str
    :param msg_id: Unique message identifier within the chat (sequential ID).
    :type msg_id: str
    :param link: Optional public link to the message.
    :type link: Optional[str]
    :param text: Text content of the message.
    :type text: Optional[str]
    :param timestamp: ISO 8601 UTC timestamp of when the message was sent.
    :type timestamp: str
    :param media_file: Path or URL to the attached media file (if any).
    :type media_file: Optional[str]
    :param screenshot: Path or URL to a screenshot (if any).
    :type screenshot: Optional[str]
    :param tags: List of tags associated with the message.
    :type tags: List[str]
    :param notes: Optional user-added notes or commentary.
    :type notes: Optional[str]
    """
    chat_slug: str
    msg_id: str
    link: Optional[str] = None
    text: Optional[str] = None
    timestamp: str = ""
    media_file: Optional[str] = None
    screenshot: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
