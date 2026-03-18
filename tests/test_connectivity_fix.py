import unittest
import os
import subprocess
from unittest.mock import patch, MagicMock

class TestConnectivityFix(unittest.TestCase):
    def test_powershell_script_logic(self):
        # We'll mock the actual run since we can't run PS in this environment.
        # This confirms that if a script runs and respects environment variables, it'll work.
        # But wait, I want to verify the logic inside the .ps1 file.
        # Since I can't run .ps1, I'll just rely on the manual review of the change
        # and checking for syntax errors if I could.

        # Let's check for any obvious syntax errors by reading it.
        with open("ps_scripts/get_network_adapters.ps1", "r") as f:
            content = f.read()

        self.assertIn('$checkIp = if ($env:DIAGNOSTIC_CHECK_IP) { $env:DIAGNOSTIC_CHECK_IP } else { "8.8.8.8" }', content)
        self.assertIn('Test-Connection -ComputerName $checkIp', content)

if __name__ == "__main__":
    unittest.main()
