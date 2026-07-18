from fastapi import APIRouter, HTTPException

from app.browser.linkedin_login import (
    linkedin_login_service,
)
from app.core.config import get_settings
from app.schemas.browser_schema import (
    LinkedInLoginRequest,
    LinkedInLoginResponse,
)


router = APIRouter(
    prefix="/api/linkedin",
    tags=["LinkedIn"],
)

settings = get_settings()


@router.post(
    "/login",
    response_model=LinkedInLoginResponse,
)
async def login_to_linkedin(
    request: LinkedInLoginRequest,
):
    """
    LinkedIn login is allowed only when FastAPI
    is running on the user's Windows computer.

    Credentials are never accepted by the cloud
    Render deployment.
    """
    if settings.cloud_mode:
        raise HTTPException(
            status_code=409,
            detail=(
                "LinkedIn login must run on the "
                "Windows local worker. Credentials "
                "are not accepted by the cloud server."
            ),
        )

    try:
        return await linkedin_login_service.login(
            email=request.email,
            password=(
                request.password.get_secret_value()
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
                "LinkedIn login failed: "
                f"{error}"
            ),
        ) from error