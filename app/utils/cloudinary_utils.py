"""
Cloudinary upload utilities for the Arcanum application.

Provides helper functions for uploading screenshots
to Cloudinary with WebP conversion and quality control.
"""

from cloudinary.uploader import upload
from cloudinary.exceptions import Error as CloudinaryError


def upload_screenshot(file_storage) -> str:
    """
    Upload screenshot to Cloudinary as WebP with controlled quality.

    :param file_storage: Werkzeug FileStorage object from form.
    :return: Cloudinary image URL in WebP format.
    :raises RuntimeError: If upload fails.
    """
    try:
        result = upload(
            file_storage,
            folder="arcanum/screenshots",
            resource_type="image",
            format="webp",
            quality="auto:good"
        )
        return result["secure_url"]
    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e
