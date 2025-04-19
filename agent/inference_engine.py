import json
import os
import random
from collections import Counter
from datetime import datetime
import re

# Load real-time data from zeroinput_memory.json
def load_user_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Filter out empty entries
        if isinstance(data, list):
            data = [entry for entry in data if isinstance(entry, dict) and entry]
        
        return data
    except Exception as e:
        print(f"Error loading user data: {e}")
        return {}

# Load patterns data
def load_patterns(file_path="zeroinput_patterns.json"):
    try:
        with open(file_path, 'r') as file:
            patterns = json.load(file)
        return patterns
    except Exception as e:
        print(f"Error loading patterns: {e}")
        return {}

# Define inference rules (expand as needed)
inference_rules = {
    "file_extension": {
        ".txt": "The user is likely working on text or notes.",
        ".docx": "The user might be working on a document or writing a report.",
        ".exe": "The user is likely using an application or running a setup.",
        ".pdf": "The user might be reading or working on a PDF document.",
        ".md": "The user might be working on markdown documentation or a README file.",
        ".xlsx": "The user is likely working on a spreadsheet.",
        ".py": "The user is working on Python code.",
        ".js": "The user is working on JavaScript code.",
        ".html": "The user is working on a web page.",
        ".css": "The user is working on web styling.",
        ".json": "The user is working with data or configuration files.",
        ".pptx": "The user is working on a presentation."
    },
    "process_activity": {
        "notepad.exe": "The user might be editing or viewing some notes.",
        "chrome.exe": "The user might be browsing the web or researching.",
        "explorer.exe": "The user might be organizing or managing files.",
        "Code.exe": "The user is likely working on code or a project.",
        "msedge.exe": "The user might be browsing with Microsoft Edge.",
        "DuckDuckGo.exe": "The user is searching the web using DuckDuckGo.",
        "python.exe": "The user is running Python scripts.",
        "powershell.exe": "The user is working with PowerShell scripts or commands.",
        "cmd.exe": "The user is running command line tools.",
        "zoom.exe": "The user might be in a meeting or video call.",
        "slack.exe": "The user might be communicating with colleagues.",
        "outlook.exe": "The user is checking emails or managing calendar."
    },
    "time_context": {
        "morning": "This is a good time to plan your day or check emails.",
        "afternoon": "Consider reviewing your progress on today's tasks.",
        "evening": "Time to wrap up work and prepare for tomorrow.",
        "late_night": "Consider taking a break or switching to less intensive tasks."
    },
    "window_patterns": {
        "Visual Studio Code": "You're coding. Consider using Ctrl+Space for autocomplete or Alt+Shift+F to format.",
        "browser": "You're browsing. Remember to bookmark important pages with Ctrl+D.",
        "document": "You're writing. Save regularly with Ctrl+S.",
        "presentation": "You're working on slides. Use Alt+Shift+Left/Right to reorganize slides.",
        "spreadsheet": "You're analyzing data. Remember Alt+= for quick sum."
    }
}

# Function to match file extension to action
def match_file_extension(file):
    _, extension = os.path.splitext(file)
    return inference_rules["file_extension"].get(extension.lower(), f"User is working with {extension} files.")

# Function to match process to action
def match_process(process):
    return inference_rules["process_activity"].get(process.lower(), f"User has {process} running.")

# Get current time context
def get_time_context():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "late_night"

# Extract project context from file paths
def extract_project_context(files):
    project_patterns = {}
    
    for file in files:
        # Extract project names from paths
        parts = os.path.normpath(file).split(os.sep)
        for part in parts:
            if part and part != "Users" and part != "Desktop" and not part.startswith("."):
                project_patterns[part] = project_patterns.get(part, 0) + 1
    
    # Return the most common project context
    if project_patterns:
        most_common = max(project_patterns.items(), key=lambda x: x[1])
        return most_common[0]
    return None

# Function to analyze active window for contextual clues
def analyze_window_title(title):
    # Check for common applications in window title
    for key, value in inference_rules["window_patterns"].items():
        if key.lower() in title.lower():
            return value
    
    # Extract information from window title
    if " - " in title:
        file_name = title.split(" - ")[0]
        return f"You're working on {file_name}."
    
    return f"You're working in {title}."

