"""
Message form for the Arcanum application.

Defines a WTForms-based form for creating and editing message entities,
with integrated validation, normalization, and structured logging.

Fields and validation are fully synchronized with the Message model.
"""

import logging
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, IntegerField,
    DateField, TimeField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, URL, ValidationError
)

from app.models.message import Message
from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import to_utc_iso, DEFAULT_TZ

logger = logging.getLogger(__name__)


def validate_not_blank(_form, field) -> None:
    """
    WTForms validator to ensure the field is not empty or whitespace.

    :param _form: Parent form (unused).
    :param field: WTForms field.
    :raises ValidationError: If field is empty or contains only whitespace.
    """
    if not field.data or not field.data.strip():
        raise ValidationError("Text cannot be empty or whitespace.")


class MessageForm(FlaskForm):
    """
    Represents the message creation and edit form.

    Contains fields for message content, metadata, and user notes.
    """
    id = HiddenField()  # Used for editing only (optional)
    chat_ref_id = HiddenField()  # FK for the parent chat

    msg_id = IntegerField(
        "Message ID",
        validators=[
            Optional(),
            NumberRange(
                min=0, message="Message ID must be a positive integer."
            )
        ]
    )

    date = DateField(
        "Date",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Date is required.")]
    )
    time = TimeField(
        "Time",
        format="%H:%M:%S",
        validators=[DataRequired(message="Time is required.")]
    )

    link = StringField(
        "Message Link",
        validators=[
            Optional(),
            URL(message="Please enter a valid URL starting with "
                        "http:// or https://.")
        ]
    )

    text = TextAreaField(
        "Text",
        validators=[validate_not_blank]
    )

    media = StringField(
        "Media (file path or URL)",
        validators=[Optional()]
    )

    screenshot = StringField(
        "Screenshot (file path or URL)",
        validators=[Optional()]
    )

    tags = StringField(
        "Tags",
        validators=[Optional()]
    )

    notes = TextAreaField(
        "Notes",
        validators=[Optional()]
    )

    submit = SubmitField("Save")

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the form and log the creation.
        """
        super().__init__(*args, **kwargs)
        self.datetime_error = None
        logger.debug("[MESSAGES|FORM] MessageForm initialized.")

    def validate(self, extra_validators: list | None = None) -> bool:
        """
        Run all validators and custom datetime validation.

        :param extra_validators: Optional list of extra validator callables.
        :return: True if form passes all validation, False otherwise.
        """
        initial = super().validate(extra_validators)
        if not initial:
            logger.debug(
                "[MESSAGES|FORM] Validation failed. Errors: %s", self.errors
            )
            return False

        if self.date.data and self.time.data:
            local_dt = datetime.combine(self.date.data, self.time.data)
            local_dt = DEFAULT_TZ.localize(local_dt)
            if local_dt > datetime.now(DEFAULT_TZ):
                logger.debug(
                    "[MESSAGES|FORM] Date/time in future: %s", local_dt
                )
                self.date.errors.append(
                    "Date and time cannot be in the future."
                )
                self.time.errors.append(
                    "Date and time cannot be in the future."
                )
                self.datetime_error = "Date and time cannot be in the future."
                return False
        return True

    def validate_link(self, field: StringField) -> None:
        """
        Ensure the link starts with http:// or https:// if provided.
        """
        if field.errors or not field.data:
            return
        if not field.data.startswith(("http://", "https://")):
            logger.debug("[MESSAGES|FORM] Invalid link: %s", field.data)
            raise ValidationError(
                "Message link must start with 'http://' or 'https://'."
            )

    def process_tags(self) -> list[str]:
        """
        Process and normalize the tags field.

        Splits the tags string by comma, strips whitespace,
        and returns a list of non-empty tags.

        :return: List of stripped tags.
        """
        if not self.tags.data:
            return []
        return [
            tag.strip() for tag in self.tags.data.split(",") if tag.strip()
        ]

    def populate_from_model(self, message: Message) -> None:
        """
        Populate the form fields from a Message model instance.

        :param message: Message model instance.
        """
        logger.debug(
            "[MESSAGES|FORM] Populating form from Message: %s", message
        )
        self.id.data = message.id
        self.chat_ref_id.data = message.chat_ref_id
        self.msg_id.data = message.msg_id
        if message.timestamp:
            local_dt = message.timestamp.astimezone(DEFAULT_TZ)
            self.date.data = local_dt.date()
            self.time.data = local_dt.time()
        else:
            self.date.data = None
            self.time.data = None
        self.link.data = message.link
        self.text.data = message.text
        self.media.data = message.media
        self.screenshot.data = message.screenshot
        self.tags.data = ", ".join(message.tags) if message.tags else ""
        self.notes.data = message.notes

    def to_model_dict(self) -> dict:
        """
        Convert the form data to a dictionary suitable for the Message model.

        :return: Dictionary of form data.
        """
        timestamp = None
        if self.date.data and self.time.data:
            local_dt = datetime.combine(self.date.data, self.time.data)
            local_dt = DEFAULT_TZ.localize(local_dt)
            timestamp = to_utc_iso(local_dt)

        data = {
            "id": to_int_or_none(self.id.data),
            "chat_ref_id": empty_to_none(self.chat_ref_id.data),
            "msg_id": to_int_or_none(self.msg_id.data),
            "timestamp": timestamp,
            "link": empty_to_none(self.link.data),
            "text": empty_to_none(self.text.data),
            "media": empty_to_none(self.media.data),
            "screenshot": empty_to_none(self.screenshot.data),
            "tags": self.process_tags(),
            "notes": empty_to_none(self.notes.data),
        }
        logger.debug("[MESSAGES|FORM] Form data for model: %s", data)
        return data
