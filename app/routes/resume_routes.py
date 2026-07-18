from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.schemas.profile_schema import ResumeProfile
from app.schemas.resume_schema import ResumeUploadResponse
from app.services.resume_service import resume_service


router = APIRouter(
    prefix="/api/resume",
    tags=["Resume"],
)


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    resume: UploadFile = File(...),
) -> ResumeUploadResponse:
    try:
        return await resume_service.upload_resume(
            resume
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
                "Resume upload failed: "
                f"{str(error)}"
            ),
        ) from error


@router.post(
    "/analyze",
    response_model=ResumeProfile,
)
async def analyze_resume() -> ResumeProfile:
    try:
        return await resume_service.analyze_resume()

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "CrewAI resume analysis failed: "
                f"{str(error)}"
            ),
        ) from error


@router.get(
    "/profile",
    response_model=ResumeProfile,
)
async def get_resume_profile() -> ResumeProfile:
    try:
        return resume_service.get_profile()

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error