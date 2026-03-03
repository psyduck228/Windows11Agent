## 2024-03-02 - Path Traversal Vulnerability in PowerShell Script Runner
**Vulnerability:** The `run_powershell_script` function in `app.py` constructs a file path by joining the script directory with a user-provided (or currently hardcoded) script name using `os.path.join`. However, it doesn't validate if the resolved path actually stays within the intended `ps_scripts` directory.
**Learning:** `os.path.join` on Windows/Linux will accept absolute paths or traversals like `../../` for the second argument, allowing an attacker to specify *any* file on the system to be executed via PowerShell.
**Prevention:** Always use `os.path.abspath` to resolve the final path and verify that it starts with the intended safe directory (e.g., `os.path.abspath(path).startswith(safe_dir)`) before executing or reading files.

## 2024-03-03 - Missing Timeout on External Process Execution
**Vulnerability:** The `subprocess.run` call in `run_powershell_script` lacked a `timeout` argument. Since Streamlit runs synchronously on a fixed thread pool, a hanging PowerShell script could block a worker thread indefinitely, leading to resource exhaustion and Denial of Service (DoS).
**Learning:** External blocking calls (like shell scripts or remote APIs) must always have a strict timeout in synchronous web frameworks like Streamlit to prevent thread starvation.
**Prevention:** Always include a `timeout` parameter in `subprocess.run` (e.g., `timeout=30`) and handle `subprocess.TimeoutExpired` to recover securely.
