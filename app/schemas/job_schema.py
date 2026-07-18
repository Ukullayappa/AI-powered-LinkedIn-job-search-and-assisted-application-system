from pydantic import BaseModel, Field


class JobSearchRequest(BaseModel):
    keywords: str

    location: str = "India"

    date_posted_days: int = Field(
        default=3,
        ge=1,
        le=30,
    )

    easy_apply_only: bool = True

    max_jobs: int = Field(
        default=10,
        ge=1,
        le=20,
    )


class JobItem(BaseModel):
    job_id: str
    title: str
    company: str = ""
    location: str = ""
    url: str
    easy_apply: bool = False
    description: str = ""


class RankJobsRequest(BaseModel):
    minimum_score: int = Field(
        default=60,
        ge=0,
        le=100,
    )

    max_results: int = Field(
        default=5,
        ge=1,
        le=5,
    )

    excluded_title_words: list[str] = Field(
        default_factory=lambda: [
            "senior",
            "lead",
            "manager",
            "architect",
            "principal",
            "staff engineer",
        ]
    )


class RankedJob(JobItem):
    match_score: int = Field(
        ge=0,
        le=100,
    )

    eligible: bool

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    reason: str = ""