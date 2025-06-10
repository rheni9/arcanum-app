"""
Dashboard route for the Arcanum application.

Provides the authenticated user dashboard page with navigation to key sections.
"""

import logging
from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)


@dashboard_bp.route("/")
def dashboard() -> str:
    """
    Render the dashboard page.

    :return: Rendered dashboard HTML page.
    """
    logger.info("[DASHBOARD|VIEW] Dashboard page displayed.")
    return render_template("dashboard.html")
