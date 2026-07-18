from fastapi import APIRouter, HTTPException

from app.browser.linkedin_login import (
    linkedin_login_service,
)
from app.schemas.browser_schema import (
    LinkedInLoginRequest,
    LinkedInLoginResponse,
)


router = APIRouter(
    prefix="/api/linkedin",
    tags=["LinkedIn"],
)


@router.post(
    "/login",
    response_model=LinkedInLoginResponse,
)
async def login_to_linkedin(
    request: LinkedInLoginRequest,
):
    """
    The password is used only for this request.
    The backend saves the LinkedIn browser
    session, not the credentials.
    """

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
