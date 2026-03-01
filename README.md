# Windows 11 Diagnostic AI Agent

An autonomous diagnostic assistant built with Streamlit and powered by Google's Gemini API. This application provides a web-based interface to run common Windows administrative diagnostics (via PowerShell) and seamlessly chat with an AI expert about the results.

## Features
- **Run PowerShell Diagnostics**: Query WMI and Event Logs securely.
  - **Analyze Startup Processes**: Get insights into the software that launches when Windows starts.
  - **Check Network & Reset DNS**: List network adapters and resolve DNS caching issues.
  - **Scan Critical Events**: Quickly review recent critical system errors from the Windows Event Logs.
- **AI Chat Assistant**: Ask questions directly in the app. The AI is specifically instructed to analyze the most recent diagnostic output to provide tailored expert IT advice.
- **Model Selector**: Choose between multiple Gemini models (e.g., `gemini-2.5-flash`, `gemini-1.5-pro`).
- **Real-Time Streaming**: AI responses stream directly to the chat interface, providing an intuitive "typing" experience.

## Prerequisites
- Python 3.9+
- A Google Gemini API Key

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd Windows11Agent
   ```
2. Install the required Python packages:
   ```bash
   pip install streamlit google-generativeai python-dotenv
   ```
3. Set up your environment variables:
   - Create a file named `.env` in the root directory (or modify the existing one).
   - Add your Google API key:
     ```env
     GOOGLE_API_KEY=your_google_api_key_here
     ```

## Usage

### Using the App Launcher
You can easily start the application by double-clicking the **`start_agent.bat`** file located in the root directory. This will automatically execute the required setup and open the Streamlit web app in your default browser.

### Using the Terminal
Alternatively, launch the application manually using the terminal:
```bash
streamlit run app.py
```

## Security
- The diagnostic scripts use PowerShell. The execution policy is temporarily bypassed for the individual script runs using `-ExecutionPolicy Bypass`.
- Ensure your `.env` file (containing your API keys) is added to `.gitignore` so it is not accidentally uploaded to a public repository.

## Project Structure
- `app.py`: The main Streamlit application logic and UI.
- `ps_scripts/`: Directory containing the underlying PowerShell diagnostic scripts.
- `start_agent.bat`: Quick-start batch launcher for Windows users.
- `.env`: Environment variables and API keys (not tracked in version control).
