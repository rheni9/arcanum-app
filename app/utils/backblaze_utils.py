"""
B2 S3 upload utilities for the Arcanum application.

Provides helper functions for uploading screenshots, chat images,
and other media to Backblaze B2 via S3-compatible API.
Supports optional WebP conversion and ordering with counters.
"""

import logging
from uuid import uuid4
from urllib.parse import urlparse
from io import BytesIO
from werkzeug.datastructures import FileStorage
from PIL import Image, UnidentifiedImageError
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)


def convert_to_webp(file_storage: FileStorage) -> BytesIO:
    """
    Open uploaded image and convert it to WebP format in memory.

    :param file_storage: Werkzeug FileStorage object.
    :return: BytesIO containing WebP data.
    :raises UnidentifiedImageError: If file is not a valid image.
    """
    image = Image.open(file_storage)
    webp_bytes = BytesIO()
    image.save(webp_bytes, "WEBP", quality=80)
    webp_bytes.seek(0)
    return webp_bytes


def is_image_file(file_storage: FileStorage) -> bool:
    """
    Determine if an uploaded file is an image based on its extension.

    :param file_storage: Werkzeug FileStorage object.
    :return: True if file has image extension, False otherwise.
    """
    return file_storage.filename.lower().endswith((
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"
    ))


def upload_generic_webp(
    file_storage: FileStorage,
    bucket: str,
    base_path: str,
    prefix: str,
    filename_pattern: str
) -> str:
    """
    Upload a WebP image with counter and UUID to B2 bucket.

    Handles counting existing files to maintain order.

    :param file_storage: Werkzeug FileStorage object.
    :param bucket: B2 bucket name.
    :param base_path: Folder path inside the bucket.
    :param prefix: Prefix to list existing objects for counting.
    :param filename_pattern: Pattern with placeholders for counter and UUID.
    :return: Public B2 URL for the uploaded file.
    :raises RuntimeError: If upload fails.
    """
    s3_client = current_app.s3_client

    logger.debug("[B2|UPLOAD] Listing objects with prefix: %s", prefix)
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        existing = response.get("Contents", [])
        count = len(existing) + 1
        counter = f"{count:02d}"

    except ClientError as e:
        logger.error("[B2|UPLOAD] Failed to list objects: %s", e)
        raise RuntimeError(f"B2 listing failed: {e}") from e

    unique_suffix = uuid4().hex[:8]
    filename = filename_pattern.format(counter=counter, uuid=unique_suffix)
    key = f"{base_path}{filename}"

    logger.debug("[B2|UPLOAD] Preparing WebP '%s'", key)

    try:
        webp_bytes = convert_to_webp(file_storage)

        s3_client.upload_fileobj(
            webp_bytes,
            bucket,
            key,
            ExtraArgs={"ContentType": "image/webp"}
        )
        logger.info("[B2|UPLOAD] Uploaded: %s", key)

        return (
            f"{current_app.config['B2_S3_ENDPOINT_URL']}/"
            f"{bucket}/{key}"
        )

    except (UnidentifiedImageError, OSError) as e:
        logger.error("[B2|UPLOAD] Invalid image file: %s", e)
        raise RuntimeError(f"Invalid image file: {e}") from e
    except ClientError as e:
        logger.error("[B2|UPLOAD] B2 upload failed: %s", e)
        raise RuntimeError(f"B2 upload failed: {e}") from e


def upload_image(file_storage: FileStorage, chat_slug: str) -> str:
    """
    Upload chat image with counter and UUID to B2 bucket.

    Stores image under 'arcanum/chats/<chat_slug>/images/'.

    :param file_storage: Werkzeug FileStorage object.
    :param chat_slug: Chat slug for folder structure.
    :return: Public B2 URL.
    """
    bucket = current_app.config["B2_S3_BUCKET_NAME"]
    base_path = f"arcanum/chats/{chat_slug}/images/"
    prefix = f"{base_path}image_"
    pattern = "image_{counter}_{uuid}.webp"

    return upload_generic_webp(
        file_storage, bucket, base_path, prefix, pattern
    )


def upload_screenshot(
    file_storage: FileStorage,
    chat_slug: str,
    timestamp_str: str
) -> str:
    """
    Upload screenshot with timestamp, counter, and UUID to B2 bucket.

    Stores under 'arcanum/chats/<chat_slug>/screenshots/'.

    :param file_storage: Werkzeug FileStorage object.
    :param chat_slug: Chat slug for folder structure.
    :param timestamp_str: Timestamp string (YYYYMMDD_HHMMSS).
    :return: Public B2 URL.
    """
    bucket = current_app.config["B2_S3_BUCKET_NAME"]
    base_path = f"arcanum/chats/{chat_slug}/screenshots/"
    prefix = f"{base_path}screenshot_{timestamp_str}_"
    pattern = f"screenshot_{timestamp_str}_{{counter}}_{{uuid}}.webp"

    return upload_generic_webp(
        file_storage, bucket, base_path, prefix, pattern
    )


def upload_media_file(file_storage: FileStorage, chat_slug: str) -> str:
    """
    Upload a media file to B2 bucket.

    Images are converted to WebP; other files are stored as-is.
    Media files are stored under 'arcanum/chats/<chat_slug>/media/'.

    :param file_storage: Werkzeug FileStorage object.
    :param chat_slug: Chat slug for folder structure.
    :return: Public B2 URL for the uploaded file.
    :raises RuntimeError: If upload or conversion fails.
    """
    bucket = current_app.config["B2_S3_BUCKET_NAME"]
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
                bucket,
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
                bucket,
                key,
                ExtraArgs={"ContentType": file_storage.mimetype}
            )
            logger.info("[B2|UPLOAD] Media file uploaded: %s", key)

        except ClientError as e:
            logger.error("[B2|UPLOAD] B2 upload failed: %s", e)
            raise RuntimeError(f"B2 upload failed: {e}") from e

    return (
        f"{current_app.config['B2_S3_ENDPOINT_URL']}/"
        f"{bucket}/{key}"
    )


def generate_signed_s3_url(
    file_url: str,
    expires_in: int = 3600
) -> str:
    """
    Generate a signed URL for any stored B2 file.

    Works for screenshots, images, or other private objects.

    :param file_url: Full stored file URL from database.
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
