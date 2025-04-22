import os
import subprocess
import re
import webbrowser
#import pyautogui
import time
from typing import Dict, Any

def extract_action_from_suggestion(suggestion: str) -> Dict[str, Any]:
    """Extract actionable components from a suggestion text"""
    if not suggestion:
        return {'type': None, 'target': None}
    
    action_info = {
        'type': None,
        'target': None,
        'params': {}
    }
    
    # Check if this is a keyboard shortcut suggestion
# Replace the shortcut_match regex with this improved version
    shortcut_match = re.search(
        r'(?:try|use|press)\s+(?:the\s+)?'  # Action words
        r'((?:ctrl|alt|shift|win|tab|esc|spacebar|space bar|enter|delete|backspace|home|end|page up|page down)'
        r'(?:\s*\+\s*(?:shift|alt|ctrl|tab|[a-z0-9]))?'  # First combination
        r'(?:\s*\+\s*(?:shift|alt|ctrl|tab|[a-z0-9]))?)',  # Second combination (optional),
        suggestion.lower()
    )
    if shortcut_match:
        action_info['type'] = 'keyboard_shortcut'
        action_info['target'] = shortcut_match.group(1).strip()
        return action_info
    
    # Check for app files with extensions
    app_file_match = re.search(r'(\w+\.py|\w+\.exe|\w+\.json)', suggestion)
    if app_file_match:
        action_info['type'] = 'open_app'
        action_info['target'] = app_file_match.group(1)
        return action_info
    
    # Check for app opening patterns
    app_patterns = [
        r'open\s+([\w\s\.]+)',
        r'switch to\s+([\w\s\.]+)',
        r'use\s+([\w\s\.]+)',
        r'open it now\?',  # Special case for ML suggestions
        r'ready to switch\?'  # Special case for ML suggestions
    ]
    
    for pattern in app_patterns:
        match = re.search(pattern, suggestion.lower())
        if match:
            # Special cases for ML suggestions that don't explicitly name the app
            if pattern in ['r\'open it now\?\'', 'r\'ready to switch\?\'']:
                # Try to extract app name from earlier in the sentence
                app_name_match = re.search(r'([\w\s\.]+)(?:\s+next|after)', suggestion)
                if app_name_match:
                    action_info['type'] = 'open_app'
                    action_info['target'] = app_name_match.group(1).strip()
                    return action_info
            else:
                target = match.group(1).strip().rstrip('?.,!')
                if target not in ['it', 'this', 'that', 'them', 'they', 'these', 'those']:
                    action_info['type'] = 'open_app'
                    action_info['target'] = target
                    return action_info
    
    # Check for non-actionable suggestions
    non_actionable_indicators = [
        'shortcut', 'keyboard', 'tip', 'consider', 'try', 
        'ctrl+', 'alt+', 'shift+', 'tutorial', 'faster', 'speed'
    ]
    
    if any(indicator in suggestion.lower() for indicator in non_actionable_indicators):
        action_info['type'] = 'show_tip'
        action_info['target'] = suggestion
        return action_info
    
    # Extract app name from ML model suggestions like:
    # "You sometimes use main.py in this context. Would you like to open it?"
    ml_suggestion_match = re.search(r'sometimes use\s+([\w\s\.]+)\s+in this context', suggestion)
    if ml_suggestion_match:
        action_info['type'] = 'open_app'
        action_info['target'] = ml_suggestion_match.group(1).strip()
        return action_info
    
    # Check for website suggestions
    website_match = re.search(r'([\w\.-]+\.(com|org|net|io|dev))', suggestion.lower())
    if website_match:
        action_info['type'] = 'open_website'
        action_info['target'] = website_match.group(1)
        return action_info
    
    return action_info

