import time
import json
import psutil
import pygetwindow as gw
from plyer import notification

# Load memory
with open("zeroinput_patterns.json", "r") as f:
    memory = json.load(f)

def get_active_window_title():
    try:
        win = gw.getActiveWindow()
        return win.title if win else None
    except:
        return None

def get_running_processes():
    return [p.name() for p in psutil.process_iter(['name'])]

def match_pattern(active_window, processes):
    triggered = []
    
    # Check for frequent window matches
    for win, count in memory.get("frequent_windows", []):
        if win in active_window:
            triggered.append(f"Window matched: {win}")

    # Check for process patterns
    for proc, count in memory.get("frequent_processes", []):
        if proc in processes:
            triggered.append(f"Process running: {proc}")

    return triggered

def notify_user(message):
    notification.notify(
        title="ZeroInput Suggestion 💡",
        message=message,
        timeout=5
    )

def main_loop():
    seen_windows = set()
    
    while True:
        active_window = get_active_window_title()
        running_procs = get_running_processes()

        if active_window and active_window not in seen_windows:
            matches = match_pattern(active_window, running_procs)
            if matches:
                suggestion = "You're working on something familiar.\n" + "\n".join(matches)
                notify_user(suggestion)
                print("🔔", suggestion)
                seen_windows.add(active_window)

        time.sleep(5)  # Poll every 5 seconds

if __name__ == "__main__":
    main_loop()
