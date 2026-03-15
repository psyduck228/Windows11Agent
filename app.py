"""Windows 11 Diagnostic AI Agent Streamlit App."""

import os
import subprocess
import time
import streamlit as st  # type: ignore
import google.generativeai as genai  # type: ignore
from litellm import completion  # type: ignore
from dotenv import load_dotenv  # type: ignore
import logging
from logging.handlers import RotatingFileHandler

# 🛡️ Sentinel: Configure secure audit logging for sensitive operations
# 🛡️ Sentinel: Use RotatingFileHandler to prevent unbounded log growth (Disk Exhaustion DoS)
audit_logger = logging.getLogger("security_audit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    fh = RotatingFileHandler(
        "security_audit.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - SECURITY AUDIT - %(message)s")
    )
    audit_logger.addHandler(fh)

# Load API keys from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key and api_key != "your_google_api_key_here":
    try:
        genai.configure(api_key=api_key)  # type: ignore
    except (ValueError, TypeError):
        pass

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ps_scripts")

# 🛡️ Sentinel: Strict allowlist of scripts to prevent unauthorized execution
ALLOWED_SCRIPTS = {
    "get_startup_processes.ps1",
    "get_network_adapters.ps1",
    "reset_dns_cache.ps1",
    "get_critical_events.ps1",
}

WELCOME_MESSAGE = (
    "Hello! I am your Windows 11 Diagnostic AI Agent. "
    "Run a diagnostic tool above and then ask me any questions "
    "about the results!"
)

# 🎨 Palette: Extract duplicated user-facing strings into global constants
UI_ANALYSIS_FAILED = "Analysis failed!"
UI_ANALYSIS_COMPLETE = "Analysis complete!"
UI_REQUIRE_DIAGNOSTIC = "Run a diagnostic tool above first..."


@st.cache_data(ttl=3600)
def get_gemini_models():
    """Fetches available Gemini models from the Google Generative AI API."""
    return [
        f"gemini/{m.name.split('models/')[1]}"  # type: ignore
        for m in genai.list_models()  # type: ignore
        if "generateContent" in getattr(m, "supported_generation_methods", [])
    ]


def run_powershell_script(script_name: str) -> str:
    """Executes a PowerShell script and returns the output."""
    # 🛡️ Sentinel: Prevent Log Injection (CRLF) and Type Errors by sanitizing inputs
    sanitized_script_name = str(script_name).replace("\n", " ").replace("\r", "")

    # 🛡️ Sentinel: Implement strict whitelist validation for script execution
    if script_name not in ALLOWED_SCRIPTS:
        audit_logger.warning(
            f"Unauthorized script execution attempt: {sanitized_script_name}"
        )
        return "Error: Unauthorized script execution requested."

    # 🛡️ Sentinel: Implement rate limiting to prevent CPU/memory exhaustion via rapid execution
    current_time = time.time()
    last_run = st.session_state.get("last_script_execution", 0)
    if current_time - last_run < 5:
        audit_logger.warning(f"Rate limit exceeded for script: {sanitized_script_name}")
        return "Error: Rate limit exceeded. Please wait 5 seconds before running another diagnostic."

    st.session_state["last_script_execution"] = current_time

    audit_logger.info(f"Diagnostic script execution requested: {sanitized_script_name}")

    # 🛡️ Sentinel: Prevent Path Traversal (LFI/RCE)
    script_path = os.path.abspath(os.path.join(SCRIPTS_DIR, script_name))
    # Add trailing slash to SCRIPTS_DIR to prevent sibling directory attacks
    base_dir = os.path.abspath(SCRIPTS_DIR)
    if not base_dir.endswith(os.sep):
        base_dir += os.sep
    if not script_path.startswith(base_dir):
        audit_logger.warning(
            f"Path traversal attempt blocked for script: {sanitized_script_name}"
        )
        return "Error: Invalid script path requested."

    if not os.path.exists(script_path):
        audit_logger.warning(f"Requested script not found: {sanitized_script_name}")
        return "Error: Script not found."

    try:
        # Define the arguments for powershell execution
        args = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-NoProfile",
            "-File",
            script_path,
        ]

        # Execute the process
        # 🛡️ Sentinel: Prevent environment variable leakage to external processes
        secure_env = os.environ.copy()
        secure_env.pop("GOOGLE_API_KEY", None)

        # 🛡️ Sentinel: Add timeout to prevent long-running scripts
        # from blocking the Streamlit thread
        powershell_result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env=secure_env,
        )

        output = powershell_result.stdout
        if powershell_result.stderr:
            # 🛡️ Sentinel: Prevent Log Injection (CRLF) by sanitizing newlines in stderr
            sanitized_stderr = powershell_result.stderr.replace("\n", " ").replace(
                "\r", ""
            )
            # 🛡️ Sentinel: Fail securely by logging errors instead of leaking them to the user interface
            audit_logger.error(
                f"Script {sanitized_script_name} executed with errors/warnings: {sanitized_stderr}"
            )

        if powershell_result.returncode != 0:
            # 🛡️ Sentinel: Explicitly return 'Execution Failed' on non-zero exit code to ensure UI correctly flags failure (False-Positive Success Prevention)
            return f"Execution Failed: The diagnostic script returned an error code ({powershell_result.returncode})."

        audit_logger.info(f"Successfully executed script: {sanitized_script_name}")
        return output if output.strip() else "Command executed with no output."

    except subprocess.TimeoutExpired:
        # 🛡️ Sentinel: Fail securely on timeout without leaking system state
        audit_logger.error(f"Script execution timed out: {sanitized_script_name}")
        return "Execution Failed: The diagnostic script timed out after 30 seconds."
    except (OSError, ValueError) as e:
        # 🛡️ Sentinel: Return a generic error to prevent exposing system details
        sanitized_error = str(e).replace("\n", " ").replace("\r", "")
        audit_logger.error(
            f"Unexpected error executing {sanitized_script_name}: {sanitized_error}"
        )
        return (
            "Execution Failed: An unexpected error occurred "
            "while executing the diagnostic script."
        )


