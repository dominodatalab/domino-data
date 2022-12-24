"""Feature store logging setup tests."""


def test_logger_initialize_properly(monkeypatch):
    """Ensure logger initialize without errors."""
    monkeypatch.delenv("HOME")

    from domino_data._feature_store import logging  # pylint: disable=import-outside-toplevel

    logging.get_feature_store_logger()
