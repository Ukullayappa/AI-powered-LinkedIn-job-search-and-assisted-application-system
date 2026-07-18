import json

from crewai import Agent, Crew, Process, Task

from app.crews.llm_factory import create_llm
from app.schemas.job_schema import (
    CollectedJob,
    JobFilters,
    RankedJobList,
)
from app.schemas.profile_schema import ResumeProfile


class MatchingCrew:
    def run(
        self,
        profile: ResumeProfile,
        jobs: list[CollectedJob],
        filters: JobFilters,
    ) -> RankedJobList:
        if not jobs:
            return RankedJobList(jobs=[])

        llm = create_llm(temperature=0)

        matching_agent = Agent(
            role="Job Matching Recruiter",
            goal=(
                "Compare the resume with jobs and rank "
                "the strongest realistic matches."
            ),
            backstory=(
                "You are an evidence-based recruiter. "
                "You never guarantee selection and never "
                "pretend that missing skills are present."
            ),
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

        matching_task = Task(
            description="""
Compare the candidate profile with every supplied job.

For every job:

1. Give a match score from 0 to 100.
2. Identify matched skills.
3. Identify missing important skills.
4. Check experience eligibility.
5. Check education eligibility.
6. Check excluded keywords.
7. Check Easy Apply availability.
8. Set eligible to false when an important mandatory
   requirement is clearly missing.
9. Preserve the original job_id, title, company,
   location, URL and description.
10. Sort jobs from highest score to lowest.

Do not guarantee that the candidate will be selected.

Candidate profile:

{profile_json}

User filters:

{filters_json}

Jobs:

{jobs_json}
""",
            expected_output=(
                "A RankedJobList containing all supplied "
                "jobs sorted by match score."
            ),
            agent=matching_agent,
            output_pydantic=RankedJobList,
        )

        crew = Crew(
            agents=[matching_agent],
            tasks=[matching_task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff(
            inputs={
                "profile_json": json.dumps(
                    profile.model_dump(),
                    ensure_ascii=False,
                ),
                "filters_json": json.dumps(
                    filters.model_dump(),
                    ensure_ascii=False,
                ),
                "jobs_json": json.dumps(
                    [job.model_dump() for job in jobs],
                    ensure_ascii=False,
                ),
            }
        )

        if result.pydantic is None:
            raise RuntimeError(
                "CrewAI did not return structured rankings."
            )

        return result.pydantic