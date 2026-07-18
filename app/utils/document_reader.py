from pathlib import Path

from docx import Document
from pypdf import PdfReader


def read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))

    pages: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)

    return "\n".join(pages)


def read_docx(file_path: Path) -> str:
    document = Document(str(file_path))

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
    ]

    return "\n".join(paragraphs)


def read_txt(file_path: Path) -> str:
    return file_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )


def read_resume_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        text = read_pdf(file_path)

    elif extension == ".docx":
        text = read_docx(file_path)

    elif extension == ".txt":
        text = read_txt(file_path)

    else:
        raise ValueError(
            "Only PDF, DOCX and TXT files are supported."
        )

    cleaned_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    cleaned_text = "\n".join(cleaned_lines)

    if len(cleaned_text) < 50:
        raise ValueError(
            "Very little text was extracted from the resume. "
            "Upload a text-based PDF, DOCX or TXT file."
        )

    return cleaned_text