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

import app


@pytest.mark.parametrize(
    "invalid_script",
    [
        "../app.py",
        "../../etc/passwd",
        "ps_scripts/../../app.py",
        "/etc/passwd",
        "../../Windows/System32/drivers/etc/hosts",
    ],
)
def test_run_powershell_script_path_traversal(invalid_script):
    """Test that various path traversal attempts are blocked."""
    # Reset last_script_execution to 0 to bypass rate limit
    with patch("app.st.session_state", {"last_script_execution": 0}), patch(
        "app.ALLOWED_SCRIPTS", {invalid_script}
    ):
        result = app.run_powershell_script(invalid_script)

    assert result == "Error: Invalid script path requested."


def test_run_powershell_script_valid_path():
    """Test that valid script paths are allowed (even if file doesn't exist for this test)."""
    valid_script = "get_startup_processes.ps1"

    with patch("app.st.session_state", {"last_script_execution": 0}), patch(
        "app.os.path.exists", return_value=True
    ), patch("app.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Output", stderr="", returncode=0)
        result = app.run_powershell_script(valid_script)

    assert "Error: Invalid script path requested." not in result


def test_run_powershell_script_sibling_directory_traversal():
    """Test that sibling directory traversal attempts are blocked."""
    # Mock SCRIPTS_DIR to a known value for this test
    base_path = os.path.abspath("ps_scripts")

    with patch("app.SCRIPTS_DIR", base_path):
        # This path might start with base_path if we are not careful
        # e.g. /app/ps_scripts_dangerous starts with /app/ps_scripts
        # But our code adds a trailing slash to base_dir, which should prevent this.

        sibling_script = "../ps_scripts_dangerous/attack.ps1"

        with patch("app.st.session_state", {"last_script_execution": 0}), patch(
            "app.ALLOWED_SCRIPTS", {sibling_script}
        ):
            result = app.run_powershell_script(sibling_script)

        assert result == "Error: Invalid script path requested."
