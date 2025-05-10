"""
User dashboard route for the Arcanum application.

Displays an overview panel after successful login.
Accessible only to authenticated users.
"""

from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard() -> str:
    """
    Display the main dashboard page for authenticated users.

    :returns: Rendered HTML content of the dashboard.
    :rtype: str
    """
    return render_template("dashboard.html")
