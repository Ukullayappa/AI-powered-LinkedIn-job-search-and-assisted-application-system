from __future__ import annotations

from typing import Any

from app.repositories.supabase_client import (
    supabase_client,
)


class AgentRunRepository:
    TABLE_NAME = "agent_runs"

    def create(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._to_database(state)

        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .insert(payload)
            .execute()
        )

        if not result.data:
            raise RuntimeError(
                "Agent run was not created "
                "in Supabase."
            )

        return self._from_database(
            result.data[0]
        )

    def get_by_run_id(
        self,
        run_id: str,
    ) -> dict[str, Any] | None:
        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("*")
            .eq("run_id", run_id)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return self._from_database(
            result.data[0]
        )

    def get_latest(
        self,
    ) -> dict[str, Any] | None:
        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return self._from_database(
            result.data[0]
        )

    def get_next_queued(
        self,
    ) -> dict[str, Any] | None:
        """
        Return the oldest queued run that has
        not been cancelled.
        """
        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .select("*")
            .eq("status", "queued")
            .eq("stop_requested", False)
            .order(
                "created_at",
                desc=False,
            )
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return self._from_database(
            result.data[0]
        )

    def update(
        self,
        run_id: str,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._to_database(state)

        payload.pop(
            "run_id",
            None,
        )

        result = (
            supabase_client
            .table(self.TABLE_NAME)
            .update(payload)
            .eq(
                "run_id",
                run_id,
            )
            .execute()
        )

        if not result.data:
            raise RuntimeError(
                "Agent run was not updated "
                "in Supabase."
            )

        return self._from_database(
            result.data[0]
        )

    def _to_database(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "run_id": state.get("run_id"),
            "status": state.get(
                "status",
                "idle",
            ),
            "stage": state.get(
                "stage",
                "idle",
            ),
            "message": state.get(
                "message",
                "",
            ),
            "settings": state.get(
                "settings",
                {},
            ),
            "jobs_collected": state.get(
                "jobs_collected",
                0,
            ),
            "best_jobs": state.get(
                "best_jobs",
                0,
            ),
            "current_job_number": state.get(
                "current_job_number",
                0,
            ),
            "current_job_id": (
                state.get("current_job_id")
                or None
            ),
            "current_job_title": (
                state.get("current_job_title")
                or None
            ),
            "submitted_count": state.get(
                "submitted_count",
                0,
            ),
            "failed_count": state.get(
                "failed_count",
                0,
            ),
            "maximum_applications": state.get(
                "maximum_applications",
                5,
            ),
            "stop_requested": state.get(
                "stop_requested",
                False,
            ),
            "updated_at": state.get(
                "updated_at"
            ),
        }

    def _from_database(
        self,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "run_id": str(
                row.get("run_id", "")
            ),
            "status": str(
                row.get(
                    "status",
                    "idle",
                )
            ),
            "stage": str(
                row.get(
                    "stage",
                    "idle",
                )
            ),
            "message": str(
                row.get("message", "")
            ),
            "settings": row.get(
                "settings",
                {},
            ),
            "jobs_collected": int(
                row.get(
                    "jobs_collected",
                    0,
                )
            ),
            "best_jobs": int(
                row.get(
                    "best_jobs",
                    0,
                )
            ),
            "current_job_number": int(
                row.get(
                    "current_job_number",
                    0,
                )
            ),
            "current_job_id": str(
                row.get(
                    "current_job_id",
                    "",
                )
                or ""
            ),
            "current_job_title": str(
                row.get(
                    "current_job_title",
                    "",
                )
                or ""
            ),
            "submitted_count": int(
                row.get(
                    "submitted_count",
                    0,
                )
            ),
            "failed_count": int(
                row.get(
                    "failed_count",
                    0,
                )
            ),
            "maximum_applications": int(
                row.get(
                    "maximum_applications",
                    0,
                )
            ),
            "stop_requested": bool(
                row.get(
                    "stop_requested",
                    False,
                )
            ),
            "started_at": str(
                row.get(
                    "created_at",
                    "",
                )
            ),
            "updated_at": str(
                row.get(
                    "updated_at",
                    "",
                )
            ),
        }


agent_run_repository = AgentRunRepository()