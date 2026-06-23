import PyPDF2
import docx
import io


def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()
        return text if text else "No text found in PDF"
    except Exception as e:
        return f"Error reading PDF: {e}"


def extract_text_from_docx(file_content: bytes) -> str:
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = "\n".join(p.text for p in doc.paragraphs if p.text).strip()
        return text if text else "No text found in Word document"
    except Exception as e:
        return f"Error reading Word document: {e}"