# --- Streamlit App Initialization ---
st.set_page_config(page_title="Windows 11 Diagnostic AI Agent", layout="wide")

if "diagnostic_output" not in st.session_state:
    st.session_state["diagnostic_output"] = ""

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": WELCOME_MESSAGE}]

# --- Sidebar ---
with st.sidebar:
    st.markdown("### AI Configuration")

    available_models = ["ollama/deepseek-r1"]
    default_gemini = [
        "gemini/gemini-1.5-flash",
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-pro",
    ]

    if not api_key or api_key == "your_google_api_key_here":
        st.info("Configure GOOGLE_API_KEY in .env to unlock Gemini models.", icon="💡")
    else:
        st.success("Google API Key loaded.", icon="✅")
        try:
            gemini_models = get_gemini_models()
            if gemini_models:
                available_models = gemini_models + available_models
            else:
                available_models = default_gemini + available_models
        except Exception:
            # 🛡️ Sentinel: Catch all exceptions to prevent leaking API errors/stack traces
            available_models = default_gemini + available_models

    selected_model = st.selectbox(
        "Select Model",
        available_models,
        index=0,
        help="Choose the AI model to analyze your diagnostics. Gemini models require a valid Google API Key.",
    )

    st.divider()
    is_chat_empty = len(st.session_state.get("messages", [])) <= 1
    with st.popover(
        "Clear Chat History",
        icon="🗑️",
        help=(
            "Chat history is already empty."
            if is_chat_empty
            else "Clear the conversation history."
        ),
        use_container_width=True,
        disabled=is_chat_empty,
    ):
        st.markdown("Are you sure you want to delete all chat history?")
        if st.button(
            "Yes, clear chat",
            type="primary",
            use_container_width=True,
            icon="⚠️",
        ):
            st.session_state["messages"] = [
                {"role": "assistant", "content": WELCOME_MESSAGE}
            ]
            st.rerun()
# --- Header ---
st.title("Windows 11 Diagnostic AI Agent")
st.markdown("### Diagnostic Control Panel")

# --- Controls ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "Analyze Startup Processes",
        icon="🚀",
        help="Queries WMI to list programs that run when Windows starts.",
        use_container_width=True,
    ):
        with st.spinner("Analyzing startup processes..."):
            result = run_powershell_script("get_startup_processes.ps1")
        if result.startswith("Error:") or result.startswith("Execution Failed:"):
            st.toast(UI_ANALYSIS_FAILED, icon="❌")
        else:
            st.toast(UI_ANALYSIS_COMPLETE, icon="✅")
        st.session_state["diagnostic_output"] = result

with col2:
    if st.button(
        "Check Network & Reset DNS",
        icon="🌐",
        help="Lists network adapters and flushes the DNS resolver cache.",
        use_container_width=True,
    ):
        with st.spinner("Checking network & resetting DNS..."):
            result1 = run_powershell_script("get_network_adapters.ps1")
            result2 = run_powershell_script("reset_dns_cache.ps1")
        if (
            result1.startswith("Error:")
            or result1.startswith("Execution Failed:")
            or result2.startswith("Error:")
            or result2.startswith("Execution Failed:")
        ):
            st.toast(UI_ANALYSIS_FAILED, icon="❌")
        else:
            st.toast(UI_ANALYSIS_COMPLETE, icon="✅")
        st.session_state["diagnostic_output"] = (
            f"--- Network Check ---\n{result1}\n\n--- DNS Reset ---\n{result2}"
        )

