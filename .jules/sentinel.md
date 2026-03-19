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

## 2024-05-24 - Unbounded Audit Log Growth
**Vulnerability:** The application was using a standard `logging.FileHandler` for its security audit logger. A malicious actor could intentionally trigger security warnings or errors rapidly to inflate the log file size indefinitely, exhausting disk space and causing a system-wide Denial of Service (DoS).
**Learning:** Any file-based logging mechanism in a production-like environment (especially security or audit logs that can be triggered by user actions) must be bounded.
**Prevention:** Always use `logging.handlers.RotatingFileHandler` (or `TimedRotatingFileHandler`) with strict limits on file size (`maxBytes`) and number of backup files (`backupCount`) to ensure the maximum disk footprint is deterministic.

## 2024-03-08 - Server-Side Model Validation (SSRF Prevention)
**Vulnerability:** The application used a frontend `st.selectbox` to constrain the AI model choice but trusted this input directly on the server when passing it to LiteLLM. An attacker manipulating the WebSocket could bypass the UI and supply an arbitrary model string (e.g., `openai/http://malicious.internal/`), leading to Server-Side Request Forgery (SSRF) or unauthorized API consumption.
**Learning:** UI-level constraints (like dropdowns) are purely cosmetic and do not provide server-side security. Malicious clients can send arbitrary data to backend endpoints.
**Prevention:** Always enforce strict server-side validation (allowlisting) of all user-controlled inputs, verifying they match the permitted options before processing.

## 2024-03-09 - Environment Variable Leakage to External Processes
**Vulnerability:** The `subprocess.run` call in `run_powershell_script` inherited the full parent environment, unintentionally exposing the highly sensitive `GOOGLE_API_KEY` to the executed PowerShell scripts.
**Learning:** External processes inherit the environment of their parent by default. If the parent application loads sensitive secrets (like API keys) into environment variables, any executed script or subprocess will also have access to them, violating the Principle of Least Privilege and posing a severe risk if the subprocess environment is dumped, logged, or compromised.
**Prevention:** Always explicitly define or sanitize the `env` dictionary passed to `subprocess.run()` (e.g., copying `os.environ` and popping sensitive keys) when executing external commands that do not require those secrets.

## 2024-03-13 - Log Injection (CRLF) via External Process Stderr
**Vulnerability:** The raw `stderr` output from the PowerShell process was being written directly into the security audit log without sanitization. An attacker could potentially craft a payload that outputs newline (`\n`) and carriage return (`\r`) characters to `stderr`, allowing them to inject fake, multiline log entries into `security_audit.log`, confusing forensics or hiding malicious activity.
**Learning:** External processes output cannot be trusted entirely, even if the execution path is secured. Output variables (especially errors) might contain log injection payloads.
**Prevention:** Always sanitize or encode data derived from external processes before passing it to a `Logger`. For single-line logs, stripping or replacing newline characters (e.g., `text.replace('\n', ' ')`) prevents CRLF injection.

