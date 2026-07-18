from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContactInfo(StrictModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class EducationItem(StrictModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    start_date: str = ""
    end_date: str = ""
    score: str = ""


class ExperienceItem(StrictModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = Field(default_factory=list)


class ProjectItem(StrictModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class ResumeProfile(StrictModel):
    contact: ContactInfo = Field(
        default_factory=ContactInfo
    )

    professional_summary: str = ""

    skills: list[str] = Field(
        default_factory=list
    )

    education: list[EducationItem] = Field(
        default_factory=list
    )

    experience: list[ExperienceItem] = Field(
        default_factory=list
    )

    projects: list[ProjectItem] = Field(
        default_factory=list
    )

    certifications: list[str] = Field(
        default_factory=list
    )

    preferred_job_titles: list[str] = Field(
        default_factory=list
    )

    experience_level: str = "Fresher"

    raw_resume_path: str = ""
    extracted_text_path: str = ""