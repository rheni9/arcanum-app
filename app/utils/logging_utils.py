"""
Logging configuration for the Arcanum application.

Provides consistent formatting for file and console outputs,
with colorized levels for readability in development.
"""

import os
import sys
import logging
from colorlog import ColoredFormatter


def configure_logging(level: int = None) -> None:
    """
    Configure global logging for Arcanum.

    Determines log level from:
    - environment variable LOG_LEVEL,
    - function argument,
    - defaults to DEBUG.

    :param level: Explicit log level (overrides env).
    :type level: int | None
    """
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
        level = getattr(logging, env_level, logging.DEBUG)

    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "app.log")

    # ===== File Handler =====
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # ===== Console Handler with Colors =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(
        fmt=(
            "%(asctime)s "
            "%(log_color)s[%(levelname)s]%(reset)s "
            "%(cyan)s%(name)s%(reset)s: "
            "%(message_log_color)s%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG":    "white",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        },
        secondary_log_colors={
            "message": {
                "DEBUG": "white",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red"
            }
        },
        style="%",
    ))

    # ===== Root Logger =====
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler]
    )

    # Suppress noisy Werkzeug logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
