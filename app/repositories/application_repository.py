from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import (
    supabase_client,
)


class ApplicationRepository:
    TABLE_NAME = "applications"

    def get_all(
        self,
    ) -> list[dict[str, Any]]:
        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("*")
            .order(
                "submitted_at",
                desc=True,
            )
            .execute()
        )

        return list(
            result.data or []
        )

    def get_submitted_job_ids(
        self,
    ) -> set[str]:
        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("linkedin_job_id")
            .eq(
                "status",
                "submitted",
            )
            .execute()
        )

        return {
            str(row.get(
                "linkedin_job_id",
                "",
            ))
            for row in (result.data or [])
            if row.get("linkedin_job_id")
        }

    def save_submitted(
        self,
        job: dict[str, Any],
    ) -> dict[str, Any]:
        job_id = str(
            job.get(
                "job_id",
                "",
            )
        ).strip()

        if not job_id:
            raise ValueError(
                "LinkedIn job ID is missing."
            )

        payload = {
            "linkedin_job_id": job_id,
            "title": str(
                job.get(
                    "title",
                    "",
                )
            ),
            "company": str(
                job.get(
                    "company",
                    "",
                )
            ),
            "location": str(
                job.get(
                    "location",
                    "",
                )
            ),
            "url": str(
                job.get(
                    "url",
                    "",
                )
            ),
            "status": "submitted",
            "submitted_at": (
                job.get(
                    "submitted_at"
                )
                or datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        existing = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("id")
            .eq(
                "linkedin_job_id",
                job_id,
            )
            .limit(1)
            .execute()
        )

        if existing.data:
            result = (
                supabase_client
                .table(self.TABLE_NAME)
                .update(payload)
                .eq(
                    "id",
                    existing.data[0]["id"],
                )
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
                "Submitted application was not "
                "saved in Supabase."
            )

        return result.data[0]


application_repository = ApplicationRepository()
