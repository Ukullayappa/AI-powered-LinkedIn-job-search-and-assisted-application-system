from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
)


# Allow the React frontend to call FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    resume_router
)

app.include_router(
    browser_router
)

app.include_router(
    job_router
)

app.include_router(
    application_router
)

app.include_router(
    agent_router
)


@app.get("/")
async def root():
    return {
        "message": (
            f"{settings.app_name} is running"
        ),
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {
        "status": "running"
    }