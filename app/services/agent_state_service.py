from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.agent_run_repository import (
    agent_run_repository,
)
from app.schemas.agent_schema import AgentStartRequest


class AgentStateService:
    ACTIVE_STATUSES = {
        "queued",
        "running",
        "paused",
    }

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

    def ensure_no_active_run(
        self,
    ) -> None:
        latest_state = (
            agent_run_repository
            .get_latest()
        )

        if not latest_state:
            return

        if (
            latest_state.get("status")
            in self.ACTIVE_STATUSES
            and not latest_state.get(
                "stop_requested",
                False,
            )
        ):
            raise ValueError(
                "An agent run is already queued "
                "or active."
            )

    def build_state(
        self,
        request: AgentStartRequest,
        status: str,
        stage: str,
        message: str,
    ) -> dict:
        current_time = self.now()

        return {
            "run_id": str(uuid4()),
            "status": status,
            "stage": stage,
            "message": message,
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

    def create(
        self,
        request: AgentStartRequest,
    ) -> dict:
        self.ensure_no_active_run()

        state = self.build_state(
            request=request,
            status="running",
            stage="starting",
            message="Agent is starting.",
        )

        saved_state = (
            agent_run_repository
            .create(state)
        )

        self.current_run_id = (
            saved_state["run_id"]
        )

        return saved_state

    def create_queued(
        self,
        request: AgentStartRequest,
    ) -> dict:
        self.ensure_no_active_run()

        state = self.build_state(
            request=request,
            status="queued",
            stage="waiting_for_worker",
            message=(
                "Request queued. Start the Windows "
                "worker to run LinkedIn automation."
            ),
        )

        saved_state = (
            agent_run_repository
            .create(state)
        )

        self.current_run_id = (
            saved_state["run_id"]
        )

        return saved_state

    def claim_next_queued(
        self,
    ) -> dict | None:
        """
        Called only by the Windows worker.
        """
        state = (
            agent_run_repository
            .get_next_queued()
        )

        if not state:
            return None

        self.current_run_id = state["run_id"]

        state.update({
            "status": "running",
            "stage": "starting",
            "message": (
                "Windows worker claimed the run "
                "and is starting automation."
            ),
            "updated_at": self.now(),
        })

        return agent_run_repository.update(
            run_id=self.current_run_id,
            state=state,
        )

    def get(
        self,
    ) -> dict:
        state = None

        if self.current_run_id:
            state = (
                agent_run_repository
                .get_by_run_id(
                    self.current_run_id
                )
            )

        if not state:
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
            or state.get("run_id", "")
        )

        if not run_id:
            raise RuntimeError(
                "No agent run exists to update."
            )

        state.update(changes)
        state["updated_at"] = self.now()

        return agent_run_repository.update(
            run_id=run_id,
            state=state,
        )

    def request_stop(
        self,
    ) -> dict:
        latest_state = (
            agent_run_repository
            .get_latest()
        )

        if not latest_state:
            return self.idle_state()

        self.current_run_id = (
            latest_state["run_id"]
        )

        if latest_state.get(
            "status"
        ) == "queued":
            return self.update(
                status="stopped",
                stage="stopped",
                stop_requested=True,
                message=(
                    "Queued agent run was cancelled."
                ),
            )

        return self.update(
            stop_requested=True,
            message=(
                "Stop requested. The agent will stop "
                "before opening the next job."
            ),
        )


agent_state_service = AgentStateService()