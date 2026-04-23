"""Logging setup for CLI commands."""

from __future__ import annotations

import logging


def configure_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
    return logging.getLogger("documind")
