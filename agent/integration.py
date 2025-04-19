import os
import json
import sys
import random
import re
from collections import Counter
from datetime import datetime



# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.memory_store import analyze_patterns, log_to_memory, load_memory
from agent.context_tracker import get_active_window_title, get_recent_files, get_top_processes
from agent.suggestion_engine import (
    build_prompt, 
    ask_phi, 
    get_smart_suggestion, 
    get_context_category,
    ask_phi_alternate,  # Add this import
    APP_SUGGESTIONS,  # Add this import
    get_ml_suggestion  # Add this import
)

# File paths
MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_memory.json")
PATTERNS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_patterns.json")
LOGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_logs.jsonl")
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "zeroinput_feedback.json")

# Global variable to track last suggestion
_last_suggestion = {
    "text": None,
    "app_name": None,
    "timestamp": None
}

def normalize_app_name(app_name):
    """Normalize application names for consistent comparison"""
    if not app_name:
        return ""
    
    # Convert to lowercase
    name = app_name.lower()
    
    # Remove common file extensions
    extensions = ['.py', '.json', '.txt', '.html', '.js', '.exe', '.md']
    for ext in extensions:
        if name.endswith(ext):
            name = name[:-len(ext)]
    
    # Remove common application indicators
    indicators = [' - visual studio code', ' - google chrome', ' - firefox', 
                 ' - microsoft edge', ' - notepad', ' - word']
    for indicator in indicators:
        if name.endswith(indicator):
            name = name[:-len(indicator)]
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
    
    return name

def clean_memory_file(file_path):
    """Clean up the memory file by removing empty or invalid entries"""
    print("Cleaning memory file...")
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Filter out empty or incomplete entries
        valid_entries = []
        for entry in data:
            if (isinstance(entry, dict) and 
                entry.get("timestamp") and 
                entry.get("window") and 
                isinstance(entry.get("recent_files"), list) and
                isinstance(entry.get("top_processes"), list)):
                valid_entries.append(entry)
        
        # Write back the cleaned data
        with open(file_path, 'w') as file:
            json.dump(valid_entries, file, indent=2)
        
        print(f"Memory file cleaned: {len(valid_entries)} valid entries (removed {len(data) - len(valid_entries)} invalid entries)")
        return True
    except Exception as e:
        print(f"Error cleaning memory file: {e}")
        return False

def update_patterns_file(patterns):
    """Update the patterns file with new analysis"""
    try:
        with open(PATTERNS_FILE, 'w') as file:
            json.dump(patterns, file, indent=4)
        return True
    except Exception as e:
        print(f"Error updating patterns file: {e}")
        return False

def synchronize_components():
    """Synchronize all components to ensure data consistency"""
    print("Synchronizing ZeroInput components...")
    
    # 1. Clean memory file
    clean_memory_file(MEMORY_FILE)
    
    # 2. Analyze current patterns
    patterns = analyze_patterns()
    
    # 3. Update patterns file
    update_patterns_file(patterns)
    
    print("Components synchronized successfully")

