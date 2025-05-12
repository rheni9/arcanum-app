"""
Form utilities for cleaning and validating input fields.

This module provides helpers for processing raw form input data,
such as replacing empty strings with None and validating URLs.
"""

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def clean_form(data: dict) -> dict:
    """
    Return a copy of the form data dictionary where empty strings
    are replaced with None.

    :param data: Dictionary with raw form input values.
    :type data: dict
    :return: Cleaned dictionary with None instead of empty strings.
    :rtype: dict
    """
    return {k: (v.strip() if v.strip() else None) for k, v in data.items()}


def is_valid_url(url: str) -> bool:
    """
    Validate a URL to ensure it uses a valid HTTP(S) scheme.

    Supports only http and https protocols.
    Logs a warning if validation fails due to invalid format.

    :param url: Input URL string.
    :type url: str
    :return: True if URL has a valid scheme and network location,
             False otherwise.
    :rtype: bool
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except (TypeError, AttributeError) as e:
        logger.warning(
            "[VALIDATION] URL validation failed for '%s': %s",
            url, e
        )
        return False
