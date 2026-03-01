import streamlit as st
import subprocess
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ps_scripts')

def run_powershell_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        return f"Error: Script not found at {script_path}"
    
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
        return f"Execution Failed: {str(e)}"

# --- Streamlit App Initialization ---
st.set_page_config(page_title="Windows 11 Diagnostic AI Agent", layout="wide")

if "diagnostic_output" not in st.session_state:
    st.session_state["diagnostic_output"] = ""

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### AI Configuration")
    if not api_key or api_key == "your_google_api_key_here":
        st.error("⚠️ GOOGLE_API_KEY missing or invalid in .env file.")
    else:
        st.success("✅ Google API Key loaded.")
    
    selected_model = st.selectbox(
        "Select Gemini Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
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

    # Convert chat history to Gemini format, omitting the first diagnostic context if we reinject it
    gemini_history = []
    for msg in st.session_state.messages[:-1]: # exclude the prompt we just added
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # Add diagnostic output as context to the system prompt/latest message
    system_instruction = """
    You are an expert Windows IT support agent. 
    Your strict mandate is to answer the user's questions based ONLY on the provided system diagnostic results (e.g., WMI queries, Event Logs).
    If the user asks a question that cannot be answered using the provided diagnostic data, politely refuse to answer and instruct them to run the appropriate diagnostic tool first.
    """
    if st.session_state["diagnostic_output"]:
        system_instruction += "\n\n### CURRENT DIAGNOSTIC OUTPUT ###\n" + st.session_state["diagnostic_output"]
    
    with st.chat_message("assistant"):
        if not api_key or api_key == "your_google_api_key_here":
             error_msg = "Please configure your `GOOGLE_API_KEY` in the `.env` file to use the AI chat."
             st.error(error_msg)
             st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            try:
                # Initialize model with system instruction
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    system_instruction=system_instruction
                )
                
                # Start chat session with history
                chat = model.start_chat(history=gemini_history)
                
                # Stream the response
                response = chat.send_message(prompt, stream=True)
                full_response = st.write_stream(chunk.text for chunk in response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

