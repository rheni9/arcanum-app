"""
Internationalization (i18n) utilities for the Arcanum application.

Provides helper tools for managing language and timezone selection.
It integrates with Flask-Babel to ensure consistent handling of
user-facing messages across the application.

It supports locale detection and selection based on session preferences
or request headers. A TranslatableMsg wrapper separates user-facing
translations from logging messages so that logs always remain in English.
A timezone accessor is also provided to ensure all displayed times use
the configured application timezone.

Note: English ("en") is internally mapped to British English ("en_GB").
"""

from flask import current_app, session, request
from flask_babel import _

LANG_MAP = {
    "en": "en_GB",
    "uk": "uk",
}


class TranslatableMsg(str):
    """
    A string wrapper that separates UI translations from log output.
    """
    @property
    def ui(self) -> str:
        """Return localized version of the message for user-facing output."""
        return _(self)

    @property
    def log(self) -> str:
        """Return the original English version of the message for logging."""
        return str(self)


def get_locale() -> str:
    """
    Determine the best matching locale for the current request.

    Checks the session for a stored language preference. If the stored
    language is supported, it is returned. Otherwise, attempts to match
    the best language from the request's Accept-Language headers.
    Falls back to the default locale if no match is found.

    :return: Locale code string (e.g., 'en_GB', 'uk').
    """
    langs = current_app.config.get("LANGUAGES", ["en"])
    lang = session.get("lang")

    if lang in langs:
        return LANG_MAP.get(lang, lang)

    best = request.accept_languages.best_match(langs)

    return (
        LANG_MAP.get(best, best)
        or current_app.config.get("DEFAULT_LOCALE", "en_GB")
    )


def get_timezone() -> str:
    """
    Return timezone string for Babel.

    This ensures that all formatted times in the UI are displayed
    in the configured application timezone.

    :return: Timezone name string.
    """
    return current_app.config.get("DEFAULT_TZ_NAME", "Europe/Kyiv")
