import io
from typing import Literal

import docx2txt
import pdfplumber

FileType = Literal["pdf", "docx", "txt"]


def parse_pdf(file_bytes: bytes) -> str:
    parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                parts.append(page_text)
    return "\n\n".join(parts)


def parse_docx(file_bytes: bytes) -> str:
    return docx2txt.process(io.BytesIO(file_bytes))


def parse_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def parse_file(file_bytes: bytes, file_type: FileType) -> str:
    parsers = {
        "pdf": parse_pdf,
        "docx": parse_docx,
        "txt": parse_txt,
    }
    if file_type not in parsers:
        raise ValueError(f"Unsupported file type: {file_type!r}")
    return parsers[file_type](file_bytes)
