import json
import traceback

from PyPDF2 import PdfReader


def read_file(file) -> str:
    """Read text from a Streamlit UploadedFile or file-like object with .name and read/seek."""
    name = getattr(file, "name", "") or ""
    if hasattr(file, "seek"):
        file.seek(0)

    if name.lower().endswith(".pdf"):
        try:
            reader = PdfReader(file)
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            text = "\n".join(parts).strip()
            if not text:
                raise ValueError("No text could be extracted from the PDF (it may be scanned images).")
            return text
        except Exception as e:
            raise RuntimeError(f"Error reading the PDF file: {e}") from e

    if name.lower().endswith(".txt"):
        raw = file.read()
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw)

    raise ValueError("Unsupported file format; only PDF and TXT are supported.")


def get_table_data(quiz_str):
    try:
        quiz_dict = json.loads(quiz_str)
        quiz_table_data = []

        for _key, value in quiz_dict.items():
            mcq = value["mcq"]
            options = " || ".join(
                [f"{option}-> {option_value}" for option, option_value in value["options"].items()]
            )
            correct = value["correct"]
            quiz_table_data.append({"MCQ": mcq, "Choices": options, "Correct": correct})

        return quiz_table_data

    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        return False
