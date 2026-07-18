from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.agent_run_repository import (
    agent_run_repository,
)
from app.schemas.agent_schema import AgentStartRequest


class AgentStateService:
    def __init__(
        self,
    ) -> None:
        self.current_run_id = ""

    def now(
        self,
    ) -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    def idle_state(
        self,
    ) -> dict:
        return {
            "run_id": "",
            "status": "idle",
            "stage": "idle",
            "message": "Agent has not started.",
            "settings": {},
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
        }

    def create(
        self,
        request: AgentStartRequest,
    ) -> dict:
        current_time = self.now()
        run_id = str(uuid4())

        state = {
            "run_id": run_id,
            "status": "running",
            "stage": "starting",
            "message": "Agent is starting.",
            "settings": request.model_dump(),
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

        saved_state = (
            agent_run_repository.create(
                state
            )
        )

        self.current_run_id = run_id
        return saved_state

    def get(
        self,
    ) -> dict:
        state = (
            agent_run_repository
            .get_latest()
        )

        if not state:
            return self.idle_state()

        self.current_run_id = state.get(
            "run_id",
            "",
        )

        return state

    def update(
        self,
        **changes,
    ) -> dict:
        state = self.get()

        run_id = (
            self.current_run_id
            or state.get(
                "run_id",
                "",
            )
        )

        if not run_id:
            raise RuntimeError(
                "No agent run exists to update."
            )

        state.update(
            changes
        )

        state["updated_at"] = self.now()

        return agent_run_repository.update(
            run_id=run_id,
            state=state,
        )

    def request_stop(
        self,
    ) -> dict:
        return self.update(
            stop_requested=True,
            message=(
                "Stop requested. The agent will stop "
                "before opening the next job."
            ),
        )


agent_state_service = AgentStateService()
