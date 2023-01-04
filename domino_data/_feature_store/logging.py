"""Dedicated Feature Store Logging module."""

import os
import sys

from loguru import logger as _logger


def get_feature_store_logger():
    """Configure and return a logger."""
    _logger.configure(
        handlers=[
            {
                "format": "[{time}] {message}",
                "sink": sys.stdout,
                "enqueue": True,
            },
        ],
        extra={
            "ip": os.getenv("DOMINO_NODE_IP"),
            "project": os.getenv("DOMINO_PROJECT_NAME"),
            "run_id": os.getenv("DOMINO_RUN_ID"),
            "user": os.getenv("DOMINO_STARTING_USERNAME"),
        },
    )
    return _logger


logger = get_feature_store_logger()
