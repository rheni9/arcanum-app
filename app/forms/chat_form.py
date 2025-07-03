"""
Chat form for the Arcanum application.

Defines a WTForms-based form for creating and editing chat metadata,
with integrated field validation and structured logging.

Fields and validation are fully synchronized with the Chat model.
"""

import logging
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField, TextAreaField, BooleanField, FileField,
    IntegerField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, URL, Optional, NumberRange, ValidationError
)
from PIL import Image, UnidentifiedImageError

from app.models.chat import Chat
from app.services.chats_service import slug_exists
from app.utils.slugify_utils import slugify, generate_unique_slug
from app.utils.model_utils import empty_to_none, to_int_or_none
from app.utils.time_utils import parse_flexible_date
from app.utils.backblaze_utils import upload_image

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

    image = FileField(
        "Chat Image",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"],
                "Invalid image file or unsupported format."
            )
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

    def validate_image(self, field: FileField) -> None:
        """
        Validate the uploaded chat image file.

        :param field: The image file field.
        :raises ValidationError: If the file is not a valid image.
        """
        file = field.data
        if file and file.filename:
            try:
                Image.open(file).verify()
                file.stream.seek(0)  # Reset stream position
            except (UnidentifiedImageError, OSError) as e:
                logger.warning(
                    "[CHATS|FORM] Invalid image file: %s", e
                )
                raise ValidationError(
                    "Invalid image file or unsupported format."
                ) from e

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

    def _resolve_slug(
        self,
        name_value: str,
        original_slug: str | None
    ) -> str:
        """
        Determine final slug based on current and original name.

        Keeps original slug if name is unchanged.
        Generates new slug only if name changes or new chat.

        :param name_value: Current name input.
        :param original_slug: Existing slug if editing.
        :return: Final slug.
        """
        if not original_slug:
            # New chat: generate slug
            new_slug = slugify(name_value)
            if slug_exists(new_slug):
                logger.debug(
                    "[CHATS|FORM] Slug '%s' exists. Resolving unique.",
                    new_slug
                )
                return generate_unique_slug(new_slug, seed=name_value)
            return new_slug

        # Editing existing chat
        original_name = getattr(self.name, "object_data", "") or ""
        current_name = name_value

        if current_name == original_name:
            logger.debug(
                "[CHATS|FORM] Name unchanged. Keeping slug '%s'.",
                original_slug
            )
            return original_slug

        new_slug = slugify(current_name)
        if slug_exists(new_slug):
            logger.debug(
                "[CHATS|FORM] Slug '%s' exists. Resolving unique.", new_slug
            )
            return generate_unique_slug(new_slug, seed=current_name)

        return new_slug

    def _resolve_image_url(
        self,
        slug: str,
        existing_image: str | None
    ) -> str | None:
        """
        Determine final image URL for the chat.

        Uploads new file if provided; otherwise returns existing image URL.

        :param slug: Chat slug (used for storage path).
        :param existing_image: Current image URL from DB.
        :return: New or existing image URL.
        :raises ValidationError: If upload fails.
        """
        file = self.image.data
        if file and getattr(file, "filename", ""):
            try:
                return upload_image(file, slug)
            except RuntimeError as e:
                logger.warning("[CHATS|FORM] Failed to upload image: %s", e)
                self.image.errors.append("Invalid image file or format.")
                raise ValidationError("Image upload failed.") from e
        return (
            self.image.data
            if isinstance(self.image.data, str)
            else existing_image
        )

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
        self.image.data = chat.image
        self.joined.data = chat.joined
        self.is_active.data = chat.is_active
        self.is_member.data = chat.is_member
        self.is_public.data = chat.is_public
        self.notes.data = chat.notes

    def to_model_dict(
        self,
        existing_image: str | None = None,
        original_slug: str | None = None
    ) -> dict[str, object]:
        """
        Convert form data to a dictionary matching the Chat model.

        Resolves final slug and image URL, normalizes fields, and prepares
        all data for creating or updating a Chat instance.

        :param existing_image: Existing chat image URL from DB.
        :param original_slug: Original slug if editing.
        :return: Normalized dictionary for the Chat model.
        :raises ValidationError: If slug is not unique or image upload fails.
        """
        name_value = (self.name.data or "").strip()

        # Resolve final slug
        slug_value = self._resolve_slug(name_value, original_slug)

        # Resolve image
        image_url = self._resolve_image_url(slug_value, existing_image)

        # Prepare final dict
        data = {
            "id": to_int_or_none(self.id.data),
            "slug": slug_value,
            "name": empty_to_none(self.name.data),
            "type": empty_to_none(self.type.data),
            "link": empty_to_none(self.link.data),
            "chat_id": to_int_or_none(self.chat_id.data),
            "image": image_url,
            "joined": self.joined.data,
            "is_active": self.is_active.data,
            "is_member": self.is_member.data,
            "is_public": self.is_public.data,
            "notes": empty_to_none(self.notes.data),
        }

        logger.debug("[CHATS|FORM] Form data for model: %s", data)
        return data
