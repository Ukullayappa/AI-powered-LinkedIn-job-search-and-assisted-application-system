from datetime import datetime, timezone

from app.schemas.run_schema import (
    RunRecord,
    RunStatus,
)
from app.utils.json_storage import storage


class RunService:
    def create_run(self) -> RunRecord:
        run = RunRecord()

        storage.update_by_id(
            "runs",
            "run_id",
            run.model_dump(),
        )

        return run

    def get_run(self, run_id: str) -> RunRecord:
        runs = storage.read(
            "runs",
            [],
        )

        for run in runs:
            if run.get("run_id") == run_id:
                return RunRecord.model_validate(run)

        raise KeyError(
            f"Run {run_id} was not found."
        )

    def update_run(
        self,
        run_id: str,
        **changes,
    ) -> RunRecord:
        run = self.get_run(run_id)

        run_data = run.model_dump()
        run_data.update(changes)

        run_data["updated_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        updated_run = RunRecord.model_validate(
            run_data
        )

        storage.update_by_id(
            "runs",
            "run_id",
            updated_run.model_dump(),
        )

        return updated_run

    def fail_run(
        self,
        run_id: str,
        error_message: str,
    ) -> RunRecord:
        run = self.get_run(run_id)

        errors = [
            *run.errors,
            error_message,
        ]

        return self.update_run(
            run_id,
            status=RunStatus.FAILED,
            stage="failed",
            message=error_message,
            errors=errors,
        )


run_service = RunService()