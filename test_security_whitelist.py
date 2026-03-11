import sys
from unittest.mock import MagicMock

# Mock necessary modules
st = MagicMock()
st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
# Initialize session_state as a dictionary-like object that can have attributes assigned to it
class MockSessionState(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)
    def __setattr__(self, key, value):
        self[key] = value

st.session_state = MockSessionState()
st.session_state['messages'] = []
st.session_state['diagnostic_output'] = ""
sys.modules['streamlit'] = st

sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['litellm'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import unittest
from unittest.mock import patch
import app

class TestSecurityWhitelist(unittest.TestCase):

    def setUp(self):
        # Setup mock session state
        app.st.session_state = MockSessionState()

    @patch('app.audit_logger')
    def test_run_whitelisted_script(self, mock_logger):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="Success", stderr="", returncode=0)

            for script in app.ALLOWED_SCRIPTS:
                # Reset rate limit in session state
                app.st.session_state['last_script_execution'] = 0
                result = app.run_powershell_script(script)
                self.assertNotEqual(result, "Error: Unauthorized script execution requested.")

    @patch('app.audit_logger')
    def test_run_non_whitelisted_script(self, mock_logger):
        bad_scripts = ["malicious.ps1", "../outside.ps1", "ls", "Get-Process"]

        for script in bad_scripts:
            # We don't want rate limit to hit here, so reset it
            app.st.session_state['last_script_execution'] = 0
            result = app.run_powershell_script(script)
            self.assertEqual(result, "Error: Unauthorized script execution requested.")
            mock_logger.warning.assert_called_with(f"Unauthorized script execution attempt: {script}")

if __name__ == '__main__':
    unittest.main()
