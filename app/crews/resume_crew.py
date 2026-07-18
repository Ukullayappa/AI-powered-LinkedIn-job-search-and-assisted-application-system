import json

import json_repair
from crewai import Agent, Crew, Process, Task
from pydantic import ValidationError

from app.crews.llm_factory import create_llm
from app.schemas.profile_schema import ResumeProfile


class ResumeCrew:
    def run(
        self,
        resume_text: str,
    ) -> ResumeProfile:
        llm = create_llm(
            temperature=0.0
        )

        resume_analyzer = Agent(
            role="Truthful Resume Analyzer",

            goal=(
                "Extract accurate candidate information "
                "from a resume and return only JSON."
            ),

            backstory=(
                "You are a careful technical recruiter. "
                "You never invent skills, experience, dates, "
                "education, certifications, achievements, "
                "contact details, or URLs."
            ),

            llm=llm,

            verbose=True,

            allow_delegation=False,
        )

        resume_task = Task(
            description="""
Analyze the resume below and return one JSON object.

The JSON must match the supplied schema.

Rules:

- Return JSON only.
- Do not use markdown.
- Do not use ```json code fences.
- Do not add explanations before or after the JSON.
- Use only facts explicitly present in the resume.
- Never invent missing information.
- Do not increase years of experience.
- Do not treat personal projects as work experience.
- Do not add technologies that are not present.
- Use empty strings for missing text fields.
- Use empty arrays for missing list fields.
- Remove duplicate skills.
- Suitable job titles must match the actual resume.
- Preserve truthful internship information.
- The candidate may be a fresher.

Required JSON schema:

{profile_schema}

Resume:

{resume_text}
""",

            expected_output=(
                "One valid JSON object matching the supplied "
                "ResumeProfile schema, with no markdown."
            ),

            agent=resume_analyzer,

            # Do not add output_pydantic here.
            # Groq llama-3.3-70b-versatile does not
            # support CrewAI's json_schema response format.
        )

        crew = Crew(
            agents=[
                resume_analyzer
            ],

            tasks=[
                resume_task
            ],

            process=Process.sequential,

            verbose=True,
        )

        result = crew.kickoff(
            inputs={
                "resume_text": resume_text,

                "profile_schema": json.dumps(
                    ResumeProfile.model_json_schema(),
                    ensure_ascii=False,
                    indent=2,
                ),
            }
        )

        raw_output = result.raw

        if not raw_output:
            raise RuntimeError(
                "CrewAI returned an empty response."
            )

        try:
            # Handles normal JSON as well as small mistakes
            # such as markdown fences or missing commas.
            parsed_data = json_repair.loads(
                raw_output
            )

        except Exception as error:
            raise RuntimeError(
                "CrewAI returned JSON that could not "
                f"be parsed: {error}"
            ) from error

        if not isinstance(
            parsed_data,
            dict,
        ):
            raise RuntimeError(
                "CrewAI response must be one JSON object."
            )

        try:
            profile = ResumeProfile.model_validate(
                parsed_data
            )

        except ValidationError as error:
            raise RuntimeError(
                "CrewAI JSON did not match the "
                f"ResumeProfile schema: {error}"
            ) from error

        return profile