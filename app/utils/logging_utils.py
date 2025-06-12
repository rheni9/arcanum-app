"""
Logging configuration utilities for the Arcanum application.

Configures global logging with unified formatting for both file and console
outputs. Enables colorized log levels for readability during development.
"""

import os
import sys
import logging
from colorlog import ColoredFormatter


def configure_logging(level: str | None = None) -> None:
    """
    Configure global logging for the Arcanum application.

    Sets up file and console handlers with unified formatting. Detects
    log level from the parameter, or the LOG_LEVEL environment variable,
    or uses DEBUG by default.
    Clears existing handlers to avoid duplicate logs on re-configuration.

    :param level: Explicit log level as a string (e.g. "INFO"). Overrides env.
    """

    # Choose the log level
    if level is not None:
        log_level_source = "param"
    elif os.getenv("LOG_LEVEL"):
        log_level_source = "env"
    else:
        log_level_source = "default"

    log_level = (
        level or
        os.getenv("LOG_LEVEL", None) or
        "DEBUG"
    )
    log_level = log_level.upper()
    level_int = getattr(logging, log_level, logging.DEBUG)

    # Remove all existing handlers
    root_logger = logging.getLogger()
    while root_logger.handlers:
        root_logger.handlers.pop()

    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "app.log")

    # Configure file handler
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Configure console handler with colors
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

    # Apply global configuration
    logging.basicConfig(
        level=level_int,
        handlers=[file_handler, console_handler]
    )

    # Add a warning if the default is used
    if log_level_source == "default":
        logging.warning(
            "[LOG|CONFIG] LOG_LEVEL is not set. "
            "Using default log level: DEBUG"
        )

    # Suppress noisy Werkzeug logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
