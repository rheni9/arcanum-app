"""
Public landing page route for the Arcanum application.

Displays the homepage with general information before login.
Accessible without authentication.
"""

from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home() -> str:
    """
    Display the main landing page of the application.

    :returns: Rendered HTML content for the homepage.
    :rtype: str
    """
    return render_template("index.html")
