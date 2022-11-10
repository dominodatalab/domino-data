"""Containing script to sync feature store from feast to domino"""
import argparse
import sys

from ..logging import logger
from .sync import feature_store_sync

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run feature store sync.")
    parser.add_argument(
        "-i",
        "--id",
        metavar="FEATURE_STORE_ID",
        type=str,
        required=True,
        help="the domino feature store id",
    )
    parser.add_argument(
        "-p",
        "--path",
        metavar="FEAST_REPO_PATH",
        type=str,
        required=False,
        help="the feature store git repo path",
    )
    parser.add_argument(
        "-b",
        "--branch",
        metavar="FEAST_REPO_BRANCH",
        type=str,
        required=False,
        help="the feature store git repo branch",
    )

    parser.add_argument(
        "-r",
        "--retry",
        metavar="MAX_LOCK_RETRY_COUNT",
        type=int,
        required=False,
        help="the maximum feature store lock retry count",
    )
    args = parser.parse_args()

    try:
        feature_store_sync(args.id, args.path, args.branch, args.retry)
    except Exception as e:
        logger.exception(e)
        sys.exit(-1)
