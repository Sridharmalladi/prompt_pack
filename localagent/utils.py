import json 
import time
from pathlib import Path


action_log = []

def log_action(file_name, original_path, destination_path, status="moved"):
    entry = {
        "file": file_name,
        "from": str(original_path),
        "to": str(destination_path),
        "status": status,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    action_log.append(entry)

def save_log(output_path="agent_log.json"):
    log_file = Path(output_path)
    with open(log_file, "w") as f:
        json.dump(action_log, f, indent=2)


def print_summary():
    print("\n--- Smart Folder Agent Summary ---")
    print(f"Total files processed: {len(action_log)}")
    for entry in action_log:
        print(f"  [{entry['status'].upper()}] {entry['file']} → {entry['to']}")
    print("----------------------------------\n")