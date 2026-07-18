from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.crews.resume_crew import ResumeCrew
from app.repositories.profile_repository import (
    profile_repository,
)
from app.schemas.profile_schema import ResumeProfile
from app.schemas.resume_schema import ResumeUploadResponse
from app.repositories.resume_storage_repository import (
    resume_storage_service,
)
from app.utils.document_reader import (
    read_resume_bytes,
)


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

        extracted_text = await asyncio.to_thread(
            read_resume_bytes,
            file_content,
            extension,
        )

        stored_filename = (
            f"{uuid4().hex}{extension}"
        )

        storage_path = (
            resume_storage_service
            .build_storage_path(
                stored_filename
            )
        )

        content_type = (
            uploaded_file.content_type
            or mimetypes.guess_type(
                original_filename
            )[0]
            or "application/octet-stream"
        )

        old_resume = (
            profile_repository
            .get_resume_record()
        )

        await asyncio.to_thread(
            resume_storage_service.upload_bytes,
            file_content=file_content,
            storage_path=storage_path,
            content_type=content_type,
        )

        try:
            await asyncio.to_thread(
                profile_repository.save_resume_upload,
                original_filename=original_filename,
                content_type=content_type,
                resume_text=extracted_text,
                storage_path=storage_path,
            )

        except Exception:
            await asyncio.to_thread(
                resume_storage_service.remove,
                storage_path,
            )
            raise

        old_storage_path = old_resume.get(
            "storage_path",
            "",
        )

        if (
            old_storage_path
            and old_storage_path != storage_path
        ):
            try:
                await asyncio.to_thread(
                    resume_storage_service.remove,
                    old_storage_path,
                )
            except Exception as error:
                print(
                    "Old cloud resume cleanup skipped:",
                    error,
                )

        return ResumeUploadResponse(
            original_filename=original_filename,
            stored_filename=stored_filename,
            stored_path=storage_path,
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
        resume_record = (
            profile_repository
            .get_resume_record()
        )

        resume_text = resume_record.get(
            "resume_text",
            "",
        )

        if not resume_text:
            raise FileNotFoundError(
                "Upload a resume first."
            )

        profile = await asyncio.to_thread(
            ResumeCrew().run,
            resume_text,
        )

        # The resume now lives only in Supabase.
        profile.raw_resume_path = ""
        profile.extracted_text_path = ""

        await asyncio.to_thread(
            profile_repository.save,
            profile.model_dump(),
        )

        return profile

    def get_profile(
        self,
    ) -> ResumeProfile:
        profile_data = (
            profile_repository
            .get_profile_data()
        )

        if not profile_data:
            raise FileNotFoundError(
                "Analyze the resume first."
            )

        return ResumeProfile.model_validate(
            profile_data
        )

    def get_resume_upload_payload(
        self,
    ) -> dict:
        resume_record = (
            profile_repository
            .get_resume_record()
        )

        storage_path = resume_record.get(
            "storage_path",
            "",
        )

        if not storage_path:
            raise FileNotFoundError(
                "Cloud resume was not found. "
                "Upload the resume again."
            )

        file_content = (
            resume_storage_service
            .download_bytes(
                storage_path
            )
        )

        original_filename = (
            resume_record.get(
                "original_filename",
                "",
            )
            or Path(storage_path).name
        )

        content_type = (
            resume_record.get(
                "content_type",
                "",
            )
            or "application/octet-stream"
        )

        return {
            "name": original_filename,
            "mimeType": content_type,
            "buffer": file_content,
        }


resume_service = ResumeService()
