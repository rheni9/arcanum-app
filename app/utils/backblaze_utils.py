"""
B2 S3 upload utilities for the Arcanum application.

Provides helper functions for uploading screenshots and other media
to Backblaze B2 via S3-compatible API with optional WebP conversion.
"""

import logging
from uuid import uuid4
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)


def convert_to_webp(file_storage) -> BytesIO:
    """
    Open uploaded image and convert to WebP in memory.

    :param file_storage: Werkzeug FileStorage object.
    :return: BytesIO containing WebP data.
    :raises UnidentifiedImageError: If file is not a valid image.
    """
    image = Image.open(file_storage)
    webp_bytes = BytesIO()
    image.save(webp_bytes, "WEBP", quality=80)
    webp_bytes.seek(0)
    return webp_bytes


def is_image_file(file_storage) -> bool:
    """
    Determine if uploaded file is an image based on extension.

    :param file_storage: Werkzeug FileStorage object.
    :return: True if file has image extension, False otherwise.
    """
    return file_storage.filename.lower().endswith((
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"
    ))


def upload_image(file_storage, chat_slug: str) -> str:
    """
    Upload chat image to B2 bucket as WebP.

    Stores image under the folder 'arcanum/chats/<chat_slug>/images'.

    :param file_storage: Werkzeug FileStorage object from form.
    :param chat_slug: Chat slug for organizing storage.
    :return: Public B2 URL for the uploaded image.
    :raises RuntimeError: If image is invalid or upload fails.
    """
    unique_suffix = uuid4().hex[:8]
    filename = f"image_{unique_suffix}.webp"
    key = f"arcanum/chats/{chat_slug}/images/{filename}"

    logger.debug("[B2|UPLOAD] Preparing image '%s'", key)

    try:
        webp_bytes = convert_to_webp(file_storage)

        # Upload using boto3 S3 client from current_app
        current_app.s3_client.upload_fileobj(
            webp_bytes,
            current_app.config["B2_S3_BUCKET_NAME"],
            key,
            ExtraArgs={"ContentType": "image/webp"}
        )
        logger.info("[B2|UPLOAD] Image uploaded: %s", key)

        # Return constructed public URL
        return (
            f"{current_app.config['B2_S3_ENDPOINT_URL']}/"
            f"{current_app.config['B2_S3_BUCKET_NAME']}/{key}"
        )

    except (UnidentifiedImageError, OSError) as e:
        logger.error("[B2|UPLOAD] Invalid image file: %s", e)
        raise RuntimeError(f"Invalid image file: {e}") from e
    except ClientError as e:
        logger.error("[B2|UPLOAD] B2 upload failed: %s", e)
        raise RuntimeError(f"B2 upload failed: {e}") from e


def upload_screenshot(file_storage, chat_slug: str, timestamp_str: str) -> str:
    """
    Upload screenshot to B2 bucket as WebP.

    Stores screenshot under the folder 'arcanum/chats/<chat_slug>/screenshots'.

    :param file_storage: Werkzeug FileStorage object from form.
    :param chat_slug: Chat slug for organizing storage.
    :param timestamp_str: Timestamp string (YYYYMMDD_HHMMSS).
    :return: Public B2 URL for the uploaded screenshot.
    :raises RuntimeError: If image is invalid or upload fails.
    """
    unique_suffix = uuid4().hex[:8]
    filename = f"screenshot_{timestamp_str}_{unique_suffix}.webp"
    key = f"arcanum/chats/{chat_slug}/screenshots/{filename}"

    logger.debug("[B2|UPLOAD] Preparing screenshot '%s'", key)

    try:
        webp_bytes = convert_to_webp(file_storage)

        # Upload using boto3 S3 client from current_app
        current_app.s3_client.upload_fileobj(
            webp_bytes,
            current_app.config["B2_S3_BUCKET_NAME"],
            key,
            ExtraArgs={"ContentType": "image/webp"}
        )
        logger.info("[B2|UPLOAD] Screenshot uploaded: %s", key)

        # Return constructed public URL
        return (
            f"{current_app.config['B2_S3_ENDPOINT_URL']}/"
            f"{current_app.config['B2_S3_BUCKET_NAME']}/{key}"
        )

    except (UnidentifiedImageError, OSError) as e:
        logger.error("[B2|UPLOAD] Invalid screenshot file: %s", e)
        raise RuntimeError(f"Invalid screenshot file: {e}") from e
    except ClientError as e:
        logger.error("[B2|UPLOAD] B2 upload failed: %s", e)
        raise RuntimeError(f"B2 upload failed: {e}") from e


