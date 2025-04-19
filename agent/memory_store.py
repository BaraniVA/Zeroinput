import json
import os
from datetime import datetime
from collections import Counter

MEMORY_FILE = "zeroinput_memory.json"

# Load memory from disk
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            print("Error: Memory file is corrupted. Creating new file.")
            return []

# Save memory to disk
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# Append a new memory entry
def log_to_memory(window, recent_files, processes):
    # Validate input data
    if not window or not isinstance(window, str):
        print("Warning: Invalid window title. Skipping memory entry.")
        return False
        
    if not recent_files or not isinstance(recent_files, list):
        print("Warning: Invalid recent files list. Skipping memory entry.")
        return False
        
    if not processes or not isinstance(processes, list):
        print("Warning: Invalid process list. Skipping memory entry.")
        return False
    
    memory = load_memory()
    memory.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "window": window,
        "recent_files": recent_files,
        "top_processes": processes
    })
    save_memory(memory)
    return True

def analyze_patterns():
    memory = load_memory()
    window_counter = Counter()
    file_counter = Counter()
    process_counter = Counter()

    for entry in memory:
        window_counter[entry.get("window", "")] += 1
        for f in entry.get("recent_files", []):
            file_counter[os.path.basename(f)] += 1
        for p in entry.get("top_processes", []):
            process_counter[p] += 1

    print("\n📈 Common Patterns Found:")
    print("🪟 Frequent Windows:", window_counter.most_common(3))
    print("📂 Frequent Files:", file_counter.most_common(3))
    print("⚙️  Frequent Processes:", process_counter.most_common(3))
    
    return {
        "frequent_windows": window_counter.most_common(5),
        "frequent_files": file_counter.most_common(5),
        "frequent_processes": process_counter.most_common(5)
    }