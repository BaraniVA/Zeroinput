import json
from collections import Counter, defaultdict

LOG_FILE = "zeroinput_logs.jsonl"
OUTPUT_FILE = "zeroinput_patterns.json"

def aggregate_patterns():
    window_counter = Counter()
    file_counter = Counter()
    process_counter = Counter()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                window = entry.get("window")
                files = entry.get("recent_files", [])
                processes = entry.get("top_processes", [])

                if window:
                    window_counter[window] += 1
                file_counter.update(files)
                process_counter.update(processes)

            except json.JSONDecodeError:
                continue  # skip bad lines

    result = {
        "frequent_windows": window_counter.most_common(5),
        "frequent_files": file_counter.most_common(5),
        "frequent_processes": process_counter.most_common(5)
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print("✅ Aggregated patterns saved to zeroinput_patterns.json")

if __name__ == "__main__":
    aggregate_patterns()
