import json
import os
from datetime import datetime

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

def validate_entry(window, recent_files, processes):
    """Validate data before adding to memory"""
    if not window:
        return False
    if not isinstance(recent_files, list) or not recent_files:
        return False
    if not isinstance(processes, list) or not processes:
        return False
    return True