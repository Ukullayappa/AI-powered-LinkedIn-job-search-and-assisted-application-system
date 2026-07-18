from __future__ import annotations

from pathlib import Path

from app.repositories.supabase_client import (
    supabase_client,
)


class ResumeStorageService:
    BUCKET_NAME = "resumes"
    DEFAULT_FOLDER = "default"

    def build_storage_path(
        self,
        stored_filename: str,
    ) -> str:
        safe_filename = Path(
            stored_filename
        ).name

        if not safe_filename:
            raise ValueError(
                "Stored resume filename is missing."
            )

        return (
            f"{self.DEFAULT_FOLDER}/"
            f"{safe_filename}"
        )

    def upload_bytes(
        self,
        *,
        file_content: bytes,
        storage_path: str,
        content_type: str,
    ) -> str:
        (
            supabase_client
            .storage
            .from_(self.BUCKET_NAME)
            .upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",
                    "upsert": "true",
                },
            )
        )

        return storage_path

    def download_bytes(
        self,
        storage_path: str,
    ) -> bytes:
        if not storage_path.strip():
            raise ValueError(
                "Resume storage path is missing."
            )

        return (
            supabase_client
            .storage
            .from_(self.BUCKET_NAME)
            .download(
                storage_path
            )
        )

    def remove(
        self,
        storage_path: str,
    ) -> None:
        if not storage_path.strip():
            return

        (
            supabase_client
            .storage
            .from_(self.BUCKET_NAME)
            .remove(
                [storage_path]
            )
        )


resume_storage_service = ResumeStorageService()
