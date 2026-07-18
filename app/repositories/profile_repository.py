from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import (
    supabase_client,
)


class ProfileRepository:
    """
    Stores the candidate profile, extracted resume
    text and Supabase Storage metadata.
    """

    TABLE_NAME = "profiles"
    DEFAULT_PROFILE_NAME = "default"

    def _now(
        self,
    ) -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    def _get_existing(
        self,
        profile_name: str,
    ) -> dict[str, Any] | None:
        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "profile_name",
                profile_name,
            )
            .order(
                "updated_at",
                desc=True,
            )
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return result.data[0]

    def _save_payload(
        self,
        payload: dict[str, Any],
        profile_name: str,
    ) -> dict[str, Any]:
        existing = self._get_existing(
            profile_name
        )

        if existing:
            result = (
                supabase_client
                .table(self.TABLE_NAME)
                .update(payload)
                .eq(
                    "id",
                    existing["id"],
                )
                .execute()
            )
        else:
            payload = {
                "profile_name": profile_name,
                **payload,
            }

            result = (
                supabase_client
                .table(self.TABLE_NAME)
                .insert(payload)
                .execute()
            )

        if not result.data:
            raise RuntimeError(
                "Supabase did not return the "
                "saved profile."
            )

        return result.data[0]

    def save_resume_upload(
        self,
        *,
        original_filename: str,
        content_type: str,
        resume_text: str,
        storage_path: str,
        profile_name: str = DEFAULT_PROFILE_NAME,
    ) -> dict[str, Any]:
        payload = {
            "profile_data": {},
            "full_name": "",
            "email": "",
            "phone": "",
            "location": "",
            "resume_original_filename": (
                original_filename
            ),
            "resume_content_type": content_type,
            "resume_text": resume_text,
            "resume_storage_path": storage_path,
            "updated_at": self._now(),
        }

        return self._save_payload(
            payload=payload,
            profile_name=profile_name,
        )

    def save(
        self,
        profile_data: dict[str, Any],
        profile_name: str = DEFAULT_PROFILE_NAME,
    ) -> dict[str, Any]:
        if not isinstance(
            profile_data,
            dict,
        ):
            raise ValueError(
                "Profile data must be a dictionary."
            )

        if not profile_data:
            raise ValueError(
                "Profile data cannot be empty."
            )

        contact = profile_data.get(
            "contact",
            {},
        )

        if not isinstance(contact, dict):
            contact = {}

        payload = {
            "full_name": str(
                contact.get(
                    "full_name",
                    "",
                )
            ).strip(),
            "email": str(
                contact.get(
                    "email",
                    "",
                )
            ).strip(),
            "phone": str(
                contact.get(
                    "phone",
                    "",
                )
            ).strip(),
            "location": str(
                contact.get(
                    "location",
                    "",
                )
            ).strip(),
            "profile_data": profile_data,
            "updated_at": self._now(),
        }

        return self._save_payload(
            payload=payload,
            profile_name=profile_name,
        )

    def delete_default(
        self,
    ) -> None:
        (
            supabase_client
            .table(self.TABLE_NAME)
            .delete()
            .eq(
                "profile_name",
                self.DEFAULT_PROFILE_NAME,
            )
            .execute()
        )

    def get_default(
        self,
    ) -> dict[str, Any] | None:
        return self._get_existing(
            self.DEFAULT_PROFILE_NAME
        )

    def get_profile_data(
        self,
    ) -> dict[str, Any]:
        profile_row = self.get_default()

        if not profile_row:
            return {}

        profile_data = profile_row.get(
            "profile_data",
            {},
        )

        if not isinstance(
            profile_data,
            dict,
        ):
            return {}

        return profile_data

    def get_resume_record(
        self,
    ) -> dict[str, Any]:
        profile_row = self.get_default()

        if not profile_row:
            return {}

        return {
            "original_filename": str(
                profile_row.get(
                    "resume_original_filename",
                    "",
                )
                or ""
            ),
            "content_type": str(
                profile_row.get(
                    "resume_content_type",
                    "",
                )
                or ""
            ),
            "resume_text": str(
                profile_row.get(
                    "resume_text",
                    "",
                )
                or ""
            ),
            "storage_path": str(
                profile_row.get(
                    "resume_storage_path",
                    "",
                )
                or ""
            ),
        }


profile_repository = ProfileRepository()
