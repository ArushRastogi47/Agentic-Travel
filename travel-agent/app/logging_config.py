"""
Application-wide logging setup using rich for pretty output.
"""

from __future__ import annotations

import logging
import sys

from rich.logging import RichHandler

from app.config import LOG_LEVEL


def setup_logging() -> logging.Logger:
    """Configure and return the root application logger."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_path=False,
                markup=True,
            )
        ],
        force=True,
    )
    logger = logging.getLogger("travel_agent")
    logger.setLevel(LOG_LEVEL)
    return logger


logger = setup_logging()
