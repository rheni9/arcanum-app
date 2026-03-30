"""
Health check routes for the Arcanum application.

Provides a lightweight endpoint used by infrastructure to verify that
the application instance is running and able to respond to HTTP requests.
"""

import logging
from flask import Blueprint, jsonify, Response

health_bp = Blueprint("health", __name__)
logger = logging.getLogger(__name__)


@health_bp.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    """
    Health check endpoint.

    Returns a simple JSON response indicating that the application
    is alive. This endpoint is used by external services (e.g., Koyeb)
    to determine whether the instance is ready to receive traffic.

    :return: Tuple of (JSON response, HTTP 200 status).
    """
    logger.debug("[HEALTH|CHECK] Health check endpoint called.")
    return jsonify({"status": "ok"}), 200
