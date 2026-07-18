from pydantic import BaseModel, Field


class PrepareApplicationRequest(BaseModel):
    job_id: str

    review_seconds: int = Field(
        default=300,
        ge=30,
        le=1800,
    )


class ApplicationResult(BaseModel):
    job_id: str
    title: str
    company: str
    status: str
    message: str
    screenshot: str = ""


class MarkSubmittedRequest(BaseModel):
    job_id: str


class ApplicationHistoryItem(BaseModel):
    job_id: str
    title: str
    company: str
    url: str
    status: str
    submitted_at: str


class NextJobResponse(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    url: str
    match_score: int
    message: str
