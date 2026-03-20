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


def test_run_powershell_script_environment_scrubbing():
    """Test that sensitive environment variables are correctly scrubbed."""
    valid_script = "get_startup_processes.ps1"

    mock_environ = {
        "SAFE_VAR": "safe_value",
        "PATH": "/usr/bin:/bin",
        "GOOGLE_API_KEY": "secret_key_1",
        "AWS_SECRET_ACCESS_KEY": "secret_key_2",
        "GITHUB_TOKEN": "secret_key_3",
        "DB_PASSWORD": "secret_key_4",
        "USER_CREDENTIALS": "secret_key_5",
        "SOME_API_KEY_HERE": "secret_key_6",
    }

    with patch("app.st.session_state", {"last_script_execution": 0}), patch(
        "app.os.path.exists", return_value=True
    ), patch("app.os.environ", mock_environ), patch("app.subprocess.run") as mock_run:

        mock_run.return_value = MagicMock(stdout="Output", stderr="", returncode=0)
        app.run_powershell_script(valid_script)

        # Verify subprocess.run was called
        mock_run.assert_called_once()

        # Get the 'env' argument passed to subprocess.run
        called_env = mock_run.call_args.kwargs.get("env")

        assert called_env is not None
        assert "SAFE_VAR" in called_env
        assert "PATH" in called_env
        assert "GOOGLE_API_KEY" not in called_env
        assert "AWS_SECRET_ACCESS_KEY" not in called_env
        assert "GITHUB_TOKEN" not in called_env
        assert "DB_PASSWORD" not in called_env
        assert "USER_CREDENTIALS" not in called_env
        assert "SOME_API_KEY_HERE" not in called_env


def test_sanitize_diagnostic_output_case_insensitive():
    """Test that XML tag breakout sanitization is case-insensitive."""
    test_cases = [
        ("<diagnostic_output>", "_diagnostic_output_"),
        ("</diagnostic_output>", "_/diagnostic_output_"),
        ("<DiAgNoStIc_OuTpUt>", "_diagnostic_output_"),
        ("</DIAGNOSTIC_OUTPUT>", "_/diagnostic_output_"),
        ("some <diagnostic_output> text", "some _diagnostic_output_ text"),
        ("text </DiAgNoStIc_OuTpUt> more", "text _/diagnostic_output_ more"),
        ("clean text", "clean text"),
    ]
    for input_text, expected_text in test_cases:
        assert app.sanitize_diagnostic_output(input_text) == expected_text
