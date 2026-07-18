from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def clean_resume_text(
    text: str,
) -> str:
    cleaned_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    cleaned_text = "\n".join(
        cleaned_lines
    )

    if len(cleaned_text) < 50:
        raise ValueError(
            "Very little text was extracted from the "
            "resume. Upload a text-based PDF, DOCX "
            "or TXT file."
        )

    return cleaned_text


def read_pdf_bytes(
    file_content: bytes,
) -> str:
    reader = PdfReader(
        BytesIO(file_content)
    )

    pages: list[str] = []

    for page in reader.pages:
        pages.append(
            page.extract_text() or ""
        )

    return "\n".join(pages)


def read_docx_bytes(
    file_content: bytes,
) -> str:
    document = Document(
        BytesIO(file_content)
    )

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


def read_txt_bytes(
    file_content: bytes,
) -> str:
    return file_content.decode(
        "utf-8",
        errors="ignore",
    )


def read_resume_bytes(
    file_content: bytes,
    extension: str,
) -> str:
    normalized_extension = (
        extension.lower().strip()
    )

    if normalized_extension == ".pdf":
        text = read_pdf_bytes(
            file_content
        )

    elif normalized_extension == ".docx":
        text = read_docx_bytes(
            file_content
        )

    elif normalized_extension == ".txt":
        text = read_txt_bytes(
            file_content
        )

    else:
        raise ValueError(
            "Only PDF, DOCX and TXT files "
            "are supported."
        )

    return clean_resume_text(
        text
    )


def read_resume_text(
    file_path: Path,
) -> str:
    """
    Compatibility helper for any older code
    that still supplies a Path.
    """

    return read_resume_bytes(
        file_content=file_path.read_bytes(),
        extension=file_path.suffix,
    )
