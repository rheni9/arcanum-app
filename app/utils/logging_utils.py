"""
Logging configuration utility for the Arcanum application.

Ensures that logs are written both to file (logs/app.log) and console output,
with consistent formatting across the application.
"""

import os
import sys
import logging
from colorlog import ColoredFormatter


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure application-wide logging with both file and console output.

    :param level: Logging level (e.g., DEBUG, INFO)
    :type level: int
    """
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "app.log")

    # ======= FORMATTERS =======
    # Standard file formatter
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Colored formatter for console
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

    # ======= ROOT LOGGER SETUP =======
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler]
    )

    # Suppress overly verbose logs from Werkzeug/Flask
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
