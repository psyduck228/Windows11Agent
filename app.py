import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import os

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

def update_output(text_area, content):
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, content)
    text_area.config(state=tk.DISABLED)

def analyze_startup(text_area):
    update_output(text_area, "Analyzing startup processes...\n")
    text_area.update()
    result = run_powershell_script('get_startup_processes.ps1')
    update_output(text_area, result)

def check_network(text_area):
    update_output(text_area, "Checking network adapters and resetting DNS cache...\n")
    text_area.update()
    result1 = run_powershell_script('get_network_adapters.ps1')
    result2 = run_powershell_script('reset_dns_cache.ps1')
    update_output(text_area, f"--- Network Check ---\n{result1}\n\n--- DNS Reset ---\n{result2}")

def scan_events(text_area):
    update_output(text_area, "Scanning recent critical events...\n")
    text_area.update()
    result = run_powershell_script('get_critical_events.ps1')
    update_output(text_area, result)

def create_gui():
    root = tk.Tk()
    root.title("Windows 11 Diagnostic AI Agent")
    root.geometry("800x600")
    root.configure(padx=10, pady=10)

    # Header
    header_label = tk.Label(root, text="Diagnostic Control Panel", font=("Helvetica", 16, "bold"))
    header_label.pack(pady=(0, 10))

    # Output Area
    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED)
    output_text.pack(expand=True, fill=tk.BOTH, pady=(0, 10))

    # Controls Frame
    controls_frame = tk.Frame(root)
    controls_frame.pack(fill=tk.X)

    # Buttons
    btn_startup = tk.Button(controls_frame, text="Analyze Startup Processes", width=25, 
                            command=lambda: analyze_startup(output_text))
    btn_startup.pack(side=tk.LEFT, padx=5)

    btn_network = tk.Button(controls_frame, text="Check Network & Reset DNS", width=30, 
                            command=lambda: check_network(output_text))
    btn_network.pack(side=tk.LEFT, padx=5)

    btn_events = tk.Button(controls_frame, text="Scan Critical Events", width=25, 
                           command=lambda: scan_events(output_text))
    btn_events.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
