from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.agent_schema import AgentStartRequest
from app.utils.json_storage import storage


class AgentStateService:
    def now(self) -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    def create(
        self,
        request: AgentStartRequest,
    ) -> dict:
        current_time = self.now()

        state = {
            "run_id": str(uuid4()),
            "status": "running",
            "stage": "starting",
            "message": "Agent is starting.",

            "jobs_collected": 0,
            "best_jobs": 0,

            "current_job_number": 0,
            "current_job_id": "",
            "current_job_title": "",

            "submitted_count": 0,
            "failed_count": 0,

            "maximum_applications": (
                request.maximum_applications
            ),

            "stop_requested": False,

            "started_at": current_time,
            "updated_at": current_time,
        }

        storage.write(
            "agent_run",
            state,
        )

        return state

    def get(self) -> dict:
        return storage.read(
            "agent_run",
            {
                "run_id": "",
                "status": "idle",
                "stage": "idle",
                "message": "Agent has not started.",

                "jobs_collected": 0,
                "best_jobs": 0,

                "current_job_number": 0,
                "current_job_id": "",
                "current_job_title": "",

                "submitted_count": 0,
                "failed_count": 0,

                "maximum_applications": 0,
                "stop_requested": False,

                "started_at": "",
                "updated_at": "",
            },
        )

    def update(
        self,
        **changes,
    ) -> dict:
        state = self.get()

        state.update(
            changes
        )

        state["updated_at"] = self.now()

        storage.write(
            "agent_run",
            state,
        )

        return state

    def request_stop(self) -> dict:
        return self.update(
            stop_requested=True,
            message=(
                "Stop requested. The agent will stop "
                "before opening the next job."
            ),
        )


agent_state_service = AgentStateService()
