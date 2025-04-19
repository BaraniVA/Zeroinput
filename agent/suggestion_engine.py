import subprocess
import json
import os
import random
import re
from collections import Counter
from datetime import datetime
from agent.memory_store import load_memory
from agent.context_tracker import get_active_window_title, get_recent_files, get_top_processes

# Enhanced app suggestions with more specific actionable tips
APP_SUGGESTIONS = {
    "default": [
        "Try exploring the interface for hidden productivity tools.",
        "Consider organizing your workspace with Win+Arrow keys for better multitasking.",
        "Take a quick screenshot with Win+Shift+S to capture important information.",
        "Try using the clipboard history with Win+V to access previously copied items."
    ],
    "email": [
    "Use Gmail's keyboard shortcuts by enabling them in Settings (press '?' to see available shortcuts).",
    "Try using Gmail's 'Schedule Send' feature by clicking the arrow next to the Send button.",
    "Use Gmail's search operators like 'from:' or 'has:attachment' for more powerful search.",
    "Create filters to automatically organize incoming mail by going to Settings > Filters.",
    "Use labels and folders to organize your emails by dragging emails or using the Labels button.",
    "Try using Gmail's 'Snooze' feature to temporarily hide emails until you need them.",
    "Use the 'Important first' inbox category to prioritize your most critical messages.",
    "Check out Gmail's Smart Compose feature to write emails faster with AI suggestions.",
    "Try Gmail's templates feature for frequently sent emails (enable in Advanced Settings).",
    "Use 'g then i' keyboard shortcut to quickly return to your inbox from anywhere in Gmail."
    ], 
    "canva": [
        "Try adjusting your canvas tools for creative efficiency.",
        "Use the keyboard shortcut Ctrl+G to group elements for easier manipulation.",
        "Try Canva's magic resize to repurpose your design for different platforms.",
        "Use the alignment tools (select objects and look for the alignment options) to create polished designs.",
        "Consider using Canva's Brand Kit to maintain consistency across your designs."
    ],
    "code": [
        "Use keyboard shortcuts for fast code navigation.",
        "Try Ctrl+Shift+P to open Command Palette for quick access to VS Code commands.",
        "Consider using Live Share to collaborate with team members in real-time.",
        "Try Ctrl+F to search within the current file or Ctrl+Shift+F to search across all files.",
        "Use Alt+Z to toggle word wrap for better code readability."
    ],
    "document": [
        "Try utilizing track changes for better revision control.",
        "Use Ctrl+Shift+V to paste without formatting for cleaner documents.",
        "Try using styles (Ctrl+Alt+1,2,3) to maintain consistent document structure.",
        "Consider using the Navigation pane (View > Navigation) to move quickly through document sections."
    ],
    "presentation": [
        "Set up slide transitions to enhance your presentation.",
        "Try using Alt+N to create a new slide quickly.",
        "Consider using Presenter View to see your notes while presenting.",
        "Try F5 to start the presentation from the beginning or Shift+F5 from the current slide."
    ],
    "email": [
        "Manage your inbox with filters and quick replies.",
        "Try using Ctrl+R to reply to the current email quickly.",
        "Consider scheduling emails to send later for better communication timing.",
        "Try using email templates for frequently sent message types."
    ],
    "browser": [
        "Organize your tabs with groupings or pinned tabs.",
        "Try Ctrl+Shift+T to reopen recently closed tabs.",
        "Consider using bookmark folders to organize your research topics.",
        "Try Ctrl+Tab to quickly cycle through your open tabs.",
        "Use Ctrl+D to bookmark the current page for easy reference later."
    ],
    "video": [
        "Use editing shortcuts to trim your clips faster.",
        "Try J, K, and L keys for navigating video playback (back, pause, forward).",
        "Consider using YouTube's playback speed controls (shift+, and shift+.) for faster viewing.",
        "Try using the spacebar to quickly pause and resume playback."
    ]
}

