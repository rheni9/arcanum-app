"""
Message form for the Arcanum application.

Defines a WTForms-based form for creating and editing message entities,
with integrated validation, normalization, and structured logging.

Fields and validation are fully synchronized with the Message model.
"""

import logging
from datetime import datetime, date, time
from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField, TextAreaField, IntegerField,
    HiddenField, SubmitField, FileField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, URL, ValidationError
)

from app.models.message import Message
from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import (
    to_utc_iso, parse_flexible_date, parse_flexible_time, DEFAULT_TZ
)
from app.utils.cloudinary_utils import upload_screenshot

logger = logging.getLogger(__name__)


def validate_not_blank(_form, field) -> None:
    """
    Validate that the field is not empty or whitespace-only.

    Used as a WTForms validator to prevent empty message text.
    Raises a validation error if the input is invalid.

    :param _form: WTForms parent form (unused).
    :param field: The field to validate.
    :raises ValidationError: If the value is empty or blank.
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

    date = StringField(
        "Date",
        validators=[DataRequired(message="Date is required.")]
    )
    time = StringField(
        "Time",
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

    screenshot = FileField(
        "Screenshot",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")
        ]
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
        self._parsed_date: date | None = None
        self._parsed_time: time | None = None
        self._final_dt: datetime | None = None
        logger.debug("[MESSAGES|FORM] MessageForm initialized.")

    def validate_date(self, field: StringField) -> None:
        """
        Validate and parse the date input field.

        Parses user-provided date into a valid date object.
        Stores the result internally if valid, or raises a validation error.

        :param field: The date field to validate.
        :raises ValidationError: If the date is invalid or does not exist.
        """
        raw = field.data.strip() if field.data else ""
        logger.debug("[MESSAGES|FORM] Raw date input: '%s'", raw)
        date_obj, error = parse_flexible_date(raw)
        if error:
            raise ValidationError(error)
        self._parsed_date = date_obj

    def validate_time(self, field: StringField) -> None:
        """
        Validate and parse the time input field.

        Parses user-provided time into a valid time object.
        Stores the result internally if valid, or raises a validation error.

        :param field: The time field to validate.
        :raises ValidationError: If the time is invalid or does not exist.
        """
        raw = field.data.strip() if field.data else ""
        logger.debug("[MESSAGES|FORM] Raw time input: '%s'", raw)
        time_obj, error = parse_flexible_time(raw)
        if error:
            raise ValidationError(error)
        self._parsed_time = time_obj

    def validate(self, extra_validators: list | None = None) -> bool:
        """
        Run standard and custom validation logic.

        Includes extra checks for future timestamps.

        :param extra_validators: Optional list of additional validators.
        :return: True if the form is valid, False otherwise.
        """
        is_valid = super().validate(extra_validators)
        if not is_valid:
            logger.debug(
                "[MESSAGES|FORM] Validation failed. Errors: %s", self.errors
            )
            return False

        date_raw = self.date.data.strip() if self.date.data else ""
        time_raw = self.time.data.strip() if self.time.data else ""
        logger.debug(
            "[MESSAGES|FORM] Raw date: '%s' | time: '%s'", date_raw, time_raw
        )

        # Parse date
        self._parsed_date, date_error = parse_flexible_date(date_raw)
        if date_error:
            self.date.errors.append(date_error)
            is_valid = False

        # Parse time
        self._parsed_time, time_error = parse_flexible_time(time_raw)
        if time_error:
            self.time.errors.append(time_error)
            is_valid = False

        if self._parsed_date and self._parsed_time:
            local_dt = datetime.combine(self._parsed_date, self._parsed_time)
            local_dt = DEFAULT_TZ.localize(local_dt)
            if local_dt > datetime.now(DEFAULT_TZ):
                logger.debug(
                    "[MESSAGES|FORM] Date/time in future: %s", local_dt
                )
                self.date.errors.append("")
                self.time.errors.append("")
                self.datetime_error = "Date and time cannot be in the future."
                is_valid = False
            else:
                self._final_dt = local_dt

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
            logger.debug("[MESSAGES|FORM] Invalid link: %s", field.data)
            raise ValidationError(
                "Message link must start with 'http://' or 'https://'."
            )

    def process_tags(self) -> list[str]:
        """
        Process and normalize the tags field.

        Splits the tags string by comma, strips whitespace,
        and returns a list of non-empty tags.

        :return: List of stripped tag strings.
        """
        if not self.tags.data:
            return []
        return [
            tag.strip() for tag in self.tags.data.split(",") if tag.strip()
        ]

    def populate_from_model(self, message: Message) -> None:
        """
        Fill the form fields using data from a Message instance.

        Populates all fields in the form based on the provided model.

        :param chat: The Message object containing source values.
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
        Convert form data to a dictionary matching the Message model.

        Converts and normalizes user input into a format that matches
        the Message model fields. Handles empty values, integers, and booleans.

        :return: Dictionary suitable for passing to Message or database layer.
        """
        timestamp = None
        if self._final_dt:
            timestamp = to_utc_iso(self._final_dt)

        screenshot_url = None
        if "screenshot" in request.files:
            file = request.files["screenshot"]
            if file and file.filename:
                screenshot_url = upload_screenshot(file)

        data = {
            "id": to_int_or_none(self.id.data),
            "chat_ref_id": empty_to_none(self.chat_ref_id.data),
            "msg_id": to_int_or_none(self.msg_id.data),
            "timestamp": timestamp,
            "link": empty_to_none(self.link.data),
            "text": empty_to_none(self.text.data),
            "media": empty_to_none(self.media.data),
            "screenshot": (
                screenshot_url or empty_to_none(self.screenshot.data)
            ),
            "tags": self.process_tags(),
            "notes": empty_to_none(self.notes.data),
        }
        logger.debug("[MESSAGES|FORM] Form data for model: %s", data)
        return data
