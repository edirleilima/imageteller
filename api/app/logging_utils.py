"""Lightweight logging helper."""
from __future__ import annotations

import logging

_logger = logging.getLogger("imageteller")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


def write_to_log(message: str) -> None:
    _logger.info(message)


def log_error(message: str) -> None:
    _logger.error(message)
