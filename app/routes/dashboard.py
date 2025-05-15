"""
Dashboard route for the Arcanum application.

Provides the user dashboard page for authenticated users.
"""

import logging
from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)


@dashboard_bp.route("/")
def dashboard() -> str:
    """
    Render the dashboard page.

    :returns: Rendered dashboard HTML page.
    :rtype: str
    """
    logger.info("[DASHBOARD|VIEW] Dashboard page displayed.")
    return render_template("dashboard.html")
