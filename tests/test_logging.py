"""Logging setup tests."""


def test_logger_initialize_properly(monkeypatch):
    """Ensure logger initialize without errors."""
    monkeypatch.delenv("HOME")

    from domino_data import logging  # pylint: disable=import-outside-toplevel

    logging.getlogger()
