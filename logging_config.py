"""
logging_config.py
Central logging setup. All API requests, responses, and errors are written
to trading_bot.log (in the project root) as well as printed to console.
"""

import logging
import os

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading_bot.log")

_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, configuring handlers on first call."""
    _configure_root_logger()
    return logging.getLogger(name)
