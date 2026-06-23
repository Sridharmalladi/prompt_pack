import shutil
import time
from pathlib import Path

import utils

def move_file(file_path, destination_folder):
    file_path = Path(file_path)
    destination_folder = Path(destination_folder)

    destination_folder.mkdir(parents = True, exist_ok = True)

    destination = destination_folder / file_path.name

    if destination.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        timestamp = str(int(time.time()))
        new_name = f"{stem}_{timestamp}{suffix}"
        destination = destination_folder/new_name

    shutil.move(str(file_path), str(destination))

    utils.log_action(
        file_name = file_path.name,
        original_path = file_path,
        destination_path = destination,
        status="moved"

    )