def run_complete_cycle():
    """Run a complete cycle of the ZeroInput system"""
    global _last_suggestion
    
    # 1. Get current context
    window = get_active_window_title()
    files = get_recent_files()
    processes = get_top_processes()
    
    # Check if previous suggestion was followed before creating a new one
    record_suggestion_feedback(window)
    
    # 2. Log context to memory
    log_to_memory(window, files, processes)
    
    # 3. Get recent window titles for ML prediction
    memory_data = load_memory()
    recent_windows = [entry['window'] for entry in memory_data[-10:] 
                     if isinstance(entry, dict) and 'window' in entry]
    
    # Generate suggestion using priority order
    suggestion = None
    
    # First try ML prediction (highest priority - most personalized)
    try:
        ml_suggestion = get_ml_suggestion(window, recent_windows)
        if ml_suggestion:
            suggestion = ml_suggestion
    except Exception as e:
        print(f"Error getting ML suggestion: {e}")
    
    # Then try LLM if ML failed
    if not suggestion:
        try:
            prompt = build_prompt()
            suggestion = ask_phi(prompt)
        except Exception as e:
            print(f"Error with LLM suggestion: {e}")
    
    # Fall back to pattern-based if both failed
    if not suggestion:
        suggestion = get_smart_suggestion(window, files, processes)
    
    # Store suggestion for feedback tracking
    if suggestion:
        suggested_app = extract_app_name(window)  # Default to current app
        
        # Try to extract app name from suggestion
        # This is approximate - you may need to refine this extraction method
        potential_apps = re.findall(r'open\s+([\w\s\.]+)', suggestion.lower())
        if not potential_apps:
            potential_apps = re.findall(r'switch to\s+([\w\s\.]+)', suggestion.lower())
        if not potential_apps:
            potential_apps = re.findall(r'use\s+([\w\s\.]+)', suggestion.lower())

        if potential_apps:
            suggested_app = potential_apps[0].strip().rstrip('?.,!')
        
        _last_suggestion = {
            "text": suggestion,
            "app_name": suggested_app,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    return suggestion

def load_feedback_data():
    """Load existing feedback data or create new file if it doesn't exist"""
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as file:
                return json.load(file)
        else:
            # Create initial structure
            initial_data = {
                "suggestions": [],
                "stats": {
                    "total": 0,
                    "followed": 0,
                    "ignored": 0
                }
            }
            with open(FEEDBACK_FILE, 'w') as file:
                json.dump(initial_data, file, indent=2)
            return initial_data
    except Exception as e:
        print(f"Error loading feedback data: {e}")
        return {"suggestions": [], "stats": {"total": 0, "followed": 0, "ignored": 0}}

def save_feedback_data(data):
    """Save feedback data to file"""
    try:
        with open(FEEDBACK_FILE, 'w') as file:
            json.dump(data, file, indent=2)
        return True
    except Exception as e:
        print(f"Error saving feedback data: {e}")
        return False

def extract_app_name(window_title):
    """Extract application name from window title"""
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

def record_suggestion_feedback(current_window):
    """Record feedback on whether the last suggestion was followed"""
    global _last_suggestion
    
    # If there was no previous suggestion, nothing to record
    if not _last_suggestion["text"] or not _last_suggestion["timestamp"]:
        return
    
    # Extract current app name
    current_app = extract_app_name(current_window)
    normalized_current = normalize_app_name(current_app)
    normalized_suggested = normalize_app_name(_last_suggestion["app_name"])
    
    # Check if suggestion was followed using normalized names
    followed = normalized_current == normalized_suggested
    
    # Add fuzzy matching for near matches
    if not followed and normalized_suggested and normalized_current:
        # Check if one is contained within the other
        if (normalized_suggested in normalized_current or 
            normalized_current in normalized_suggested):
            followed = True
        # Check for minimal edit distance for typos
        elif len(normalized_suggested) > 3 and len(normalized_current) > 3:
            # Simple matching - if 80% of characters match
            common_chars = sum(c1 == c2 for c1, c2 in 
                           zip(normalized_suggested, normalized_current))
            max_len = max(len(normalized_suggested), len(normalized_current))
            if common_chars / max_len > 0.8:
                followed = True
    
    # Calculate time since suggestion
    now = datetime.now()
    suggestion_time = datetime.strptime(_last_suggestion["timestamp"], "%Y-%m-%d %H:%M:%S")
    time_diff = (now - suggestion_time).total_seconds()
    
    # Only consider feedback if it's within a reasonable timeframe (5 minutes)
    if time_diff > 300:  # 5 minutes in seconds
        _last_suggestion = {"text": None, "app_name": None, "timestamp": None}
        return
    
    # Load existing feedback data
    feedback_data = load_feedback_data()
    
    # Record this suggestion and outcome
    suggestion_record = {
        "timestamp": _last_suggestion["timestamp"],
        "suggestion_text": _last_suggestion["text"],
        "suggested_app": _last_suggestion["app_name"],
        "followed": followed,
        "time_to_respond": time_diff,
        "current_app": current_app
    }
    
    # Update feedback data
    feedback_data["suggestions"].append(suggestion_record)
    feedback_data["stats"]["total"] += 1
    if followed:
        feedback_data["stats"]["followed"] += 1
    else:
        feedback_data["stats"]["ignored"] += 1
    
    # Save updated feedback data
    save_feedback_data(feedback_data)
    
    # Log the feedback for debugging
    if followed:
        print(f"✅ Suggestion followed: {_last_suggestion['text']}")
    else:
        print(f"❌ Suggestion ignored: {_last_suggestion['text']} (used {current_app} instead)")
    
    # Reset last suggestion after recording feedback
    _last_suggestion = {"text": None, "app_name": None, "timestamp": None}