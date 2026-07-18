import asyncio
from pathlib import Path

from app.browser.linkedin_automation import (
    LinkedInAutomation,
)
from app.core.config import get_settings
from app.crews.matching_crew import MatchingCrew
from app.schemas.run_schema import (
    ApplicationRecord,
    RunStatus,
    StartRunRequest,
)
from app.services.resume_service import resume_service
from app.services.run_service import run_service
from app.utils.json_storage import storage


class JobApplicationFlow:
    async def run(
        self,
        run_id: str,
        request: StartRunRequest,
    ) -> None:
        settings = get_settings()

        try:
            run_service.update_run(
                run_id,
                status=RunStatus.RUNNING,
                stage="loading_profile",
                message="Loading resume profile.",
            )

            profile = resume_service.get_profile()

            resume_path = Path(
                profile.raw_resume_path
            )

            if not resume_path.exists():
                raise FileNotFoundError(
                    "Stored resume file was not found."
                )

            auto_submit = (
                settings.auto_submit
                if request.auto_submit is None
                else request.auto_submit
            )

            minimum_score = (
                settings.minimum_match_score
                if request.minimum_match_score is None
                else request.minimum_match_score
            )

            maximum_applications = min(
                request.maximum_applications,
                settings.max_applications_per_run,
                5,
            )

            async with LinkedInAutomation() as browser:
                run_service.update_run(
                    run_id,
                    stage="collecting_jobs",
                    message="Collecting LinkedIn jobs.",
                )

                collected_jobs = await browser.collect_jobs(
                    filters=request.filters,
                    fallback_keywords=(
                        profile.preferred_job_titles
                    ),
                )

                storage.write(
                    "jobs",
                    [
                        job.model_dump()
                        for job in collected_jobs
                    ],
                )

                run_service.update_run(
                    run_id,
                    collected_jobs=len(
                        collected_jobs
                    ),
                    stage="ranking_jobs",
                    message="Ranking jobs with CrewAI.",
                )

                ranked_result = await asyncio.to_thread(
                    MatchingCrew().run,
                    profile,
                    collected_jobs,
                    request.filters,
                )

                ranked_jobs = ranked_result.jobs

                storage.write(
                    "ranked_jobs",
                    [
                        job.model_dump()
                        for job in ranked_jobs
                    ],
                )

                previous_applications = storage.read(
                    "applications",
                    [],
                )

                previous_job_ids = {
                    application.get("job_id")
                    for application
                    in previous_applications
                    if application.get("status")
                    in {
                        "submitted",
                        "ready_for_review",
                    }
                }

                selected_jobs = [
                    job
                    for job in ranked_jobs
                    if (
                        job.eligible
                        and job.easy_apply
                        and job.match_score
                        >= minimum_score
                        and job.job_id
                        not in previous_job_ids
                    )
                ][:maximum_applications]

                run_service.update_run(
                    run_id,
                    ranked_jobs=len(ranked_jobs),
                    selected_job_ids=[
                        job.job_id
                        for job in selected_jobs
                    ],
                    stage="applying",
                    message=(
                        f"Processing "
                        f"{len(selected_jobs)} jobs."
                    ),
                )

                submitted = 0
                review = 0
                failed = 0

                for index, job in enumerate(
                    selected_jobs,
                    start=1,
                ):
                    result = await browser.apply_to_job(
                        job=job,
                        resume_path=resume_path,
                        preferences=request.preferences,
                        auto_submit=auto_submit,
                    )

                    application_record = (
                        ApplicationRecord(
                            run_id=run_id,
                            job_id=job.job_id,
                            title=job.title,
                            company=job.company,
                            url=job.url,
                            match_score=job.match_score,
                            status=result["status"],
                            message=result["message"],
                            unknown_questions=result[
                                "unknown_questions"
                            ],
                        )
                    )

                    storage.append(
                        "applications",
                        application_record.model_dump(),
                    )

                    if result["status"] == "submitted":
                        submitted += 1

                    elif result["status"] in {
                        "ready_for_review",
                        "waiting_for_user",
                    }:
                        review += 1

                    else:
                        failed += 1

                    run_service.update_run(
                        run_id,
                        attempted_applications=index,
                        submitted_applications=submitted,
                        ready_for_review=review,
                        failed_applications=failed,
                    )

                run_service.update_run(
                    run_id,
                    status=RunStatus.COMPLETED,
                    stage="completed",
                    message=(
                        f"Completed. Submitted: {submitted}, "
                        f"review: {review}, failed: {failed}."
                    ),
                )

        except Exception as error:
            run_service.fail_run(
                run_id,
                str(error),
            )


job_application_flow = JobApplicationFlow()