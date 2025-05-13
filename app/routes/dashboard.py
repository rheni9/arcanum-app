"""
Dashboard route for the Arcanum application.

Provides the user dashboard page.
Requires authentication (checked via global hooks).
Displays navigation links to main sections.
"""

import logging
from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)


@dashboard_bp.route("/")
def dashboard() -> str:
    """
    Render the dashboard for authenticated users.

    :returns: Rendered dashboard HTML page.
    :rtype: str
    """
    logger.info("[DASHBOARD|VIEW] Dashboard displayed.")
    return render_template("dashboard.html")
