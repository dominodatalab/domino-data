"""Logging module."""

import os

from loguru import logger as _logger

LOGFILE_LOCATION = "$HOME/.logs/domino_data.log"


def getlogger():
    """Configure and return a logger."""
    sink = os.path.expandvars(LOGFILE_LOCATION)
    _logger.configure(
        handlers=[
            {
                "format": "[{time}] {message}",
                "sink": sink,
                "rotation": "1 day",
                "retention": 7,
                "enqueue": True,
                "serialize": True,
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


logger = getlogger()
