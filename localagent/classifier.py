from pathlib import Path

EXTENSION_MAP = {
    ".pdf":  "PDFs",
    ".doc":  "Docs",
    ".docx": "Docs",
    ".txt":  "Text",
    ".md":   "Text",
    ".jpg":  "Images",
    ".jpeg": "Images",
    ".png":  "Images",
    ".gif":  "Images",
    ".webp": "Images",
    ".mp4":  "Videos",
    ".mov":  "Videos",
    ".mp3":  "Audio",
    ".wav":  "Audio",
    ".zip":  "Archives",
    ".tar":  "Archives",
    ".gz":   "Archives",
    ".csv":  "Data",
    ".json": "Data",
    ".xlsx": "Data",
    ".py":   "Code",
    ".js":   "Code",
    ".html": "Code",
}

def classify(file_path):
    extension  = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(extension, "Misc")

"""

OBSERVE = main.py scans the folder
THINK = classifier.py decides what each file is
ACT = actions.py moves it
LOG = utils.py records it

"""