import sys
from unittest.mock import MagicMock

# Mock necessary modules
st = MagicMock()
st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
# Initialize session_state as a mock that can have attributes assigned to it
st.session_state = MagicMock()
# Specifically handle things that might be accessed during import
st.session_state.messages = []
st.session_state.diagnostic_output = ""


# Handle session_state.get for the rate limit check
def mock_get(key, default=None):
    if key == "messages":
        return []
    return 0


st.session_state.get.side_effect = mock_get
sys.modules["streamlit"] = st

sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["litellm"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

import unittest
from unittest.mock import patch
import app


class TestSecurityWhitelist(unittest.TestCase):

    def setUp(self):
        # Setup mock session state
        app.st.session_state = MagicMock()
        app.st.session_state.get.side_effect = mock_get

    @patch("app.audit_logger")
    def test_run_whitelisted_script(self, mock_logger):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="Success", stderr="", returncode=0)

            for script in app.ALLOWED_SCRIPTS:
                # Reset rate limit in session state mock
                app.st.session_state.get.side_effect = mock_get
                result = app.run_powershell_script(script)
                self.assertNotEqual(
                    result, "Error: Unauthorized script execution requested."
                )

    @patch("app.audit_logger")
    def test_run_non_whitelisted_script(self, mock_logger):
        bad_scripts = ["malicious.ps1", "../outside.ps1", "ls", "Get-Process"]

        for script in bad_scripts:
            # We don't want rate limit to hit here, so reset it
            app.st.session_state.get.side_effect = mock_get
            result = app.run_powershell_script(script)
            self.assertEqual(result, "Error: Unauthorized script execution requested.")
            mock_logger.warning.assert_called_with(
                f"Unauthorized script execution attempt: {script}"
            )


if __name__ == "__main__":
    unittest.main()
