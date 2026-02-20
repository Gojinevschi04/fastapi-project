import logging
from unittest.mock import patch

import pytest

from app.core.logging import get_logger, setup_logging


def test_setup_logging_creates_logger() -> None:
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "api"


def test_setup_logging_creates_handlers() -> None:
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 5


def test_setup_logging_log_level_string() -> None:
    with patch("app.core.logging.settings") as mock_settings:
        mock_settings.LOG_LEVEL = "DEBUG"
        logger = setup_logging()
        assert logger.level == logging.DEBUG


def test_setup_logging_log_level_int() -> None:
    with patch("app.core.logging.settings") as mock_settings:
        mock_settings.LOG_LEVEL = logging.WARNING
        logger = setup_logging()
        assert logger.level == logging.WARNING


def test_get_logger_default_name() -> None:
    logger = get_logger()
    assert logger.name == "api"


def test_get_logger_custom_name() -> None:
    logger = get_logger("custom")
    assert logger.name == "custom"
