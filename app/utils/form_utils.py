"""
Form utilities for the Arcanum application.

Provides:
- helpers for cleaning raw form input,
- normalization of empty values to None,
- consistent handling of optional fields.
"""

from typing import Dict, Optional


def clean_form(data: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    """
    Clean raw form data by normalizing empty strings to None.

    For each input field:
    - strips leading/trailing whitespace,
    - replaces empty strings with None,
    - preserves actual values unchanged.

    :param data: Dictionary with raw form input values.
    :type data: Dict[str, Optional[str]]
    :return: Cleaned form data dictionary.
    :rtype: Dict[str, Optional[str]]
    """
    return {
        key: (value.strip() if value and value.strip() else None)
        for key, value in data.items()
    }
