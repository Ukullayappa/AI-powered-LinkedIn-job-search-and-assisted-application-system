from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas.agent_schema import (
    AgentStartRequest,
    AgentStartResponse,
    AgentStatusResponse,
)
from app.services.agent_orchestrator import (
    agent_orchestrator,
)
from app.services.agent_state_service import (
    agent_state_service,
)


router = APIRouter(
    prefix="/api/agent",
    tags=["Autonomous Agent"],
)


@router.post(
    "/start",
    response_model=AgentStartResponse,
)
async def start_agent(
    request: AgentStartRequest,
):
    try:
        state = await agent_orchestrator.start(
            request
        )

        return AgentStartResponse(
            run_id=state["run_id"],
            status=state["status"],
            message=(
                "Agent started successfully."
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not start agent: {error}"
            ),
        ) from error


@router.get(
    "/status",
    response_model=AgentStatusResponse,
)
async def get_agent_status():
    return AgentStatusResponse(
        **agent_state_service.get()
    )


@router.post(
    "/stop",
    response_model=AgentStatusResponse,
)
async def stop_agent():
    state = agent_orchestrator.stop()

    return AgentStatusResponse(
        **state
    )
