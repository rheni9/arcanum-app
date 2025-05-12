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
    Render the user dashboard after successful login.

    Displays an overview panel accessible to authenticated users.

    :returns: Rendered HTML content of the dashboard.
    :rtype: str
    """
    return render_template("dashboard.html")
