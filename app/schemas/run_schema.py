from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobFilters(StrictModel):
    keywords: list[str] = Field(default_factory=list)

    location: str = "India"

    date_posted_days: int = Field(
        default=3,
        ge=1,
        le=30,
    )

    easy_apply_only: bool = True

    experience_levels: list[str] = Field(
        default_factory=lambda: [
            "Internship",
            "Entry level",
        ]
    )

    excluded_keywords: list[str] = Field(
        default_factory=list
    )


class ApplicationPreferences(StrictModel):
    phone: str = ""
    city: str = ""

    years_of_experience: str = "0"
    notice_period: str = "Immediate"

    current_salary: str = ""
    expected_salary: str = ""

    work_authorized: bool | None = None
    requires_sponsorship: bool | None = None

    willing_to_relocate: bool | None = None
    willing_to_work_onsite: bool | None = None

    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""


class CollectedJob(StrictModel):
    job_id: str
    title: str
    company: str = ""
    location: str = ""
    url: str
    description: str = ""
    easy_apply: bool = False
    posted_text: str = ""


class RankedJob(CollectedJob):
    match_score: int = Field(ge=0, le=100)

    eligible: bool

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    rejection_reasons: list[str] = Field(
        default_factory=list
    )

    explanation: str = ""


class RankedJobList(StrictModel):
    jobs: list[RankedJob] = Field(default_factory=list)