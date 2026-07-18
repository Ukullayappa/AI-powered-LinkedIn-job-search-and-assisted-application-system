from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routes.agent_routes import (
    router as agent_router,
)
from app.routes.application_routes import (
    router as application_router,
)
from app.routes.browser_routes import (
    router as browser_router,
)
from app.routes.job_routes import (
    router as job_router,
)
from app.routes.resume_routes import (
    router as resume_router,
)


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=(
        None
        if settings.public_demo_mode
        else "/docs"
    ),
    redoc_url=(
        None
        if settings.public_demo_mode
        else "/redoc"
    ),
    openapi_url=(
        None
        if settings.public_demo_mode
        else "/openapi.json"
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def public_demo_guard(
    request: Request,
    call_next,
):
    """
    Protect personal information and automation
    endpoints when the deployed application is
    running as a public portfolio demo.
    """
    protected_api_request = (
        request.url.path.startswith("/api/")
        and request.url.path != "/api/health"
    )

    if (
        settings.public_demo_mode
        and protected_api_request
    ):
        return JSONResponse(
            status_code=403,
            content={
                "detail": (
                    "This deployment is running in "
                    "public demo mode. Personal data "
                    "and automation endpoints are "
                    "disabled."
                )
            },
        )

    return await call_next(request)


app.include_router(resume_router)
app.include_router(browser_router)
app.include_router(job_router)
app.include_router(application_router)
app.include_router(agent_router)


@app.get("/")
async def root():
    return {
        "message": (
            f"{settings.app_name} is running"
        ),
        "mode": (
            "public_demo"
            if settings.public_demo_mode
            else "private"
        ),
        "docs": (
            ""
            if settings.public_demo_mode
            else "/docs"
        ),
    }


@app.get("/api/health")
async def health():
    return {
        "status": "running",
        "public_demo_mode": (
            settings.public_demo_mode
        ),
    }