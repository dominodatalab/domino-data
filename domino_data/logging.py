"""Logging module."""

import os
import sys
import tempfile

from loguru import logger as _logger

LOGFILE_LOCATION = "domino_logs/data_api.log"


def getsink():
    """Return log sink location."""
    return f"{tempfile.gettempdir()}/{LOGFILE_LOCATION}"


def getlogger():
    """Configure and return a logger."""
    _logger.configure(
        handlers=[
            {
                "format": "[{time}] {message}",
                "sink": getsink(),
                "rotation": "1 day",
                "retention": 7,
                "enqueue": True,
                "serialize": True,
            },
            {
                "format": "[{time}] {message}",
                "sink": sys.stdout,
                "filter": "domino_data._feature_store",
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
