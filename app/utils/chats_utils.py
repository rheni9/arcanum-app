"""
Chat utilities for the Arcanum application.

Provides:
- construction of Chat model instances from form data,
- centralized object building for insert/update operations.
"""

import logging

from app.models.chat import Chat
from app.forms.chat_form import ChatForm
from app.utils.time_utils import parse_date_to_dateobject

logger = logging.getLogger(__name__)


def build_chat_object(
    form: ChatForm,
    slug: str,
    chat_ref_id: int | None = None
) -> Chat:
    """
    Build a Chat model instance from form data.

    :param form: ChatForm instance.
    :param slug: Chat slug.
    :param chat_ref_id: Existing chat ID (for update).
    :return: Chat instance.
    """
    joined = form.joined.data
    return Chat(
        id=chat_ref_id,
        slug=slug,
        name=form.name.data,
        chat_id=form.chat_id.data if form.chat_id.data else None,
        type=form.type.data.strip() if form.type.data else None,
        link=form.link.data.strip() if form.link.data else None,
        joined=joined.isoformat() if joined else None,
        is_active=form.is_active.data,
        is_member=form.is_member.data,
        is_public=form.is_public.data,
        notes=form.notes.data.strip() if form.notes.data else None
    )


def prepare_chat_for_form(chat):
    """
    Prepare chat for WTForms usage.

    Ensures 'joined' is a datetime.date if stored as str in the database.
    """
    if chat and chat.joined and isinstance(chat.joined, str):
        chat.joined = parse_date_to_dateobject(chat.joined)
    return chat
