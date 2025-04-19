import pygetwindow as gw
import pyautogui
import psutil
import os
import time
from datetime import datetime
from agent.memory_store import log_to_memory, analyze_patterns
import json

def save_snapshot(data, log_path="zeroinput_logs.jsonl"):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


# Get active window title
def get_active_window_title():
    try:
        return gw.getActiveWindow().title
    except:
        return "Unknown"

# Get recently modified files from user's Documents and Downloads
def get_recent_files(limit=5):
    search_dirs = [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
    ]
    files = []
    for d in search_dirs:
        if os.path.exists(d):
            for root, _, filenames in os.walk(d):
                for name in filenames:
                    filepath = os.path.join(root, name)
                    try:
                        mod_time = os.path.getmtime(filepath)
                        files.append((filepath, mod_time))
                    except:
                        continue
    files.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in files[:limit]]

# Get list of running processes (top 5 memory usage)
def get_top_processes(limit=5):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem = proc.info['memory_info'].rss
            processes.append((proc.info['name'], mem))
        except:
            continue
    processes.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in processes[:limit]]

# Log context
def log_context():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    window = get_active_window_title()
    recent_files = get_recent_files()
    top_processes = get_top_processes()

    print(f"\n🕒 [{timestamp}]")
    print(f"🪟 Active Window: {window}")
    print("📂 Recent Files:")
    for f in recent_files:
        print(f"   - {os.path.basename(f)}")
    print("⚙️  Top Processes:")
    for p in top_processes:
        print(f"   - {p}")
        log_to_memory(window, recent_files, top_processes)


# Main loop
if __name__ == "__main__":
    print("🔍 ZeroInput Context Tracker Started...")
    log_count = 0
    try:
        while True:
            log_context()
            log_count += 1

            if log_count % 10 == 0:
                print("\n🔍 Analyzing patterns after 10 logs...")
                analyze_patterns()

            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 ZeroInput Tracker Stopped.")

analyze_patterns()