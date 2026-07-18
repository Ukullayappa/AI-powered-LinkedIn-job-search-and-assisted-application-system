from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    original_filename: str
    stored_filename: str
    stored_path: str
    extracted_characters: int
    extracted_text_preview: str