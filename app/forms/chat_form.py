"""
Chat form for the Arcanum application.

Defines a WTForms-based form for creating and editing chat metadata,
with integrated field validation and structured logging.

Fields and validation are fully synchronized with the Chat model.
"""

import logging
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, BooleanField,
    IntegerField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, URL, Optional, NumberRange, ValidationError
)

from app.models.chat import Chat
from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import parse_flexible_date

logger = logging.getLogger(__name__)


class ChatForm(FlaskForm):
    """
    Represents the chat creation and edit form.

    Contains fields for all chat metadata and status toggles.
    """
    id = HiddenField()  # Used for editing only (optional)
    slug = HiddenField()  # Used for editing only

    name = StringField(
        "Chat Name",
        validators=[DataRequired(message="Chat name is required.")]
    )

    type = StringField("Type", validators=[Optional()])

    link = StringField(
        "Link",
        validators=[
            Optional(),
            URL(message="Please enter a valid URL starting with "
                        "http:// or https://.")
        ]
    )

    chat_id = IntegerField(
        "Chat ID",
        validators=[
            Optional(),
            NumberRange(min=0, message="Chat ID must be a positive integer.")
        ]
    )

    joined = StringField("Joined Date")

    is_active = BooleanField("Active")
    is_member = BooleanField("Member")
    is_public = BooleanField("Public")
    notes = TextAreaField("Notes", validators=[Optional()])

    submit = SubmitField("Save")

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and log the creation.
        """
        super().__init__(*args, **kwargs)
        logger.debug("[CHATS|FORM] ChatForm initialized.")

    def validate(self, extra_validators: list | None = None) -> bool:
        """
        Run all field validators and log validation results.

        :param extra_validators: Optional list of additional validators.
        :return: True if the form is valid, False otherwise.
        """
        is_valid = super().validate(extra_validators)
        if not is_valid:
            logger.debug(
                "[CHATS|FORM] Validation failed. Errors: %s", self.errors
            )
        return is_valid

    def validate_link(self, field: StringField) -> None:
        """
        Validate the format of the link field.

        Raises an error if the link is not empty and does not start with
        'http://' or 'https://'.

        :param field: The link field to validate.
        :raises ValidationError: If the link has an invalid prefix.
        """
        if field.errors or not field.data:
            return
        if not field.data.startswith(("http://", "https://")):
            logger.debug("[CHATS|FORM] Invalid link: %s", field.data)
            raise ValidationError(
                "Chat link must start with 'http://' or 'https://'."
            )

    def validate_joined(self, field: StringField) -> None:
        """
        Validate the join date field.

        :param field: The join date field to validate.
        :raises ValidationError: If the date is invalid or in the future.
        """
        raw = field.data.strip() if field.data else ""
        logger.debug("[CHATS|FORM] Raw joined date input: '%s'", raw)
        if not raw:
            return

        joined_date, error = parse_flexible_date(raw)
        if error:
            raise ValidationError(error)

        if joined_date > datetime.utcnow().date():
            logger.debug("[CHATS|FORM] Join date in future: %s", joined_date)
            raise ValidationError("Join date cannot be in the future.")

        field.data = joined_date.isoformat()

    def populate_from_model(self, chat: Chat) -> None:
        """
        Fill the form fields using data from a Chat instance.

        Populates all fields in the form based on the provided model.

        :param chat: The Chat object containing source values.
        """
        logger.debug("[CHATS|FORM] Populating form from Chat: %s", chat)
        self.id.data = chat.id
        self.slug.data = chat.slug
        self.name.data = chat.name
        self.type.data = chat.type
        self.link.data = chat.link
        self.chat_id.data = chat.chat_id
        self.joined.data = chat.joined
        self.is_active.data = chat.is_active
        self.is_member.data = chat.is_member
        self.is_public.data = chat.is_public
        self.notes.data = chat.notes

    def to_model_dict(self) -> dict[str, object]:
        """
        Convert form data to a dictionary matching the Chat model.

        Converts and normalizes user input into a format that matches
        the Chat model fields. Handles empty values, integers, and booleans.

        :return: Dictionary suitable for passing to Chat or database layer.
        """
        data = {
            "id": to_int_or_none(self.id.data),
            "slug": empty_to_none(self.slug.data),
            "name": empty_to_none(self.name.data),
            "type": empty_to_none(self.type.data),
            "link": empty_to_none(self.link.data),
            "chat_id": to_int_or_none(self.chat_id.data),
            "joined": self.joined.data,
            "is_active": self.is_active.data,
            "is_member": self.is_member.data,
            "is_public": self.is_public.data,
            "notes": empty_to_none(self.notes.data),
        }
        logger.debug("[CHATS|FORM] Form data for model: %s", data)
        return data
