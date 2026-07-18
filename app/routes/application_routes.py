from fastapi import (
    APIRouter,
    HTTPException,
)

from app.browser.linkedin_apply import (
    linkedin_apply_service,
)
from app.schemas.application_schema import (
    ApplicationHistoryItem,
    ApplicationResult,
    MarkSubmittedRequest,
    NextJobResponse,
    PrepareApplicationRequest,
)
from app.services.application_tracking_service import (
    application_tracking_service,
)


router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"],
)


@router.post(
    "/prepare-one",
    response_model=ApplicationResult,
)
async def prepare_one_application(
    request: PrepareApplicationRequest,
):
    try:
        return await (
            linkedin_apply_service
            .prepare_application(request)
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
                "Application preparation failed: "
                f"{error}"
            ),
        ) from error


@router.post(
    "/mark-submitted",
    response_model=ApplicationHistoryItem,
)
async def mark_application_submitted(
    request: MarkSubmittedRequest,
):
    try:
        return (
            application_tracking_service
            .mark_submitted(
                request.job_id
            )
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
                "Could not save application status: "
                f"{error}"
            ),
        ) from error


@router.get(
    "/history",
    response_model=list[ApplicationHistoryItem],
)
async def get_application_history():
    return (
        application_tracking_service
        .get_history()
    )


@router.get(
    "/next-job",
    response_model=NextJobResponse | None,
)
async def get_next_application_job():
    try:
        return (
            application_tracking_service
            .get_next_job()
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error