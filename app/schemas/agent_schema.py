from pydantic import BaseModel, Field


class AgentStartRequest(BaseModel):
    keywords: str = ""

    location: str = "India"

    date_posted_days: int = Field(
        default=3,
        ge=1,
        le=30,
    )

    maximum_jobs_to_collect: int = Field(
        default=20,
        ge=5,
        le=20,
    )

    maximum_applications: int = Field(
        default=5,
        ge=1,
        le=5,
    )

    minimum_match_score: int = Field(
        default=60,
        ge=0,
        le=100,
    )

    review_seconds: int = Field(
        default=900,
        ge=60,
        le=1800,
    )


class AgentStartResponse(BaseModel):
    run_id: str
    status: str
    message: str


class AgentStatusResponse(BaseModel):
    run_id: str = ""
    status: str = "idle"
    stage: str = "idle"
    message: str = ""

    jobs_collected: int = 0
    best_jobs: int = 0

    current_job_number: int = 0
    current_job_id: str = ""
    current_job_title: str = ""

    submitted_count: int = 0
    failed_count: int = 0

    maximum_applications: int = 0
    stop_requested: bool = False

    started_at: str = ""
    updated_at: str = ""
