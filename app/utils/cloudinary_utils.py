"""
Cloudinary upload utilities for the Arcanum application.

Provides helper functions for uploading screenshots
to Cloudinary with WebP conversion and quality control.
"""

from PIL import Image, UnidentifiedImageError
from cloudinary.uploader import upload
from cloudinary.exceptions import Error as CloudinaryError


def upload_screenshot(file_storage, chat_slug: str) -> str:
    """
    Upload screenshot to Cloudinary as WebP with controlled quality.

    Stores image under the folder 'arcanum/screenshots/<chat_slug>'.

    :param file_storage: Werkzeug FileStorage object from form.
    :param chat_slug: Slug of the chat to organize images.
    :return: Cloudinary image URL in WebP format.
    :raises RuntimeError: If upload fails.
    """
    try:
        result = upload(
            file_storage,
            folder=f"arcanum/chats/screenshots/{chat_slug}",
            resource_type="image",
            format="webp",
            quality="auto:good"
        )
        return result["secure_url"]
    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e


def is_image_file(file_storage) -> bool:
    """
    Determine if uploaded file is an image.

    :param file_storage: FileStorage object
    :return: True if image, False otherwise
    """
    try:
        file_storage.stream.seek(0)
        Image.open(file_storage.stream).verify()
        file_storage.stream.seek(0)  # reset stream after verify
        return True
    except (UnidentifiedImageError, OSError):
        return False


def upload_media_file(file_storage, chat_slug: str) -> str:
    """
    Uploads any media file to Cloudinary.
    Images will be converted to WebP, others as-is.

    :param file_storage: FileStorage object from form.
    :param chat_slug: Slug to organize uploads.
    :return: URL to the uploaded media.
    """
    try:
        is_image = is_image_file(file_storage)
        result = upload(
            file_storage,
            folder=f"arcanum/chats/media/{chat_slug}",
            resource_type="auto",
            format="webp" if is_image else None,
            quality="auto:good" if is_image else None
        )
        return result["secure_url"]
    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e
