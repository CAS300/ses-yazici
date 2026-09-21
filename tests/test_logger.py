import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import app_logger


def test_get_log_path(monkeypatch, tmp_path):
    # Default path is app.log in project root
    default_path = app_logger.get_log_path()
    assert default_path.name == "app.log"

    # Environment variable override
    custom = tmp_path / "custom.log"
    monkeypatch.setenv("SES_YAZICI_LOG_PATH", str(custom))
    assert app_logger.get_log_path() == custom


def test_secret_filter_redaction():
    filt = app_logger.SecretFilter()
    
    # Bearer token
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Authorization: Bearer sk-9router-secret-token-123456",
        args=(),
        exc_info=None,
    )
    filt.filter(record)
    assert "sk-9router-secret-token-123456" not in record.msg
    assert "[REDACTED]" in record.msg
    assert "Authorization: Bearer [REDACTED]" in record.msg


def test_secret_filter_api_key_redaction():
    filt = app_logger.SecretFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Connecting with api_key=super_secret_key_abc to https://api.9router.com",
        args=(),
        exc_info=None,
    )
    filt.filter(record)
    assert "super_secret_key_abc" not in record.msg
    assert "[REDACTED]" in record.msg


def test_setup_logging_creates_file_and_logs(tmp_path):
    log_file = tmp_path / "test_app.log"
    logger = app_logger.setup_logging(log_path=log_file, level=logging.DEBUG)
    test_logger = app_logger.get_logger("test_module")
    
    test_logger.debug("Debug mesajı 123")
    test_logger.info("Bearer my-secret-auth-token")
    
    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()
    
    content = log_file.read_text(encoding="utf-8")
    assert "Debug mesajı 123" in content
    assert "[test_module]" in content
    assert "my-secret-auth-token" not in content
    assert "Bearer [REDACTED]" in content


def test_setup_logging_rotating_handler(tmp_path):
    log_file = tmp_path / "rotating.log"
    app_logger.setup_logging(log_path=log_file)
    
    # Check that a RotatingFileHandler exists on root logger
    from logging.handlers import RotatingFileHandler
    root = logging.getLogger()
    rotating_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    assert len(rotating_handlers) >= 1
    handler = rotating_handlers[0]
    assert handler.maxBytes == 5 * 1024 * 1024
    assert handler.backupCount == 3


def test_open_log_file_existing(tmp_path):
    log_file = tmp_path / "existing.log"
    log_file.write_text("hello log", encoding="utf-8")
    
    with patch("os.startfile", create=True) as mock_startfile:
        app_logger.open_log_file(log_path=log_file)
        mock_startfile.assert_called_once_with(str(log_file))


def test_open_log_file_creates_if_missing(tmp_path):
    log_file = tmp_path / "missing.log"
    assert not log_file.exists()
    
    with patch("os.startfile", create=True) as mock_startfile:
        app_logger.open_log_file(log_path=log_file)
        assert log_file.exists()
        mock_startfile.assert_called_once_with(str(log_file))
