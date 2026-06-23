import re
import unicodedata


def clean_text(text: str) -> str:
    # Normalize unicode (e.g. ligatures, fancy quotes → standard chars)
    text = unicodedata.normalize("NFKC", text)

    # Remove null bytes and non-printable control characters (keep \n and \t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse runs of spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Strip trailing whitespace from each line
    text = "\n".join(line.strip() for line in text.splitlines())

    # Collapse 3+ consecutive blank lines into two (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
