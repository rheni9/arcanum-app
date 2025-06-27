"""
Cloudinary upload utilities for the Arcanum application.

Provides helper functions for uploading screenshots
to Cloudinary with WebP conversion and quality control.
"""

from uuid import uuid4
from cloudinary.uploader import upload
from cloudinary.exceptions import Error as CloudinaryError


def upload_screenshot(file_storage, chat_slug: str, timestamp_str: str) -> str:
    """
    Upload screenshot to Cloudinary as WebP with controlled quality.

    Stores image under the folder 'arcanum/screenshots/<chat_slug>'.

    :param file_storage: Werkzeug FileStorage object from form.
    :param chat_slug: Slug of the chat to organize images.
    :param timestamp_str: Timestamp string from form (YYYYMMDD_HHMMSS).
    :return: Cloudinary image URL in WebP format.
    :raises RuntimeError: If upload fails.
    """
    unique_suffix = uuid4().hex[:8]
    public_id = f"screenshot_{timestamp_str}_{unique_suffix}"
    try:
        result = upload(
            file_storage,
            folder=f"arcanum/chats/screenshots/{chat_slug}",
            public_id=public_id,
            resource_type="image",
            format="webp",
            quality="auto:good",
            overwrite=False
        )
        return result["secure_url"]
    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e


def is_image_file(file_storage) -> bool:
    """
    Determine if uploaded file is an image by extension.

    :param file_storage: FileStorage object.
    :return: True if file has image extension, False otherwise.
    """
    return file_storage.filename.lower().endswith((
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"
    ))


def upload_media_file(file_storage, chat_slug: str) -> str:
    """
    Uploads any media file to Cloudinary, preserving its format and filename.

    :param file_storage: FileStorage object from form.
    :param chat_slug: Slug to organize uploads.
    :return: URL to the uploaded media.
    :raises RuntimeError: If upload fails.
    """
    try:
        is_image = is_image_file(file_storage)
        original_filename = file_storage.filename.rsplit(".", 1)[0]
        unique_suffix = uuid4().hex[:8]
        public_id = f"{original_filename}_{unique_suffix}"

        upload_options = {
            "folder": f"arcanum/chats/media/{chat_slug}",
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

        result = upload(file_storage, **upload_options)

        return result["secure_url"]

    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e
