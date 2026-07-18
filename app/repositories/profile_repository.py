from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import (
    supabase_client,
)


class ProfileRepository:
    """
    Handles profile-table operations in Supabase.
    """

    TABLE_NAME = "profiles"
    DEFAULT_PROFILE_NAME = "default"

    def _get_contact(
        self,
        profile_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Safely extract the contact object
        from the analyzed resume profile.
        """

        contact = profile_data.get(
            "contact",
            {},
        )

        if not isinstance(contact, dict):
            return {}

        return contact

    def _build_payload(
        self,
        profile_data: dict[str, Any],
        profile_name: str,
    ) -> dict[str, Any]:
        """
        Convert the complete AI profile into
        the format expected by Supabase.
        """

        contact = self._get_contact(
            profile_data
        )

        full_name = (
            contact.get("full_name")
            or profile_data.get("full_name")
            or ""
        )

        email = (
            contact.get("email")
            or profile_data.get("email")
            or ""
        )

        phone = (
            contact.get("phone")
            or profile_data.get("phone")
            or ""
        )

        location = (
            contact.get("location")
            or profile_data.get("location")
            or ""
        )

        return {
            "profile_name": profile_name,
            "full_name": str(full_name).strip(),
            "email": str(email).strip(),
            "phone": str(phone).strip(),
            "location": str(location).strip(),
            "profile_data": profile_data,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    def save(
        self,
        profile_data: dict[str, Any],
        profile_name: str = DEFAULT_PROFILE_NAME,
    ) -> dict[str, Any]:
        """
        Insert a new profile or update the
        existing default profile.
        """

        if not isinstance(profile_data, dict):
            raise ValueError(
                "Profile data must be a dictionary."
            )

        if not profile_data:
            raise ValueError(
                "Profile data cannot be empty."
            )

        payload = self._build_payload(
            profile_data=profile_data,
            profile_name=profile_name,
        )

        existing_result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("id")
            .eq(
                "profile_name",
                profile_name,
            )
            .limit(1)
            .execute()
        )

        if existing_result.data:
            profile_id = existing_result.data[0][
                "id"
            ]

            result = (
                supabase_client
                .table(self.TABLE_NAME)
                .update(payload)
                .eq("id", profile_id)
                .execute()
            )
        else:
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

    def get_default(
        self,
    ) -> dict[str, Any] | None:
        """
        Get the default profile row.
        """

        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "profile_name",
                self.DEFAULT_PROFILE_NAME,
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

    def get_profile_data(
        self,
    ) -> dict[str, Any]:
        """
        Return only the original complete
        analyzed resume profile.
        """

        profile_row = self.get_default()

        if not profile_row:
            return {}

        profile_data = profile_row.get(
            "profile_data",
            {},
        )

        if not isinstance(profile_data, dict):
            return {}

        return profile_data


profile_repository = ProfileRepository()