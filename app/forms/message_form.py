"""
Message form for the Arcanum application.

Defines a WTForms-based form for creating and editing message entities,
with integrated validation, normalization, and structured logging.

Fields and validation are fully synchronized with the Message model.
"""

import logging
import json
from datetime import datetime, date, time
from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField, TextAreaField, IntegerField,
    HiddenField, SubmitField, FileField, MultipleFileField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, URL, ValidationError
)
from PIL import Image, UnidentifiedImageError

from app.models.message import Message
from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import (
    to_utc_iso, parse_flexible_date, parse_flexible_time, DEFAULT_TZ
)
from app.utils.backblaze_utils import upload_screenshot, upload_media_file

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

    media = MultipleFileField(
        "Upload Media (up to 5 files)",
        validators=[Optional()]
    )

    screenshot = FileField(
        "Screenshot",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"],
                "Invalid image file or unsupported format."
            )
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

    def __init__(self, *args, chat_slug: str = None, **kwargs) -> None:
        """
        Initialize the form and log the creation.
        """
        super().__init__(*args, **kwargs)
        self.datetime_error = None
        self._parsed_date: date | None = None
        self._parsed_time: time | None = None
        self._final_dt: datetime | None = None
        self.chat_slug = chat_slug
        logger.debug("[MESSAGES|FORM] MessageForm initialized.")

    def _parse_media_field(self) -> list[str]:
        """
        Parse and normalize the media field into a list.

        Handles both JSON list input and comma-separated string.

        :return: List of media items (e.g., paths or URLs).
        """
        raw = self.media.data
        if not raw:
            return []
        if isinstance(raw, list):
            return [
                item.strip() for item in raw
                if isinstance(item, str) and item.strip()
            ]
        if isinstance(raw, str):
            try:
                return json.loads(raw)  # Try as JSON list
            except json.JSONDecodeError:
                return [
                    item.strip() for item in raw.split(",") if item.strip()
                ]
        return []

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

    def validate_screenshot(self, field: FileField) -> None:
        """
        Validate the uploaded screenshot file.

        Attempts to open the uploaded file as an image to ensure
        it is a valid and supported format. Raises a validation error
        if the file cannot be identified as a valid image.

        :param field: The screenshot file field.
        :raises ValidationError: If the file is not a valid image.
        """
        file = field.data
        if file and file.filename:
            try:
                Image.open(file).verify()
                file.stream.seek(0)  # Reset stream position after verify
            except (UnidentifiedImageError, OSError) as e:
                logger.warning(
                    "[MESSAGES|FORM] Invalid screenshot file: %s", e
                )
                raise ValidationError(
                    "Invalid image file or unsupported format."
                ) from e

    def validate_media(self, _field):
        """
        Validate uploaded media files: images must be valid,
        non-image files are skipped.
        """
        files = request.files.getlist("media")
        for file in files[:5]:
            if file and file.filename:
                if file.filename.lower().endswith(
                    ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
                ):
                    try:
                        Image.open(file).verify()
                        file.stream.seek(0)
                    except (UnidentifiedImageError, OSError) as e:
                        logger.warning(
                            "[MESSAGES|FORM] Invalid image in media upload: "
                            "%s", e
                        )
                        raise ValidationError(
                            "One or more media files are invalid images "
                            "or unsupported format."
                        ) from e

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

    def to_model_dict(
        self, existing_media=None, existing_screenshot=None
    ) -> dict:
        """
        Convert form data to a dictionary matching the Message model.

        Includes logic for conditional preservation of existing media
        and screenshot.

        :param existing_media: List of current media URLs (from DB).
        :param existing_screenshot: Existing screenshot URL (from DB).
        :return: Dictionary for creating/updating a Message.
        :raises ValidationError: If screenshot upload fails.
        """
        timestamp = to_utc_iso(self._final_dt) if self._final_dt else None

        # Screenshot
        file = self.screenshot.data
        if file and file.filename:
            timestamp_str = self.get_timestamp_string()
            try:
                screenshot_url = upload_screenshot(
                    file, self.chat_slug, timestamp_str
                )
            except RuntimeError as e:
                logger.warning(
                    "[MESSAGES|FORM] Failed to upload screenshot: %s", e
                )
                self.screenshot.errors.append("Invalid image file or format.")
                raise ValidationError("Screenshot upload failed.") from e
        else:
            screenshot_url = (
                self.screenshot.data if isinstance(self.screenshot.data, str)
                else existing_screenshot
            )

        # Media files
        uploaded_urls = []
        files = request.files.getlist("media")
        for file in files[:5]:
            if file and file.filename:
                try:
                    url = upload_media_file(file, self.chat_slug)
                    uploaded_urls.append(url)
                except RuntimeError as e:
                    logger.warning(
                        "[MESSAGES|FORM] Failed to upload media file: %s", e
                    )
                    self.media.errors.append(
                        "Some files could not be uploaded."
                    )

        parsed_manual = self._parse_media_field()
        existing_media = existing_media or []

        combined_media = existing_media + uploaded_urls + parsed_manual
        seen = set()
        media_urls = []
        for url in combined_media:
            if url not in seen:
                media_urls.append(url)
                seen.add(url)

        # Final dict
        data = {
            "id": to_int_or_none(self.id.data),
            "chat_ref_id": empty_to_none(self.chat_ref_id.data),
            "msg_id": to_int_or_none(self.msg_id.data),
            "timestamp": timestamp,
            "link": empty_to_none(self.link.data),
            "text": empty_to_none(self.text.data),
            "media": media_urls,
            "screenshot": screenshot_url,
            "tags": self.process_tags(),
            "notes": empty_to_none(self.notes.data),
        }

        logger.debug("[MESSAGES|FORM] Form data for model: %s", data)
        return data

    def get_timestamp_string(self) -> str:
        """
        Return timestamp from form in 'YYYYMMDD_HHMMSS' format.

        Combines parsed date and time fields.

        :return: Formatted timestamp string.
        """
        if self._parsed_date and self._parsed_time:
            return datetime.combine(
                self._parsed_date,
                self._parsed_time
            ).strftime("%Y%m%d_%H%M%S")
        return "unknown"
