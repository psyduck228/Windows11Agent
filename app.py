import streamlit as st
import subprocess
import os
import google.generativeai as genai
from litellm import completion
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key and api_key != "your_google_api_key_here":
    try:
        genai.configure(api_key=api_key)
    except Exception:
        pass

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ps_scripts')

def run_powershell_script(script_name):
    # 🛡️ Sentinel: Prevent Path Traversal (LFI/RCE)
    script_path = os.path.abspath(os.path.join(SCRIPTS_DIR, script_name))
    # Add trailing slash to SCRIPTS_DIR to prevent sibling directory attacks
    base_dir = os.path.abspath(SCRIPTS_DIR)
    if not base_dir.endswith(os.sep):
        base_dir += os.sep
    if not script_path.startswith(base_dir):
        return "Error: Invalid script path requested."

    if not os.path.exists(script_path):
        return "Error: Script not found."
    
    try:
        # Define the arguments for powershell execution
        args = ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", script_path]
        
        # Execute the process
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        
        output = result.stdout
        if result.stderr:
            output += f"\n[Errors/Warnings]:\n{result.stderr}"
            
        return output if output.strip() else "Command executed with no output."
    
    except Exception as e:
        # 🛡️ Sentinel: Return a generic error to prevent exposing system details
        return "Execution Failed: An unexpected error occurred while executing the diagnostic script."

# --- Streamlit App Initialization ---
st.set_page_config(page_title="Windows 11 Diagnostic AI Agent", layout="wide")

if "diagnostic_output" not in st.session_state:
    st.session_state["diagnostic_output"] = ""

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### AI Configuration")
    
    available_models = ["ollama/deepseek-r1"]
    default_gemini = ["gemini/gemini-1.5-flash", "gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"]
    
    if not api_key or api_key == "your_google_api_key_here":
        st.warning("⚠️ GOOGLE_API_KEY missing. Gemini models will not work.")
        available_models = default_gemini + available_models
    else:
        st.success("✅ Google API Key loaded.")
        try:
            gemini_models = [
                f"gemini/{m.name.split('models/')[1]}" 
                for m in genai.list_models() 
                if 'generateContent' in getattr(m, 'supported_generation_methods', [])
            ]
            if gemini_models:
                available_models = gemini_models + available_models
            else:
                available_models = default_gemini + available_models
        except Exception:
            available_models = default_gemini + available_models
    
    selected_model = st.selectbox(
        "Select Model",
        available_models,
        index=0
    )
# --- Header ---
st.title("Windows 11 Diagnostic AI Agent")
st.markdown("### Diagnostic Control Panel")

# --- Controls ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Analyze Startup Processes", use_container_width=True):
        st.session_state["diagnostic_output"] = "Analyzing startup processes...\n\n"
        result = run_powershell_script('get_startup_processes.ps1')
        st.session_state["diagnostic_output"] += result

with col2:
    if st.button("Check Network & Reset DNS", use_container_width=True):
        st.session_state["diagnostic_output"] = "Checking network adapters and resetting DNS cache...\n\n"
        result1 = run_powershell_script('get_network_adapters.ps1')
        result2 = run_powershell_script('reset_dns_cache.ps1')
        st.session_state["diagnostic_output"] += f"--- Network Check ---\n{result1}\n\n--- DNS Reset ---\n{result2}"

with col3:
    if st.button("Scan Critical Events", use_container_width=True):
        st.session_state["diagnostic_output"] = "Scanning recent critical events...\n\n"
        result = run_powershell_script('get_critical_events.ps1')
        st.session_state["diagnostic_output"] += result

# --- Output Area ---
st.markdown("#### Diagnostic Output")
with st.container(height=300):
   if st.session_state["diagnostic_output"]:
       st.code(st.session_state["diagnostic_output"], language="powershell")
   else:
       st.info("Run a diagnostic tool above to view output.")

st.divider()

# --- Chat Interface ---
st.markdown("### Ask about these diagnostics")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a follow-up question..."):
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
        system_instruction += "\n\n### CURRENT DIAGNOSTIC OUTPUT ###\n" + st.session_state["diagnostic_output"]

    # Convert chat history to OpenAI format for litellm
    messages_for_llm = [{"role": "system", "content": system_instruction}]
    for msg in st.session_state.messages:
        messages_for_llm.append({"role": msg["role"], "content": msg["content"]})
    
    with st.chat_message("assistant"):
        if selected_model.startswith("gemini") and (not api_key or api_key == "your_google_api_key_here"):
             error_msg = "Please configure your `GOOGLE_API_KEY` in the `.env` file to use Gemini models."
             st.error(error_msg)
             st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            try:
                # Call litellm completion
                response = completion(
                    model=selected_model,
                    messages=messages_for_llm,
                    stream=True
                )
                
                # Stream the response
                def generate():
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                            
                full_response = st.write_stream(generate())
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                # 🛡️ Sentinel: Do not leak detailed error strings to the UI.
                # In a real app we would log str(e) securely here.
                error_msg = "An unexpected error occurred while generating the response. Please try again later."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

