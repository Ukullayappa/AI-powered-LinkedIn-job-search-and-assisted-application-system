from fastapi import (
    APIRouter,
    HTTPException,
)

from app.browser.linkedin_search import (
    linkedin_search_service,
)
from app.schemas.job_schema import (
    JobItem,
    JobSearchRequest,
    RankJobsRequest,
    RankedJob,
)
from app.services.job_ranking_service import (
    job_ranking_service,
)
from app.utils.json_storage import storage


router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
)


@router.post(
    "/search",
    response_model=list[JobItem],
)
async def search_jobs(
    request: JobSearchRequest,
):
    try:
        return await (
            linkedin_search_service
            .search_jobs(request)
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
                "LinkedIn job search failed: "
                f"{error}"
            ),
        ) from error


@router.post(
    "/rank",
    response_model=list[RankedJob],
)
async def rank_jobs(
    request: RankJobsRequest,
):
    try:
        return await (
            job_ranking_service
            .rank_jobs(request)
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
                "Job ranking failed: "
                f"{error}"
            ),
        ) from error


@router.get(
    "/saved",
    response_model=list[JobItem],
)
async def get_saved_jobs():
    return storage.read(
        "jobs",
        [],
    )


@router.get(
    "/ranked",
    response_model=list[RankedJob],
)
async def get_ranked_jobs():
    return storage.read(
        "ranked_jobs",
        [],
    )


@router.get(
    "/best",
    response_model=list[RankedJob],
)
async def get_best_jobs():
    return storage.read(
        "best_jobs",
        [],
    )