# Function to infer next actions based on user data
def make_inference(data, patterns=None):
    # If data is a list (a history of records), analyze the history
    if isinstance(data, list) and data:
        # For pattern analysis, use the full history
        history = data[-10:] if len(data) > 10 else data  # Use last 10 entries
        
        # Extract the most recent entry for immediate context
        recent_data = data[-1]
    else:
        history = [data] if isinstance(data, dict) else []
        recent_data = data if isinstance(data, dict) else {}
    
    if not recent_data:
        print("No valid recent data found.")
        return "Unable to make an inference."

    # Get the active window, recent files, and processes from the data
    active_window = recent_data.get("window", "")
    recent_files = recent_data.get("recent_files", [])
    top_processes = recent_data.get("top_processes", [])
    
    # Get time context
    time_context = get_time_context()
    time_suggestion = inference_rules["time_context"].get(time_context, "")
    
    # Extract project context
    project = extract_project_context(recent_files)
    project_context = f"You're working on the {project} project." if project else ""
    
    # Analyze window title for context
    window_analysis = analyze_window_title(active_window)
    
    # Basic inferences
    file_inferences = [match_file_extension(file) for file in recent_files if file]
    process_inferences = [match_process(process) for process in top_processes if process]
    
    # Analyze patterns over time
    frequent_windows = []
    frequent_files = []
    frequent_processes = []
    
    if patterns:
        # Use pre-computed patterns if available
        frequent_windows = patterns.get("frequent_windows", [])
        frequent_files = patterns.get("frequent_files", [])
        frequent_processes = patterns.get("frequent_processes", [])
    else:
        # Compute patterns from history
        window_counter = Counter()
        file_counter = Counter()
        process_counter = Counter()
        
        for entry in history:
            if isinstance(entry, dict):
                window_counter[entry.get("window", "")] += 1
                file_counter.update(entry.get("recent_files", []))
                process_counter.update(entry.get("top_processes", []))
        
        frequent_windows = window_counter.most_common(3)
        frequent_files = file_counter.most_common(3)
        frequent_processes = process_counter.most_common(3)
    
    # Generate weighted suggestions
    suggestions = []
    
    # Window and time-based suggestions (high priority)
    suggestions.append((window_analysis, 5))
    if time_suggestion:
        suggestions.append((time_suggestion, 4))
    if project_context:
        suggestions.append((project_context, 4))
    
    # File-based suggestions (medium priority)
    for inference in file_inferences:
        if inference:
            suggestions.append((inference, 3))
    
    # Process-based suggestions (medium priority)
    for inference in process_inferences:
        if inference:
            suggestions.append((inference, 3))
    
    # Generate workflow-based suggestions
    if frequent_windows:
        current_window = active_window
        next_possible_windows = [w for w, _ in frequent_windows if w != current_window]
        if next_possible_windows:
            suggestions.append((f"Consider switching to {next_possible_windows[0]} next based on your workflow patterns.", 2))
    
    # Generate task completion suggestions
    if "Code.exe" in top_processes and any(file.endswith(('.py', '.js', '.html', '.css')) for file in recent_files):
        suggestions.append(("Remember to test your code before committing changes.", 3))
    
    if "msedge.exe" in top_processes or "chrome.exe" in top_processes:
        suggestions.append(("Consider saving important research to a document for reference.", 2))
    
    # Choose the best suggestion based on weights
    if suggestions:
        # Sort by weight (descending)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        # Get all suggestions with the highest weight
        top_weight = suggestions[0][1]
        top_suggestions = [s for s, w in suggestions if w == top_weight]
        
        # Return a random one from the top-weighted suggestions
        return random.choice(top_suggestions)
    
    return "No specific suggestions at this time."

# Generate more specific suggestions based on patterns
def generate_suggestion(inferences):
    # Replace the random choice with a more targeted approach
    if not inferences:
        return "No insights available at the moment."
    
    # Filter out empty inferences
    valid_inferences = [inf for inf in inferences if inf]
    
    if not valid_inferences:
        return "Continue with your current task."
    
    return random.choice(valid_inferences)

# Enhanced main function
def inference_engine(file_path, patterns_path="zeroinput_patterns.json"):
    print("Running Inference Engine...")
    
    # Load real-time data
    user_data = load_user_data(file_path)
    if not user_data:
        print("No data loaded, unable to make inferences.")
        return "No user data available"
    
    # Load patterns if available
    patterns = load_patterns(patterns_path)
    
    # Report data quality
    if isinstance(user_data, list):
        valid_entries = sum(1 for entry in user_data if 
                          isinstance(entry, dict) and 
                          entry.get("window") and 
                          entry.get("recent_files") and 
                          entry.get("top_processes"))
        
        print(f"Data quality: {valid_entries}/{len(user_data)} valid entries ({valid_entries/max(1, len(user_data)):.0%})")
    
    # Generate and print suggestion
    suggestion = make_inference(user_data, patterns)
    print(f"Suggested Action: {suggestion}")
    
    return suggestion

# Path to your files
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_memory.json")
patterns_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_patterns.json")

# Run the inference engine with real-time user data
if __name__ == "__main__":
    inference_engine(file_path, patterns_path)