def execute_action(action_info: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the specified action and return status"""
    result = {
        'success': False,
        'info_only': False,
        'message': ""
    }
    
    if not action_info or 'type' not in action_info or not action_info['type']:
        result['message'] = "No actionable information found in suggestion"
        return result
    
    action_type = action_info['type']
    target = action_info.get('target', '')
    
    print(f"Executing action: {action_type} -> {target}")
    
    if action_type == 'open_app':
        success = open_application(target)
        result['success'] = success
        result['message'] = f"Successfully opened {target}" if success else f"Failed to open {target}"
        
    elif action_type == 'open_website':
        success = open_website(target)
        result['success'] = success
        result['message'] = f"Successfully opened website {target}" if success else f"Failed to open website {target}"
        
    elif action_type == 'keyboard_shortcut':
        # Mark as information-only instead of failure
        result['info_only'] = True
        result['message'] = f"TIP: Try using the keyboard shortcut {target}"
        print(f"This suggestion recommends keyboard shortcut: {target}")
        print("Keyboard shortcuts execution is not implemented for safety reasons")
        
    elif action_type == 'show_tip':
        # Mark as information-only instead of failure
        result['info_only'] = True 
        result['message'] = f"TIP: {target}"
        print(f"This is a helpful tip: {target}")
        
    return result

def open_application(app_name: str) -> bool:
    """Open an application by name"""
    if not app_name:
        return False
    
    # Common applications mapping
    app_mapping = {
        'chrome': 'chrome.exe',
        'google chrome': 'chrome.exe',
        'firefox': 'firefox.exe',
        'edge': 'msedge.exe',
        'microsoft edge': 'msedge.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'notepad': 'notepad.exe',
        'visual studio code': 'code.exe',
        'vscode': 'code.exe',
        'code': 'code.exe',
        'explorer': 'explorer.exe',
        'file explorer': 'explorer.exe',
    }
    
    # Try to find a matching app
    executable = app_mapping.get(app_name.lower(), None)
    
    # If no mapping found, check if app_name is already an executable
    if not executable and app_name.lower().endswith('.exe'):
        executable = app_name
    
    # Try to run the executable
    if executable:
        try:
            subprocess.Popen(executable)
            return True
        except FileNotFoundError:
            print(f"Could not find executable: {executable}")
    
    # Look for Python files in the project
    if app_name.endswith('.py'):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, _, files in os.walk(project_dir):
            if app_name in files:
                try:
                    subprocess.Popen(['python', os.path.join(root, app_name)])
                    return True
                except:
                    pass
    
    print(f"Could not find or open application: {app_name}")
    return False

def open_file(file_path: str) -> bool:
    """Open a file with its default application"""
    if not file_path:
        return False
    
    # Try to use the system's default application to open the file
    try:
        os.startfile(file_path)
        return True
    except:
        pass
    
    # If the direct open failed, try looking in common locations
    search_dirs = [
        os.path.expanduser('~/Documents'),
        os.path.expanduser('~/Desktop'),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ]
    
    for directory in search_dirs:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower() == file_path.lower() or file_path.lower() in file.lower():
                    try:
                        os.startfile(os.path.join(root, file))
                        return True
                    except:
                        continue
    
    print(f"Could not find or open file: {file_path}")
    return False

def open_website(url: str) -> bool:
    """Open a website in the default browser"""
    if not url:
        return False
    
    # Ensure URL has proper format
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"Error opening website: {e}")
        return False

# For testing
if __name__ == "__main__":
    # Test the action extraction and execution
    test_suggestions = [
        "You might want to open Chrome to check your emails.",
        "Switch to Visual Studio Code to continue your project.",
        "Would you like to open notepad.exe?",
        "You often visit github.com after coding. Would you like to check it now?",
        "Consider opening the document report.docx to review your work."
    ]
    
    for suggestion in test_suggestions:
        print(f"\nTesting suggestion: '{suggestion}'")
        action = extract_action_from_suggestion(suggestion)
        print(f"Extracted action: {action}")
        # Uncomment to test execution: execute_action(action)