with col3:
    if st.button(
        "Scan Critical Events",
        icon="⚠️",
        help="Scans Windows Event Logs for recent critical system errors.",
        use_container_width=True,
    ):
        with st.spinner("Scanning critical events..."):
            result = run_powershell_script("get_critical_events.ps1")
        if result.startswith("Error:") or result.startswith("Execution Failed:"):
            st.toast(UI_ANALYSIS_FAILED, icon="❌")
        else:
            st.toast(UI_ANALYSIS_COMPLETE, icon="✅")
        st.session_state["diagnostic_output"] = result

# --- Output Area ---
st.markdown("#### Diagnostic Output")
with st.container(height=300):
    output = st.session_state.get("diagnostic_output", "")
    if output:
        if "Error:" in output or "Execution Failed:" in output:
            st.error(output, icon="❌")
        else:
            st.code(output, language="powershell")
    else:
        st.info(UI_REQUIRE_DIAGNOSTIC, icon="💡")

st.divider()

# --- Chat Interface ---
st.markdown("### Ask about these diagnostics")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
# 🛡️ Sentinel: Enforce max input length to prevent potential resource exhaustion / DoS
CHAT_PLACEHOLDER = (
    "Ask a question about the diagnostic results..."
    if st.session_state.get("diagnostic_output")
    else UI_REQUIRE_DIAGNOSTIC
)
CHAT_DISABLED = not bool(st.session_state.get("diagnostic_output"))

if prompt := st.chat_input(CHAT_PLACEHOLDER, max_chars=2000, disabled=CHAT_DISABLED):
    # 🛡️ Sentinel: Implement rate limiting to prevent API abuse and DoS via rapid requests
    current_time = time.time()
    last_chat = st.session_state.get("last_chat_time", 0)
    if current_time - last_chat < 3:
        st.toast("Please wait a moment before sending another message.", icon="⚠️")
        audit_logger.warning("Rate limit exceeded for chat input.")
    else:
        st.session_state["last_chat_time"] = current_time

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add diagnostic output as context to the system prompt/latest message
        system_instruction = """
        You are an expert Windows IT support agent.
        Your strict mandate is to answer the user's questions based ONLY on the provided system diagnostic results (e.g., WMI queries, Event Logs).
        If the user asks a question that cannot be answered using the provided diagnostic data, politely refuse to answer and instruct them to run the appropriate diagnostic tool first.
        """
        if st.session_state["diagnostic_output"]:
            system_instruction += (
                "\n\n### CURRENT DIAGNOSTIC OUTPUT ###\n"
                + st.session_state["diagnostic_output"]
            )

        # Convert chat history to OpenAI format for litellm
        messages_for_llm = [{"role": "system", "content": system_instruction}]

        # 🛡️ Sentinel: Limit conversation history to prevent Context Window/Token Exhaustion DoS
        MAX_HISTORY = 10
        history = st.session_state.messages[-MAX_HISTORY:]

        for msg in history:
            messages_for_llm.append({"role": msg["role"], "content": msg["content"]})

        with st.chat_message("assistant"):
            # 🛡️ Sentinel: Enforce strict server-side model validation to prevent arbitrary model execution (Authorization Bypass / SSRF defense)
            if selected_model not in available_models:
                # 🛡️ Sentinel: Prevent Log Injection (CRLF) by sanitizing newlines
                sanitized_model = (
                    str(selected_model).replace("\n", " ").replace("\r", "")
                )
                audit_logger.warning(
                    f"Unauthorized model selection bypassed UI: {sanitized_model}"
                )
                st.error(
                    "Invalid model selected. Please choose a valid model.", icon="❌"
                )
                st.stop()

            if selected_model.startswith("gemini") and (
                not api_key or api_key == "your_google_api_key_here"
            ):
                ERROR_MSG = (
                    "Please configure your `GOOGLE_API_KEY` in the "
                    "`.env` file to use Gemini models."
                )
                st.error(ERROR_MSG, icon="❌")
                st.session_state.messages.append(
                    {"role": "assistant", "content": ERROR_MSG}
                )
            else:
                try:
                    # Call litellm completion
                    # 🛡️ Sentinel: Add timeout to prevent API hangs from blocking Streamlit threads
                    response = completion(
                        model=selected_model,
                        messages=messages_for_llm,
                        stream=True,
                        timeout=30,
                    )

                    # Stream the response
                    def generate():
                        """Yields chunks of the stream response."""
                        for chunk in response:
                            content = chunk.choices[0].delta.content  # type: ignore
                            if content:
                                yield content

                    full_response = st.write_stream(generate())

                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )

                except Exception as e:
                    # 🛡️ Sentinel: Catch all exceptions (Timeout, APIError) to avoid leaking stack traces to the UI.
                    sanitized_error = str(e).replace("\n", " ").replace("\r", "")
                    audit_logger.error(
                        f"LLM API completion error securely caught: {sanitized_error}"
                    )
                    ERROR_MSG = (
                        "An unexpected error occurred while generating the "
                        "response. Please try again later."
                    )
                    st.error(ERROR_MSG, icon="❌")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": ERROR_MSG}
                    )
