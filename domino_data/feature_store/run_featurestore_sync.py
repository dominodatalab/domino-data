"""Containing script to sync feature store from feast to domino"""
import sys

from ..logging import logger
from .featurestore_sync import feature_store_sync

if __name__ == "__main__":
    try:
        feature_store_sync()
    except Exception as e:
        logger.exception(e)
        sys.exit(-1)
