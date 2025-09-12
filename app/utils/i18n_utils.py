"""
Internationalization (i18n) utilities for the Arcanum application.

Provides helper functions for locale detection and selection,
integrated with Flask-Babel. These utilities ensure consistent
handling of language preferences across the application, including
session overrides and request header negotiation.
"""

from flask import current_app, session, request


def get_locale() -> str:
    """
    Determine the best matching locale for the current request.

    Checks the session for a stored language preference. If the stored
    language is supported, it is returned. Otherwise, attempts to match
    the best language from the request's Accept-Language headers. Falls
    back to the default locale if no match is found.

    :return: Locale code string (e.g., 'en', 'uk').
    """
    langs = current_app.config.get("LANGUAGES", ["en"])
    lang = session.get("lang")

    if lang in langs:
        return lang

    return (
        request.accept_languages.best_match(langs)
        or current_app.config.get("DEFAULT_LOCALE", "en")
    )
