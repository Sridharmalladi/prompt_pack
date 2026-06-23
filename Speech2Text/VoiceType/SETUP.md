# VoiceType — Setup Guide

## 1. Open in Xcode

```
open "VoiceType.xcodeproj"
```

Set your **Development Team** in Target → Signing & Capabilities (free personal team is fine for local use).

---

## 2. Install faster-whisper

```bash
pip3 install faster-whisper
```

If you use a virtual environment, set the Python path via an env var at launch:

```bash
VOICETYPE_PYTHON=/path/to/venv/bin/python3 open VoiceType.app
```

Or create a launch wrapper script.

---

## 3. Download the Whisper model

```bash
mkdir -p ~/Library/Application\ Support/VoiceType/models/small
curl -L "https://huggingface.co/guillaumekln/faster-whisper-small/resolve/main/model.bin" \
     -o ~/Library/Application\ Support/VoiceType/models/small/model.bin
```

The Dashboard will show **"Ready"** (green) once the file exists.

---

## 4. Grant Permissions

### Microphone
System Settings → Privacy & Security → Microphone → enable VoiceType

### Accessibility
System Settings → Privacy & Security → Accessibility → enable VoiceType

Both are required for the hotkey and text injection to work.
The Dashboard shows red "Required" badges if either is missing.

---

## 5. Build & Run

- **Xcode**: Cmd+R
- **CLI**: `xcodebuild -scheme VoiceType -configuration Debug build`

The app runs as a menu bar item only (no Dock icon).

---

## 6. Usage

| Action | Hotkey |
|--------|--------|
| Start recording | Hold **Control + Shift** |
| Stop & transcribe | Release **Control + Shift** |
| Open Dashboard | Click menu bar icon → Open Dashboard |

---

## 7. Package as .app

Product → Archive → Distribute App → Direct Distribution
Or simply: Product → Show Build Folder in Finder → copy `.app` from `Debug/`

---

## 8. Python path note

If `python3` is not in `/usr/local/bin` or `/opt/homebrew/bin`, set:

```bash
# in ~/.zshrc or as a launchd env var:
launchctl setenv VOICETYPE_PYTHON /full/path/to/python3
```

Then relaunch VoiceType.
