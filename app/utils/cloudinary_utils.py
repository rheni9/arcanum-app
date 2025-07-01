"""
Cloudinary upload utilities for the Arcanum application.

Provides helper functions for uploading screenshots and other media
to Cloudinary with optional WebP conversion and quality control.
"""

import logging
from uuid import uuid4
from cloudinary.uploader import upload
from cloudinary.exceptions import Error as CloudinaryError

logger = logging.getLogger(__name__)


def is_image_file(file_storage) -> bool:
    """
    Determine if uploaded file is an image by extension.

    :param file_storage: FileStorage object.
    :return: True if file has image extension, False otherwise.
    """
    return file_storage.filename.lower().endswith((
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"
    ))


def upload_screenshot(file_storage, chat_slug: str, timestamp_str: str) -> str:
    """
    Upload screenshot to Cloudinary as WebP with controlled quality.

    Stores image under the folder 'arcanum/screenshots/<chat_slug>'.

    :param file_storage: Werkzeug FileStorage object.
    :param chat_slug: Chat slug for organizing storage.
    :param timestamp_str: Timestamp string (YYYYMMDD_HHMMSS).
    :return: Cloudinary secure URL for uploaded screenshot.
    :raises RuntimeError: If upload fails.
    """
    unique_suffix = uuid4().hex[:8]
    public_id = f"screenshot_{timestamp_str}_{unique_suffix}"
    folder = f"arcanum/chats/screenshots/{chat_slug}"

    logger.debug("[CLOUDINARY|UPLOAD] Preparing screenshot '%s'", public_id)

    try:
        result = upload(
            file_storage,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            format="webp",
            quality="auto:good",
            overwrite=False
        )
        logger.info(
            "[CLOUDINARY|UPLOAD] Screenshot uploaded: %s", result["secure_url"]
        )
        return result["secure_url"]

    except CloudinaryError as e:
        logger.error("[CLOUDINARY|UPLOAD] Upload failed: %s", e)
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e


def upload_media_file(file_storage, chat_slug: str) -> str:
    """
    Uploads a media file to Cloudinary.

    Images are converted to WebP; other files are stored as-is.

    :param file_storage: Werkzeug FileStorage object.
    :param chat_slug: Chat slug for organizing storage.
    :return: Cloudinary secure URL for uploaded file.
    :raises RuntimeError: If upload fails.
    """
    is_image = is_image_file(file_storage)
    original_name = file_storage.filename.rsplit(".", 1)[0]
    unique_suffix = uuid4().hex[:8]
    public_id = f"{original_name}_{unique_suffix}"
    folder = f"arcanum/chats/media/{chat_slug}"

    upload_options = {
        "folder": folder,
        "resource_type": "auto",
        "use_filename": False,
        "public_id": public_id,
        "overwrite": False
    }

    if is_image:
        upload_options.update({
            "format": "webp",
            "quality": "auto:good"
        })

    logger.debug("[CLOUDINARY|UPLOAD] Preparing media file '%s'", public_id)

    try:
        result = upload(file_storage, **upload_options)
        logger.info(
            "[CLOUDINARY|UPLOAD] Media file uploaded: %s", result["secure_url"]
        )
        return result["secure_url"]

    except CloudinaryError as e:
        logger.error("[CLOUDINARY|UPLOAD] Upload failed: %s", e)
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e
