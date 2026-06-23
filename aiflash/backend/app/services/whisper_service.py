import io

from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

# Audio formats accepted by the Whisper API
_SUPPORTED_FORMATS = {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg"}


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Send audio bytes to OpenAI Whisper and return the transcribed text.
    filename must include a supported extension so Whisper can detect the format.
    Raises ValueError if whisper is disabled or the format is unsupported.
    """
    if not settings.whisper_enabled:
        raise ValueError("Whisper transcription is disabled.")

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in _SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format '.{ext}'. "
            f"Supported: {', '.join(sorted(_SUPPORTED_FORMATS))}"
        )

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename  # Whisper uses the name to detect MIME type

    response = _client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return response.text.strip()