# Add this function to generate workflow sequence suggestions
def generate_workflow_suggestion(patterns, current_app):
    """Generate suggestions based on observed application sequences"""
    if not patterns.get('next_apps') or not patterns.get('next_apps')[0]:
        return None
        
    next_app, frequency = patterns['next_apps'][0]
    
    # Only suggest if the pattern has happened multiple times (threshold)
    if frequency < 3:
        return None
        
    # Create different types of workflow suggestions
    suggestions = [
        f"You often open {next_app} after using {current_app}. Would you like to open it now?",
        f"Based on your patterns, you typically switch to {next_app} next. Ready to make the switch?",
        f"I notice you frequently use {next_app} after {current_app}. Consider opening it to continue your workflow.",
        f"Your usual workflow: {current_app} → {next_app}. Want to continue this pattern?"
    ]
    
    return random.choice(suggestions)

# Keep existing APP_SUGGESTIONS as a fallback, but don't rely on it exclusively

def extract_application_from_window(window_title):
    """Extract the likely application name from a window title"""
    # Common patterns in window titles
    patterns = [
        r"(.+?) - .+",  # Pattern: "Document - Application"
        r".+ - (.+)",   # Pattern: "Application - Document" 
        r"(.+?)\s*[\[\(].*?[\]\)]",  # Pattern: "Application [status]" or "Application (status)"
        r"(.+?):\s",    # Pattern: "Application: Document"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, window_title)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, return the first word or the whole title if short
    words = window_title.split()
    return words[0] if words else window_title

def analyze_user_patterns(memory_data, current_window, current_files, current_processes):
    """Analyze user behavior patterns from memory data"""
    if not memory_data or not isinstance(memory_data, list):
        return {}
    
    patterns = {}
    
    # Extract the current application context
    current_app = extract_application_from_window(current_window)
    
    # Count frequency of applications used
    app_counter = Counter()
    for entry in memory_data:
        if isinstance(entry, dict) and 'window' in entry:
            app = extract_application_from_window(entry['window'])
            app_counter[app] += 1
    
    patterns['frequent_apps'] = app_counter.most_common(5)
    
    # Find workflow sequences (what apps are used before/after current app)
    next_apps = Counter()
    previous_apps = Counter()
    
    for i in range(1, len(memory_data)):
        if (isinstance(memory_data[i], dict) and 'window' in memory_data[i] and
            isinstance(memory_data[i-1], dict) and 'window' in memory_data[i-1]):
            
            current = extract_application_from_window(memory_data[i]['window'])
            previous = extract_application_from_window(memory_data[i-1]['window'])
            
            if current == current_app:
                previous_apps[previous] += 1
            
            if previous == current_app:
                next_apps[current] += 1
    
    patterns['previous_apps'] = previous_apps.most_common(3)
    patterns['next_apps'] = next_apps.most_common(3)
    
    # Analyze time patterns
    time_of_day = {}
    for entry in memory_data:
        if isinstance(entry, dict) and 'timestamp' in entry:
            try:
                timestamp = entry['timestamp']
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                hour = dt.hour
                
                # Categorize into morning, afternoon, evening, night
                time_category = (
                    "morning" if 5 <= hour < 12 else
                    "afternoon" if 12 <= hour < 17 else
                    "evening" if 17 <= hour < 22 else
                    "night"
                )
                
                time_of_day[time_category] = time_of_day.get(time_category, 0) + 1
            except (ValueError, TypeError):
                pass
    
    patterns['time_of_day'] = time_of_day
    
    # Find common files used with this application
    files_with_app = Counter()
    for entry in memory_data:
        if (isinstance(entry, dict) and 'window' in entry and 
            extract_application_from_window(entry['window']) == current_app and
            'recent_files' in entry and isinstance(entry['recent_files'], list)):
            
            for file in entry['recent_files']:
                if file:
                    basename = os.path.basename(file)
                    files_with_app[basename] += 1
    
    patterns['frequent_files_with_app'] = files_with_app.most_common(3)
    
    # Find common processes used with this application
    processes_with_app = Counter()
    for entry in memory_data:
        if (isinstance(entry, dict) and 'window' in entry and 
            extract_application_from_window(entry['window']) == current_app and
            'top_processes' in entry and isinstance(entry['top_processes'], list)):
            
            for process in entry['top_processes']:
                if process:
                    processes_with_app[process] += 1
    
    patterns['frequent_processes_with_app'] = processes_with_app.most_common(5)
    
    # Find usage duration patterns
    if len(memory_data) >= 2:
        # Rough estimate of how long user typically spends in applications
        app_durations = {}
        current_app = None
        start_time = None
        
        for entry in memory_data:
            if isinstance(entry, dict) and 'window' in entry and 'timestamp' in entry:
                try:
                    app = extract_application_from_window(entry['window'])
                    time_obj = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                    
                    if app != current_app:
                        # App changed, calculate duration for previous app
                        if current_app and start_time:
                            duration = (time_obj - start_time).total_seconds() / 60  # in minutes
                            if current_app not in app_durations:
                                app_durations[current_app] = []
                            app_durations[current_app].append(duration)
                        
                        current_app = app
                        start_time = time_obj
                except (ValueError, TypeError):
                    pass
        
        # Calculate average durations
        avg_durations = {}
        for app, durations in app_durations.items():
            if durations:
                avg_durations[app] = sum(durations) / len(durations)
        
        patterns['avg_app_duration'] = {k: round(v, 1) for k, v in avg_durations.items()}
    
    return patterns

def generate_personalized_suggestion(current_window, recent_files, top_processes, memory_data=None):
    """Generate a personalized suggestion based on user patterns"""
    if not memory_data:
        memory_data = load_memory()
    
    # Analyze patterns from memory data
    patterns = analyze_user_patterns(memory_data, current_window, recent_files, top_processes)
    
    # Extract current application context
    current_app = extract_application_from_window(current_window)
    
    # First priority: Check for application workflow sequences
    # This addresses the user's request about "always open YouTube after VS Code"
    workflow_suggestion = generate_workflow_suggestion(patterns, current_app)
    if workflow_suggestion:
        return workflow_suggestion
    
    # Continue with existing insights generation...
    insights = []
    
    # Workflow pattern insights (more general than the specific suggestion above)
    if patterns.get('next_apps'):
        next_app = patterns['next_apps'][0][0]
        insights.append(f"Consider preparing your {next_app} workflow, as you often switch to it after {current_app}.")
    
    # Rest of the function remains the same...
    
    # Time-based insights
    now = datetime.now()
    hour = now.hour
    time_category = (
        "morning" if 5 <= hour < 12 else
        "afternoon" if 12 <= hour < 17 else
        "evening" if 17 <= hour < 22 else
        "night"
    )
    
    if time_category == "evening" or time_category == "night":
        insights.append(f"Consider turning on night mode to reduce eye strain while working late.")
    
    # Duration-based insights
    if current_app in patterns.get('avg_app_duration', {}):
        avg_duration = patterns['avg_app_duration'][current_app]
        if avg_duration > 45:  # If user typically spends more than 45 minutes
            insights.append(f"You typically spend {avg_duration:.1f} minutes in {current_app}. Consider setting a timer for breaks.")
    
    # File-based insights
    if patterns.get('frequent_files_with_app'):
        common_file = patterns['frequent_files_with_app'][0][0]
        insights.append(f"You often work with {common_file} in {current_app}. Consider creating a shortcut for quick access.")
    
    # Use these insights to create a well-formed suggestion
    if insights:
        return random.choice(insights)
    
    # Fallback to category-based suggestions if no insights
    category = get_context_category(current_window, top_processes)
    if category in APP_SUGGESTIONS:
        return random.choice(APP_SUGGESTIONS[category])
    
    # Ultimate fallback
    return f"Try exploring the {current_app} interface for features that could speed up your current workflow."

def get_context_category(window_title, processes):
    """Determine the general category of work being done"""
    window_lower = window_title.lower()
    
    # Check for common applications in window title or processes
    if "gmail" in window_lower or "mail.google" in window_lower:
        return "email"
    elif "docs.google" in window_lower:
        return "document"
    elif "slides.google" in window_lower:
        return "presentation"
    elif "sheets.google" in window_lower:
        return "spreadsheet"
    elif "youtube" in window_lower:
        return "video"
    elif "canva" in window_lower:
        return "canva"
    elif "visual studio code" in window_lower or "vs code" in window_lower or "code.exe" in [p.lower() for p in processes]:
        return "code"
    elif "word" in window_lower or "document" in window_lower or ".doc" in window_lower:
        return "document"
    elif "powerpoint" in window_lower or "presentation" in window_lower or ".ppt" in window_lower:
        return "presentation"
    elif "outlook" in window_lower or "mail" in window_lower or "gmail" in window_lower:
        return "email"
    elif "chrome" in window_lower or "edge" in window_lower or "firefox" in window_lower or "browser" in window_lower:
        return "browser"
    elif "premiere" in window_lower or "video" in window_lower or "youtube" in window_lower:
        return "video"
    
    # Check processes for clues
    for process in processes:
        process_lower = process.lower()
        if "canva" in process_lower:
            return "canva"
        elif "code" in process_lower or "visual studio" in process_lower:
            return "code"
        elif "word" in process_lower:
            return "document"
        elif "powerpoint" in process_lower:
            return "presentation"
        elif "outlook" in process_lower or "thunderbird" in process_lower:
            return "email"
        elif "chrome" in process_lower or "firefox" in process_lower or "edge" in process_lower:
            return "browser"
        elif "premiere" in process_lower or "vegas" in process_lower or "video" in process_lower:
            return "video"
    
    return "default"

def get_smart_suggestion(window, files, processes):
    """Get a more intelligent suggestion based on context patterns"""
    # First try to generate a personalized suggestion based on patterns
    personalized = generate_personalized_suggestion(window, files, processes)
    if personalized:
        return personalized
        
    # Fallback to category-based suggestions
    category = get_context_category(window, processes)
    relevant_suggestions = APP_SUGGESTIONS.get(category, APP_SUGGESTIONS["default"])
    return random.choice(relevant_suggestions)

def get_ml_suggestion(window_title, recent_windows):
    """Get suggestion from ML model based on recent activity"""
    try:
        # Import the ML predictor module
        from agent.ml.ml_predictor import predict_next_app, generate_suggestion_from_prediction
        
        # Make prediction
        prediction = predict_next_app(recent_windows)
        
        # Generate suggestion if prediction is available
        if prediction:
            suggestion = generate_suggestion_from_prediction(prediction, window_title)
            if suggestion:
                print(f"ML model suggested: {suggestion}")
                return suggestion
    except Exception as e:
        print(f"Error using ML model for suggestion: {e}")
    
    return None

def build_prompt():
    """Build a better prompt for the LLM with specific guidance"""
    memory = load_memory()[-10:]  # Get recent activity 
    window = get_active_window_title()
    files = get_recent_files()[:5]  # Get more files for context
    procs = get_top_processes()
    
    # Extract application name
    app_name = extract_application_from_window(window)
    
    # Analyze patterns to include in prompt
    patterns = analyze_user_patterns(memory, window, files, procs)
    
    # Format pattern information for the prompt
    pattern_info = ""
    if patterns:
        if patterns.get('next_apps'):
            pattern_info += f"- User often switches to {patterns['next_apps'][0][0]} after using {app_name}\n"
        
        if patterns.get('frequent_files_with_app'):
            files_str = ", ".join(f[0] for f, _ in patterns['frequent_files_with_app'][:2])
            pattern_info += f"- User frequently works with these files in {app_name}: {files_str}\n"
        
        if app_name in patterns.get('avg_app_duration', {}):
            pattern_info += f"- User typically spends {patterns['avg_app_duration'][app_name]:.1f} minutes in {app_name}\n"

    prompt = f"""
You are ZeroInput, an intelligent AI assistant that provides personalized productivity suggestions based on the user's current context and past behavior patterns.

Current user activity:
- Active Window: {window}
- Application: {app_name}
- Recent Files: {', '.join(os.path.basename(f) for f in files) if files else 'None'}
- Running Processes: {', '.join(procs) if procs else 'None'}

User behavior patterns:
{pattern_info}

Your task is to provide ONE specific, actionable suggestion that would help the user be more productive with {app_name} right now.

Guidelines:
1. Be specific to {app_name} and the user's current task
2. Provide a practical, immediately useful tip (e.g., keyboard shortcuts, features, best practices)
3. Start with a verb when possible (e.g., "Use", "Try", "Consider")
4. Keep it concise - a single sentence of actionable advice
5. Focus on helping the user work more efficiently or effectively
6. Don't just describe what they're doing - add value beyond their current knowledge

Your specific, actionable suggestion (one sentence only):
"""

    return prompt

def ask_phi(prompt):
    """Get suggestion from Phi model with improved timeout"""
    try:
        print("Requesting suggestion from Phi model...")
        
        # Check if Ollama is running first
        check_result = subprocess.run(
            ['ollama', 'list'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        
        if check_result.returncode != 0:
            print("Ollama doesn't seem to be running, falling back to pattern-based suggestions")
            raise Exception("Ollama not running")
        
        # Then try using the LLM with a much longer timeout
        result = subprocess.run(
            ['ollama', 'run', 'phi'],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30  # Increased from 10 to 30 seconds
        )
        response = result.stdout.decode().strip()
        
        # Rest of your function remains the same...
        
        # If we got a valid response and it's not an error message
        if response and not response.startswith("Error:") and len(response) > 10:
            # Clean up the response
            response = response.replace("Your specific, actionable suggestion:", "").strip()
            
            # Filter out non-actionable responses
            if response.lower().startswith(("you are", "i am", "the user is", "this is")):
                print("Received non-actionable response from Phi, falling back to pattern-based suggestions")
                raise Exception("Non-actionable response")
                
            return response
        
        print("Invalid response from Phi, falling back to pattern-based suggestions")
        raise Exception("Invalid Phi response")
        
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"LLM error: {e}, falling back to context-based suggestions")
        
        # Get the current context for a better fallback
        window = get_active_window_title()
        files = get_recent_files()[:3]
        procs = get_top_processes()[:3]
        
        # Use the application-specific suggestion
        category = get_context_category(window, procs)
        if category != "default" and category in APP_SUGGESTIONS:
            print(f"Using {category}-specific suggestions")
            return random.choice(APP_SUGGESTIONS[category])
        
        # Fallback to general smart suggestion
        return get_smart_suggestion(window, files, procs)
    
# Add this new function to suggestion_engine.py
def ask_phi_alternate(prompt):
    """Alternative method to call Ollama with better process management"""
    try:
        print("Using alternative method to call Phi model...")
        import requests
        
        # Use Ollama's HTTP API instead of CLI
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'phi',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=45  # Even longer timeout for API call
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    return result['response'].strip()
            
            print(f"API error: {response.status_code} - {response.text}")
            raise Exception(f"API error: {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise
            
    except Exception as e:
        print(f"Alternative LLM approach error: {e}")
        # Fall back to context-based suggestions
        window = get_active_window_title()
        files = get_recent_files()[:3]
        procs = get_top_processes()[:3]
        
        # Use application-specific suggestion
        category = get_context_category(window, procs)
        if category != "default" and category in APP_SUGGESTIONS:
            print(f"Using {category}-specific suggestions")
            return random.choice(APP_SUGGESTIONS[category])
        
        # Ultimate fallback
        return get_smart_suggestion(window, files, procs)