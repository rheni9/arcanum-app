"""
Language routes for the Arcanum application.

Provides an endpoint for setting the user's language preference
and storing it in the session, with redirection back to the
previous page or the home page.
"""

import logging
from flask import Blueprint, redirect, request, session, url_for, current_app

lang_bp = Blueprint("lang", __name__, url_prefix="/lang")
logger = logging.getLogger(__name__)


@lang_bp.route("/set/<lang_code>")
def set_language(lang_code: str):
    """
    Set the user language preference.

    Stores the selected language in the session if it is supported.
    Redirects the user back to the referring page or the home page.

    :param lang_code: Language code requested by the user.
    :return: Redirect response to the previous or home page.
    """
    supported = current_app.config.get("LANGUAGES", ["en"])
    if lang_code in supported:
        session["lang"] = lang_code
        logger.debug("[LANG|SET] Language changed to '%s'.", lang_code)
    else:
        logger.warning("[LANG|SET] Unsupported language code '%s'.", lang_code)

    return redirect(request.referrer or url_for("home.home"))
