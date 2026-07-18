import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.crews.resume_crew import ResumeCrew
from app.schemas.profile_schema import ResumeProfile
from app.schemas.resume_schema import ResumeUploadResponse
from app.utils.document_reader import read_resume_text
from app.utils.json_storage import storage


class ResumeService:
    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt",
    }

    async def upload_resume(
        self,
        uploaded_file: UploadFile,
    ) -> ResumeUploadResponse:
        settings = get_settings()

        original_filename = Path(
            uploaded_file.filename or "resume"
        ).name

        extension = Path(
            original_filename
        ).suffix.lower()

        if extension not in self.allowed_extensions:
            raise ValueError(
                "Only PDF, DOCX and TXT "
                "resumes are supported."
            )

        file_content = await uploaded_file.read()

        if not file_content:
            raise ValueError(
                "The uploaded resume is empty."
            )

        maximum_size = 5 * 1024 * 1024

        if len(file_content) > maximum_size:
            raise ValueError(
                "Resume must be smaller than 5 MB."
            )

        stored_filename = (
            f"{uuid4().hex}{extension}"
        )

        stored_path = (
            settings.upload_directory
            / stored_filename
        )

        stored_path.write_bytes(
            file_content
        )

        try:
            extracted_text = read_resume_text(
                stored_path
            )

        except Exception:
            if stored_path.exists():
                stored_path.unlink()

            raise

        extracted_text_path = (
            settings.upload_directory
            / f"{stored_path.stem}_extracted.txt"
        )

        extracted_text_path.write_text(
            extracted_text,
            encoding="utf-8",
        )

        resume_meta = {
            "original_filename": (
                original_filename
            ),
            "stored_filename": (
                stored_filename
            ),
            "stored_path": str(
                stored_path.resolve()
            ),
            "extracted_text_path": str(
                extracted_text_path.resolve()
            ),
            "extracted_characters": len(
                extracted_text
            ),
        }

        storage.write(
            "resume_meta",
            resume_meta,
        )

        # Remove the old profile whenever
        # a new resume is uploaded.
        storage.write(
            "profile",
            {},
        )

        return ResumeUploadResponse(
            original_filename=original_filename,
            stored_filename=stored_filename,
            stored_path=str(
                stored_path.resolve()
            ),
            extracted_characters=len(
                extracted_text
            ),
            extracted_text_preview=(
                extracted_text[:1000]
            ),
        )

    async def analyze_resume(
        self,
    ) -> ResumeProfile:
        resume_meta = storage.read(
            "resume_meta",
            {},
        )

        if not resume_meta:
            raise FileNotFoundError(
                "Upload a resume first."
            )

        extracted_text_path = Path(
            resume_meta.get(
                "extracted_text_path",
                "",
            )
        )

        if not extracted_text_path.exists():
            raise FileNotFoundError(
                "Extracted resume text was not found. "
                "Upload the resume again."
            )

        resume_text = (
            extracted_text_path.read_text(
                encoding="utf-8"
            )
        )

        profile = await asyncio.to_thread(
            ResumeCrew().run,
            resume_text,
        )

        profile.raw_resume_path = (
            resume_meta["stored_path"]
        )

        profile.extracted_text_path = str(
            extracted_text_path.resolve()
        )

        storage.write(
            "profile",
            profile.model_dump(),
        )

        return profile

    def get_profile(
        self,
    ) -> ResumeProfile:
        profile_data = storage.read(
            "profile",
            {},
        )

        if not profile_data:
            raise FileNotFoundError(
                "Analyze the resume first."
            )

        return ResumeProfile.model_validate(
            profile_data
        )


resume_service = ResumeService()