def upload_media_file(file_storage, chat_slug: str) -> str:
    """
    Upload a media file to B2 bucket.

    Images are converted to WebP; other files are stored as-is.
    Stores media under the folder 'arcanum/chats/<chat_slug>/media'.

    :param file_storage: Werkzeug FileStorage object from form.
    :param chat_slug: Chat slug for organizing storage.
    :return: Public B2 URL for the uploaded file.
    :raises RuntimeError: If upload or conversion fails.
    """
    original_name = file_storage.filename.rsplit(".", 1)[0]
    unique_suffix = uuid4().hex[:8]

    if is_image_file(file_storage):
        filename = f"{original_name}_{unique_suffix}.webp"
        key = f"arcanum/chats/{chat_slug}/media/{filename}"
        logger.debug("[B2|UPLOAD] Preparing image file '%s'", key)

        try:
            webp_bytes = convert_to_webp(file_storage)

            current_app.s3_client.upload_fileobj(
                webp_bytes,
                current_app.config["B2_S3_BUCKET_NAME"],
                key,
                ExtraArgs={"ContentType": "image/webp"}
            )

            logger.info("[B2|UPLOAD] Image uploaded as WebP: %s", key)

        except (UnidentifiedImageError, OSError) as e:
            logger.error("[B2|UPLOAD] Invalid image file: %s", e)
            raise RuntimeError(f"Invalid image file: {e}") from e
        except ClientError as e:
            logger.error("[B2|UPLOAD] B2 upload failed: %s", e)
            raise RuntimeError(f"B2 upload failed: {e}") from e

    else:
        ext = file_storage.filename.rsplit(".", 1)[-1].lower()
        filename = f"{original_name}_{unique_suffix}.{ext}"
        key = f"arcanum/chats/{chat_slug}/media/{filename}"
        logger.debug("[B2|UPLOAD] Preparing non-image media file '%s'", key)

        try:
            current_app.s3_client.upload_fileobj(
                file_storage,
                current_app.config["B2_S3_BUCKET_NAME"],
                key,
                ExtraArgs={"ContentType": file_storage.mimetype}
            )
            logger.info("[B2|UPLOAD] Media file uploaded: %s", key)

        except ClientError as e:
            logger.error("[B2|UPLOAD] B2 upload failed: %s", e)
            raise RuntimeError(f"B2 upload failed: {e}") from e

    return (
        f"{current_app.config['B2_S3_ENDPOINT_URL']}/"
        f"{current_app.config['B2_S3_BUCKET_NAME']}/{key}"
    )


def generate_signed_s3_url(
    file_url: str,
    expires_in: int = 3600
) -> str:
    """
    Generate a signed URL for any stored B2 file.

    Works for screenshots, media, or other private objects.

    :param file_url: Full stored file URL from DB.
    :param expires_in: Expiration time in seconds.
    :return: Signed URL for temporary access.
    """
    if not file_url:
        return ""

    parsed = urlparse(file_url)
    key = parsed.path.lstrip("/").split("/", 1)[-1]  # remove /BUCKET_NAME/

    return current_app.s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": current_app.config["B2_S3_BUCKET_NAME"],
            "Key": key
        },
        ExpiresIn=expires_in
    )


def clean_url(url: str) -> str:
    """
    Remove query params from a URL for consistent comparison.

    :param url: Original URL with possible query string.
    :return: Cleaned URL without params.
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
