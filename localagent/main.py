import sys
from pathlib import Path

import classifier
import actions
import utils

SCAN_FOLDER = Path.home() / "Downloads" / "test_downloads"
OUTPUT_FOLDER = Path.home() / "Downloads" / "test_downloads" / "Organized"


def run_agent():
    print(f"\nScanning: {SCAN_FOLDER}")
    print(f"Output:   {OUTPUT_FOLDER}\n")

    files = [f for f in SCAN_FOLDER.iterdir() if f.is_file()]

    if not files:
        print("No files found. Exiting.")
        return

    print(f"Found {len(files)} file(s). Starting...\n")

    for file_path in files:
        category = classifier.classify(file_path)
        destination_folder = OUTPUT_FOLDER / category

        try:
            actions.move_file(file_path, destination_folder)
            print(f"  Moved: {file_path.name}  →  {category}/")
        except Exception as e:
            utils.log_action(
                file_name=file_path.name,
                original_path=file_path,
                destination_path=destination_folder,
                status=f"failed: {str(e)}"
            )
            print(f"  FAILED: {file_path.name} — {str(e)}")

    utils.print_summary()
    utils.save_log(OUTPUT_FOLDER / "agent_log.json")
    print(f"Log saved to: {OUTPUT_FOLDER / 'agent_log.json'}")


if __name__ == "__main__":
    run_agent()