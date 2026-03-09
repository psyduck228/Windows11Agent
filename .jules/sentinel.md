## 2024-03-02 - Path Traversal Vulnerability in PowerShell Script Runner
**Vulnerability:** The `run_powershell_script` function in `app.py` constructs a file path by joining the script directory with a user-provided (or currently hardcoded) script name using `os.path.join`. However, it doesn't validate if the resolved path actually stays within the intended `ps_scripts` directory.
**Learning:** `os.path.join` on Windows/Linux will accept absolute paths or traversals like `../../` for the second argument, allowing an attacker to specify *any* file on the system to be executed via PowerShell.
**Prevention:** Always use `os.path.abspath` to resolve the final path and verify that it starts with the intended safe directory (e.g., `os.path.abspath(path).startswith(safe_dir)`) before executing or reading files.

## 2024-03-03 - Missing Timeout on External Process Execution
**Vulnerability:** The `subprocess.run` call in `run_powershell_script` lacked a `timeout` argument. Since Streamlit runs synchronously on a fixed thread pool, a hanging PowerShell script could block a worker thread indefinitely, leading to resource exhaustion and Denial of Service (DoS).
**Learning:** External blocking calls (like shell scripts or remote APIs) must always have a strict timeout in synchronous web frameworks like Streamlit to prevent thread starvation.
**Prevention:** Always include a `timeout` parameter in `subprocess.run` (e.g., `timeout=30`) and handle `subprocess.TimeoutExpired` to recover securely.

## 2024-03-04 - Leaked Stack Traces and Thread Starvation from External API Calls
**Vulnerability:** The application was not using a broad `except Exception:` block around calls to remote APIs (like `genai.list_models()` and `litellm.completion()`), allowing unexpected network or API-related exceptions to bubble up and potentially expose sensitive stack traces to the Streamlit UI. Additionally, the LLM completion API call lacked a strict timeout, which could cause thread starvation if the API hangs.
**Learning:** Any interactions with external systems must use strict timeout boundaries and robust, catch-all exception handling (`except Exception:`) in synchronous UI frameworks to both prevent DoS and ensure secure, non-leaking error fallback mechanisms.
**Prevention:** Ensure that every remote API call has an explicit `timeout` defined and is wrapped in a generic `try-except Exception` block that securely handles the error without exposing raw error strings to the UI.

## 2024-03-05 - Missing Security Audit Logging for Sensitive Operations
**Vulnerability:** The application was allowing users to execute privileged PowerShell scripts (using `-ExecutionPolicy Bypass`) without maintaining any internal record of when these scripts were executed, whether they succeeded, or if they failed. It also caught and swallowed LLM API exceptions securely but failed to record the error details anywhere for administrative review.
**Learning:** For any application that executes potentially dangerous commands or acts as an administrative control panel, the lack of audit logging is a significant security gap. Without logs, it is impossible to perform post-incident forensics, monitor for abuse (e.g., repeated path traversal attempts or DoS via button mashing), or diagnose internal API failures without exposing details to the user.
**Prevention:** Always implement robust, file-based security audit logging (e.g., using Python's `logging` module) to record the execution of sensitive operations, record any access violations, and securely capture the details of caught exceptions.

## 2024-05-24 - Prevent Stderr Information Leakage from PowerShell Scripts
**Vulnerability:** The application was appending raw `powershell_result.stderr` output directly to the user-facing `diagnostic_output`.
**Learning:** Returning unhandled errors directly to users exposes internal system information (e.g., stack traces, paths, internal configuration), leading to information leakage which can facilitate further attacks.
**Prevention:** Always log `stderr` from backend/system processes securely using a designated `audit_logger`, and provide generic, safe error messages to the user interface instead of returning raw exception details or stack traces.

## 2026-03-07 - Resource Exhaustion via Rapid Script Execution
**Vulnerability:** The application allowed users to trigger resource-intensive PowerShell scripts (like WMI queries) continuously without delay. This lack of rate limiting could cause CPU and memory exhaustion, leading to a Denial of Service (DoS).
**Learning:** Administrative endpoints that execute system commands are prime targets for resource exhaustion attacks (even accidental ones like button mashing).
**Prevention:** Implement server-side rate limiting (e.g., using session state timestamps) to enforce cooldown periods between resource-intensive operations.

## 2024-05-24 - LLM Denial of Wallet and Context Exhaustion
**Vulnerability:** The chat interface lacked rate limiting on user inputs and didn't restrict the number of previous messages sent to the LLM. An attacker could rapidly spam messages, driving up API costs (Denial of Wallet) or exhausting the model's context window, causing requests to fail or take exponentially longer.
**Learning:** Chat interfaces connected to paid or rate-limited LLM APIs must have both input frequency limits (cooldowns) and token/context limits (restricting history length) to prevent abuse and excessive costs.
**Prevention:** Always implement a cooldown mechanism (e.g., 3 seconds) for user chat inputs and explicitly limit the array of previous messages (e.g., last 10 messages) appended to the API request context.
## 2024-05-18 - Prevent False-Positive Success Responses
**Vulnerability:** Streamlit user interface displayed successful `st.toast("Analysis complete!", icon="✅")` even when underlying powershell execution scripts failed, misleading users.
**Learning:** Security feedback in UI must accurately reflect actual backend operation results; false positives can lead users to mistakenly believe diagnostics were run correctly or that the system is secure.
**Prevention:** Always conditionally verify the return values or error states of backend calls (e.g., checking if output starts with 'Error:' or 'Execution Failed:') before presenting success feedback to the user via UI components like `st.toast`.

## 2025-05-14 - Missing Whitelist Validation for Script Execution
**Vulnerability:** The `run_powershell_script` function accepted any string as a `script_name`. While path traversal checks were in place, an attacker could still potentially execute any script within the `ps_scripts` directory, even if not intended for user access.
**Learning:** Relying solely on path validation (like `startswith`) is a "filtering" approach which is less secure than a "whitelisting" approach. If new scripts are added to the directory for internal use, they might be accidentally exposed.
**Prevention:** Always implement a strict allowlist (whitelist) of known-good inputs for sensitive operations like system command execution. This provides a definitive defense-in-depth layer.