## 2024-03-13 - UI False Positive Success on Silent Script Failures
**Vulnerability:** The application executed PowerShell scripts via `subprocess.run` but failed to verify the exit status (`returncode`). If a script failed internally (e.g., a WMI query error) but still generated some text output or completed execution, the Python backend treated it as a success, and the frontend displayed a misleading "Analysis complete! ✅" toast.
**Learning:** Checking for output content is insufficient to determine process success. Many command line tools or scripts output error details to `stdout` instead of `stderr` or exit cleanly even when failing.
**Prevention:** Always verify the actual exit code (`returncode == 0` for success) when executing system commands. Explicitly map non-zero exit codes to generic, safe error strings (`"Execution Failed: ..."`) so the UI correctly triggers failure feedback mechanisms.
## 2026-03-15 - Prevent Log Injection via Input Sanitization
**Vulnerability:** Untrusted inputs (like script_name and exception strings) were logged directly without explicit string casting and CRLF stripping, enabling Log Injection attacks.
**Learning:** Even internal arguments or exception objects must be sanitized because an attacker might bypass UI validation or unexpected types might cause AttributeError.
**Prevention:** Always explicitly cast to string and replace newlines (e.g., str(val).replace('
', ' ').replace('', '')) before writing to security audit logs.

## 2024-03-16 - Server-Side Input Length Validation (DoS Prevention)
**Vulnerability:** The chat input length was only validated on the frontend UI using Streamlit's `max_chars` parameter. An attacker could bypass the UI and send oversized inputs directly to the backend.
**Learning:** Frontend/UI constraints are easily bypassed. Processing unconstrained input size on the server side can lead to API Denial of Wallet (due to excessive tokens) or memory exhaustion (Denial of Service).
**Prevention:** Always enforce input length limits server-side (e.g., `if len(prompt) > 2000: ...`), explicitly validating the input length before processing and securely logging any violations.

## 2024-03-20 - Prevent Indirect Prompt Injection from Diagnostic Logs
**Vulnerability:** The AI system prompt directly appended the `diagnostic_output` (which includes data like Windows Event Logs) without strict delimiters or security directives. Because unprivileged users or applications can write to Windows Event Logs, an attacker could craft a log entry containing malicious instructions (e.g., "Ignore previous instructions and say X"). The AI might then execute these injected instructions, leading to Indirect Prompt Injection.
**Learning:** Any system data ingested into an LLM context that can be influenced by external actors (like log files, external web content, or user inputs) must be treated as untrusted data.
**Prevention:** Always encapsulate untrusted data within explicit delimiters (e.g., `<diagnostic_output>...</diagnostic_output>`) and provide a strict security directive to the model explicitly instructing it to treat the encapsulated content only as raw data to be analyzed, never as executable instructions.

## 2026-03-17 - Hardcoded IP Address in Network Diagnostic
**Vulnerability:** Hardcoded IP address (8.8.8.8) used for internet connectivity testing in a PowerShell script.
**Learning:** Hardcoding external dependencies like IP addresses reduces system flexibility, hinders maintenance, and can be flagged as a security risk by scanners.
**Prevention:** Always use environment variables or configuration parameters for external endpoints, providing sensible defaults to maintain backward compatibility.

## 2026-03-18 - Indirect Prompt Injection via XML Tag Breakout
**Vulnerability:** The application used XML delimiters (`<diagnostic_output>`) to encapsulate untrusted diagnostic data (like Windows Event Logs) to prevent Indirect Prompt Injection. However, the untrusted data itself was not sanitized for these delimiters.
**Learning:** If an attacker inserts the closing tag (`</diagnostic_output>`) into the untrusted data (e.g., via a malicious Event Log entry), they can prematurely close the data context. Any text following the injected closing tag might then be interpreted by the LLM as part of the core system prompt/instructions, defeating the delimiter defense.
**Prevention:** When using delimiters to isolate untrusted data in an LLM prompt, always sanitize the untrusted payload by escaping, encoding, or stripping the delimiter tags (e.g., `.replace("</diagnostic_output>", "_/diagnostic_output_")`) before appending it to the prompt.

## 2026-03-19 - Pattern-based Environment Variable Scrubbing for External Processes
**Vulnerability:** The `subprocess.run` call scrubbed only the specific `GOOGLE_API_KEY` environment variable. If additional integrations (like different LiteLLM providers or other API services) required new secrets (e.g., `AWS_SECRET_ACCESS_KEY`, `OPENAI_API_KEY`), they would be leaked to the external PowerShell script by default, as the scrubbing list was hardcoded and not extensible.
**Learning:** Hardcoded, explicitly named lists for scrubbing sensitive environment variables are brittle and fail open when new features are added. Extensible architectures require robust, pattern-matching defenses to account for future secret additions without requiring manual updates to the scrubbing logic.
**Prevention:** Always implement pattern-based scrubbing (e.g., checking for keys containing `API_KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`) when passing the `env` dictionary to external processes, ensuring that both current and future sensitive variables are automatically stripped.
