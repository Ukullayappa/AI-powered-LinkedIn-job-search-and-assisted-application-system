import json

import json_repair
from crewai import Agent, Crew, Process, Task

from app.crews.llm_factory import create_llm


class JobMatchCrew:
    def rank_jobs(
        self,
        profile: dict,
        jobs: list[dict],
        excluded_title_words: list[str],
    ) -> list[dict]:
        llm = create_llm(
            temperature=0.0
        )

        matcher_agent = Agent(
            role="Entry-Level Job Matcher",

            goal=(
                "Compare the candidate resume with jobs "
                "and find the strongest realistic matches."
            ),

            backstory=(
                "You are a careful technical recruiter. "
                "You never invent candidate skills and never "
                "guarantee that a candidate will be hired."
            ),

            llm=llm,

            verbose=True,

            allow_delegation=False,
        )

        matching_task = Task(
            description="""
Compare the candidate profile with every job.

Return only one JSON array.

Each JSON item must contain:

{
  "job_id": "original job ID",
  "match_score": 0,
  "eligible": true,
  "matched_skills": [],
  "missing_skills": [],
  "reason": ""
}

Scoring guide:

- Required technical skills: 40 points
- Related projects: 20 points
- Experience level: 15 points
- Education eligibility: 10 points
- Job-title relevance: 10 points
- Location relevance: 5 points

Rules:

- Use only information found in the candidate profile.
- Do not invent skills or experience.
- Do not guarantee hiring or interview selection.
- Score each job from 0 to 100.
- Mark senior, lead, manager, architect,
  principal and staff roles as ineligible.
- Mark jobs requiring clearly unsupported
  mandatory experience as ineligible.
- Keep the original job_id exactly.
- Return JSON only.
- Do not use markdown.
- Do not use JSON code fences.
- Sort highest score first.

Excluded title words:

{excluded_words}

Candidate profile:

{profile_json}

Jobs:

{jobs_json}
""",

            expected_output=(
                "A JSON array containing one ranking object "
                "for every supplied job."
            ),

            agent=matcher_agent,
        )

        crew = Crew(
            agents=[
                matcher_agent
            ],

            tasks=[
                matching_task
            ],

            process=Process.sequential,

            verbose=True,
        )

        result = crew.kickoff(
            inputs={
                "excluded_words": json.dumps(
                    excluded_title_words
                ),

                "profile_json": json.dumps(
                    profile,
                    ensure_ascii=False,
                    indent=2,
                ),

                "jobs_json": json.dumps(
                    jobs,
                    ensure_ascii=False,
                    indent=2,
                ),
            }
        )

        raw_result = result.raw

        if not raw_result:
            raise RuntimeError(
                "CrewAI returned an empty ranking."
            )

        parsed_result = json_repair.loads(
            raw_result
        )

        # Sometimes an LLM wraps the array inside
        # an object such as {"rankings": [...]}.
        if isinstance(parsed_result, dict):
            parsed_result = parsed_result.get(
                "rankings",
                parsed_result.get(
                    "jobs",
                    [],
                ),
            )

        if not isinstance(
            parsed_result,
            list,
        ):
            raise RuntimeError(
                "CrewAI ranking must be a JSON list."
            )

        return parsed_result