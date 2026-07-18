import asyncio

from app.browser.linkedin_apply import (
    linkedin_apply_service,
)
from app.browser.linkedin_login import (
    linkedin_login_service,
)
from app.browser.linkedin_search import (
    linkedin_search_service,
)
from app.schemas.agent_schema import (
    AgentStartRequest,
)
from app.schemas.application_schema import (
    PrepareApplicationRequest,
)
from app.schemas.job_schema import (
    JobSearchRequest,
    RankJobsRequest,
)
from app.services.agent_state_service import (
    agent_state_service,
)
from app.services.application_tracking_service import (
    application_tracking_service,
)
from app.services.job_ranking_service import (
    job_ranking_service,
)
from app.services.resume_service import (
    resume_service,
)
from app.utils.json_storage import storage


class AgentOrchestrator:
    def __init__(self):
        self.running_task: asyncio.Task | None = None

    async def start(
        self,
        request: AgentStartRequest,
    ) -> dict:
        if (
            self.running_task is not None
            and not self.running_task.done()
        ):
            raise ValueError(
                "The agent is already running."
            )

        state = agent_state_service.create(
            request
        )

        self.running_task = asyncio.create_task(
            self.run_workflow(
                request
            )
        )

        return state

    async def run_workflow(
        self,
        request: AgentStartRequest,
    ):
        try:
            # 1. Analyze uploaded resume.
            agent_state_service.update(
                stage="analyzing_resume",
                message=(
                    "Analyzing the uploaded resume."
                ),
            )

            analyzed_profile = (
                await resume_service.analyze_resume()
            )

            profile = analyzed_profile.model_dump()

            if not profile:
                raise RuntimeError(
                    "Resume analysis did not create "
                    "a candidate profile."
                )

            # 2. Login or reuse LinkedIn session.
            agent_state_service.update(
                stage="logging_in",
                message=(
                    "Loading the saved LinkedIn session."
                ),
            )

            login_result = (
                await linkedin_login_service.login()
            )

            if login_result.status != "logged_in":
                raise RuntimeError(
                    login_result.message
                )

            # 3. Choose search keywords.
            keywords = request.keywords.strip()

            if not keywords:
                preferred_titles = profile.get(
                    "preferred_job_titles",
                    [],
                )

                if preferred_titles:
                    keywords = " OR ".join(
                        preferred_titles[:3]
                    )
                else:
                    keywords = (
                        "Software Engineer OR "
                        "Full Stack Developer"
                    )

            # 4. Search LinkedIn jobs.
            agent_state_service.update(
                stage="searching_jobs",
                message=(
                    f"Searching LinkedIn jobs for: "
                    f"{keywords}"
                ),
            )

            search_request = JobSearchRequest(
                keywords=keywords,
                location=request.location,
                date_posted_days=(
                    request.date_posted_days
                ),
                easy_apply_only=True,
                max_jobs=(
                    request.maximum_jobs_to_collect
                ),
            )

            jobs = await (
                linkedin_search_service.search_jobs(
                    search_request
                )
            )

            agent_state_service.update(
                jobs_collected=len(jobs),
                message=(
                    f"Collected {len(jobs)} jobs."
                ),
            )

            if not jobs:
                raise RuntimeError(
                    "No matching LinkedIn jobs "
                    "were found."
                )

            # 5. Rank jobs.
            agent_state_service.update(
                stage="ranking_jobs",
                message=(
                    "Comparing jobs with the resume."
                ),
            )

            rank_request = RankJobsRequest(
                minimum_score=(
                    request.minimum_match_score
                ),
                max_results=(
                    request.maximum_applications
                ),
            )

            await job_ranking_service.rank_jobs(
                rank_request
            )

            best_jobs = storage.read(
                "best_jobs",
                [],
            )

            agent_state_service.update(
                best_jobs=len(best_jobs),
                message=(
                    f"Selected {len(best_jobs)} "
                    "best jobs."
                ),
            )

            if not best_jobs:
                raise RuntimeError(
                    "No eligible jobs reached the "
                    "minimum match score."
                )

            # 6. Skip jobs already submitted.
            history = (
                application_tracking_service
                .get_history()
            )

            submitted_job_ids = {
                str(item.job_id)
                for item in history
                if item.status == "submitted"
            }

            pending_jobs = [
                job
                for job in best_jobs
                if str(job.get("job_id"))
                not in submitted_job_ids
            ]

            submitted_count = 0
            failed_count = 0

            # 7. Apply to jobs one at a time.
            for job_number, job in enumerate(
                pending_jobs,
                start=1,
            ):
                current_state = (
                    agent_state_service.get()
                )

                if current_state.get(
                    "stop_requested"
                ):
                    agent_state_service.update(
                        status="stopped",
                        stage="stopped",
                        message=(
                            "Agent stopped by user."
                        ),
                    )

                    return

                if (
                    submitted_count
                    >= request.maximum_applications
                ):
                    break

                job_id = str(
                    job.get("job_id")
                )

                agent_state_service.update(
                    status="running",
                    stage="preparing_application",
                    current_job_number=job_number,
                    current_job_id=job_id,
                    current_job_title=job.get(
                        "title",
                        "",
                    ),
                    submitted_count=submitted_count,
                    failed_count=failed_count,
                    message=(
                        f"Preparing job {job_number}: "
                        f"{job.get('title', '')}. "
                        "Answer unknown questions and "
                        "click Submit manually."
                    ),
                )

                apply_request = (
                    PrepareApplicationRequest(
                        job_id=job_id,
                        review_seconds=(
                            request.review_seconds
                        ),
                    )
                )

                result = await (
                    linkedin_apply_service
                    .prepare_application(
                        apply_request
                    )
                )

                if result.status == "submitted":
                    agent_state_service.update(
                        stage="submission_detected",
                        message=(
                            "Manual submission detected."
                        ),
                    )

                    application_tracking_service.mark_submitted(
                        job_id
                    )

                    submitted_count += 1

                    agent_state_service.update(
                        stage="moving_to_next_job",
                        submitted_count=submitted_count,
                        message=(
                            "Application saved as submitted. "
                            "Opening the next job."
                        ),
                    )

                    await asyncio.sleep(3)

                    continue

                if result.status == "easy_apply_not_found":
                    failed_count += 1

                    agent_state_service.update(
                        failed_count=failed_count,
                        message=(
                            "Easy Apply was unavailable. "
                            "Moving to the next job."
                        ),
                    )

                    await asyncio.sleep(2)

                    continue

                agent_state_service.update(
                    status="paused",
                    stage=result.status,
                    submitted_count=submitted_count,
                    failed_count=failed_count,
                    message=result.message,
                )

                return

            # 8. Complete workflow.
            agent_state_service.update(
                status="completed",
                stage="completed",
                submitted_count=submitted_count,
                failed_count=failed_count,
                current_job_id="",
                current_job_title="",
                message=(
                    "Agent run completed. "
                    f"{submitted_count} applications "
                    "were submitted."
                ),
            )

        except Exception as error:
            agent_state_service.update(
                status="failed",
                stage="failed",
                message=str(error),
            )

            print(
                "Agent workflow failed:",
                error,
            )

    def stop(self) -> dict:
        return (
            agent_state_service
            .request_stop()
        )


agent_orchestrator = AgentOrchestrator()
