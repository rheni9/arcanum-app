"""
Home route for the Arcanum application.

Provides the public landing page and application access notice.
"""

import logging
from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)
logger = logging.getLogger(__name__)


@home_bp.route("/")
def home() -> str:
    """
    Render the landing page.

    :return: Rendered homepage HTML.
    """
    logger.info("[HOME|VIEW] Landing page displayed.")
    return render_template("index.html")
