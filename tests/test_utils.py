import os
import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock dependencies before importing app
st_mock = MagicMock()
st_mock.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
st_mock.sidebar.__enter__.return_value = MagicMock()


def mock_get(key, default=None):
    if key == "messages":
        return []
    return 0


st_mock.session_state.get.side_effect = mock_get

sys.modules["streamlit"] = st_mock
sys.modules["litellm"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from app import sanitize_log_input


def test_sanitize_log_input_basic():
    """Test basic sanitization of newlines and carriage returns."""
    assert sanitize_log_input("hello\nworld") == "hello world"
    assert sanitize_log_input("hello\rworld") == "helloworld"
    assert sanitize_log_input("hello\r\nworld") == "hello world"


def test_sanitize_log_input_multiple():
    """Test sanitization of multiple occurrences."""
    assert sanitize_log_input("\n\n\r\r") == "  "
    assert sanitize_log_input("line1\nline2\r\nline3") == "line1 line2 line3"


def test_sanitize_log_input_non_string():
    """Test that non-string inputs are converted and sanitized."""
    assert sanitize_log_input(123) == "123"
    assert sanitize_log_input(None) == "None"

    class MockError(Exception):
        def __str__(self):
            return "Error\nDetails"

    assert sanitize_log_input(MockError()) == "Error Details"


def test_sanitize_log_input_no_change():
    """Test that strings without newlines or carriage returns are unchanged."""
    assert sanitize_log_input("clean string") == "clean string"
    assert sanitize_log_input("") == ""
