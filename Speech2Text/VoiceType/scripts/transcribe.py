#!/usr/bin/env python3
"""
VoiceType – faster-whisper transcription bridge.
Usage: python3 transcribe.py <audio_file_path>
Prints the transcription to stdout (no trailing newline extras).
"""
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("", end="")
        sys.exit(0)

    audio_path = sys.argv[1]
    if not os.path.exists(audio_path):
        print("", end="")
        sys.exit(0)

    model_dir = os.path.expanduser(
        "~/Library/Application Support/VoiceType/models/small"
    )

    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(
            model_dir,
            device="cpu",
            compute_type="int8",
        )
        segments, _ = model.transcribe(audio_path, language=None, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments)
        print(text.strip(), end="")
    except Exception as e:
        # Surface error to Swift via stderr, print empty to stdout
        print(f"ERROR: {e}", file=sys.stderr)
        print("", end="")
        sys.exit(1)

if __name__ == "__main__":
    main()
