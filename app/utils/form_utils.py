"""
Form utilities for cleaning raw input fields.

This module provides helpers for processing form data,
such as replacing empty strings with None.
"""


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
