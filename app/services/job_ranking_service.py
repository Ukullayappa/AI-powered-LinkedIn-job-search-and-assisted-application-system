import asyncio

from playwright.async_api import (
    Page,
    async_playwright,
)

from app.core.config import get_settings
from app.crews.job_match_crew import JobMatchCrew
from app.schemas.job_schema import (
    RankJobsRequest,
    RankedJob,
)
from app.services.application_tracking_service import (
    application_tracking_service,
)
from app.utils.json_storage import storage


class JobRankingService:
    def __init__(self):
        self.settings = get_settings()

    async def get_description(
        self,
        page: Page,
    ) -> str:
        """
        Read the job description from LinkedIn.
        """

        await page.wait_for_timeout(
            4000
        )

        await page.mouse.wheel(
            0,
            1000,
        )

        await page.wait_for_timeout(
            1500
        )

        description_selectors = [
            "#job-details",
            ".jobs-description__content",
            ".jobs-description-content__text",
            ".jobs-box__html-content",
            "article.jobs-description",
            "div[class*='jobs-description']",
        ]

        for selector in description_selectors:
            description_box = page.locator(
                selector
            ).first

            try:
                if (
                    await description_box.count()
                    == 0
                ):
                    continue

                description_text = (
                    await description_box.inner_text(
                        timeout=5000
                    )
                )

                cleaned_text = " ".join(
                    description_text.split()
                )

                if len(cleaned_text) > 100:
                    return cleaned_text

            except Exception:
                continue

        try:
            body_text = await page.locator(
                "body"
            ).inner_text()

            if (
                "About the job"
                not in body_text
            ):
                print(
                    "'About the job' text "
                    "was not found."
                )

                return ""

            description_text = body_text.split(
                "About the job",
                1,
            )[1]

            end_markers = [
                "Set alert for similar jobs",
                "About the company",
                "Company photos",
                "Meet the hiring team",
                "Similar jobs",
                "People also viewed",
                "Explore collaborative articles",
            ]

            for marker in end_markers:
                if marker in description_text:
                    description_text = (
                        description_text.split(
                            marker,
                            1,
                        )[0]
                    )

            cleaned_text = " ".join(
                description_text.split()
            )

            if len(cleaned_text) > 100:
                return cleaned_text

        except Exception as error:
            print(
                "Could not read page text:",
                error,
            )

        return ""

    async def collect_descriptions(
        self,
        jobs: list[dict],
    ) -> list[dict]:
        """
        Open every new job and read its JD
        invisibly.
        """

        auth_file = (
            self.settings.linkedin_auth_state
        )

        if not auth_file.exists():
            raise ValueError(
                "LinkedIn session was not found. "
                "Run POST /api/linkedin/login first."
            )

        async with async_playwright() as playwright:
            # JD collection stays invisible.
            browser = await playwright.chromium.launch(
                headless=True,
            )

            context = await browser.new_context(
                storage_state=str(auth_file),
                viewport={
                    "width": 1440,
                    "height": 900,
                },
            )

            page = await context.new_page()

            try:
                total_jobs = len(
                    jobs
                )

                for index, job in enumerate(
                    jobs,
                    start=1,
                ):
                    print(
                        f"Reading new job "
                        f"{index}/{total_jobs}: "
                        f"{job['title']}"
                    )

                    try:
                        await page.goto(
                            job["url"],
                            wait_until=(
                                "domcontentloaded"
                            ),
                            timeout=60000,
                        )

                        await page.wait_for_timeout(
                            2000
                        )

                        if (
                            "/login"
                            in page.url.lower()
                        ):
                            raise ValueError(
                                "LinkedIn session expired. "
                                "Run the login endpoint again."
                            )

                        description = (
                            await self.get_description(
                                page
                            )
                        )

                        job["description"] = (
                            description[:12000]
                        )

                        print(
                            "Description characters:",
                            len(description),
                        )

                        if not description:
                            screenshot_path = (
                                self.settings
                                .screenshot_directory
                                / (
                                    "description-"
                                    f"{job['job_id']}.png"
                                )
                            )

                            screenshot_path.parent.mkdir(
                                parents=True,
                                exist_ok=True,
                            )

                            await page.screenshot(
                                path=str(
                                    screenshot_path
                                ),
                                full_page=True,
                            )

                            print(
                                "Description was not found."
                            )

                            print(
                                "Screenshot saved:",
                                screenshot_path,
                            )

                    except ValueError:
                        raise

                    except Exception as error:
                        print(
                            "Could not read job:",
                            error,
                        )

                        job["description"] = ""

                storage.write(
                    "jobs",
                    jobs,
                )

                return jobs

            finally:
                await context.close()
                await browser.close()

    def make_safe_list(
        self,
        value,
    ) -> list[str]:
        """
        Convert CrewAI output into a clean list.
        """

        if not isinstance(
            value,
            list,
        ):
            return []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    async def rank_jobs(
        self,
        request: RankJobsRequest,
    ) -> list[RankedJob]:
        """
        Rank only jobs that have not already
        been submitted.
        """

        profile = storage.read(
            "profile",
            {},
        )

        if not profile:
            raise ValueError(
                "Resume profile was not found. "
                "Upload and analyze the resume first."
            )

        jobs = storage.read(
            "jobs",
            [],
        )

        if not jobs:
            raise ValueError(
                "No new jobs were found. "
                "Search LinkedIn jobs first."
            )

        submitted_job_ids = (
            application_tracking_service
            .get_submitted_job_ids()
        )

        new_jobs = [
            job
            for job in jobs
            if str(
                job.get(
                    "job_id",
                    "",
                )
            )
            not in submitted_job_ids
        ]

        skipped_count = (
            len(jobs)
            - len(new_jobs)
        )

        print(
            "Previously submitted jobs removed "
            "before JD collection:",
            skipped_count,
        )

        if not new_jobs:
            storage.write(
                "ranked_jobs",
                [],
            )

            storage.write(
                "best_jobs",
                [],
            )

            raise ValueError(
                "All collected jobs were already "
                "submitted. No new jobs to rank."
            )

        jobs_with_descriptions = (
            await self.collect_descriptions(
                new_jobs
            )
        )

        print(
            "Sending new jobs to CrewAI "
            "for ranking..."
        )

        ai_rankings = await asyncio.to_thread(
            JobMatchCrew().rank_jobs,
            profile,
            jobs_with_descriptions,
            request.excluded_title_words,
        )

        ranking_by_job_id = {
            str(
                item.get(
                    "job_id"
                )
            ): item
            for item in ai_rankings
            if isinstance(
                item,
                dict,
            )
        }

        ranked_jobs: list[
            RankedJob
        ] = []

        for job in jobs_with_descriptions:
            job_id = str(
                job["job_id"]
            )

            ai_result = (
                ranking_by_job_id.get(
                    job_id,
                    {},
                )
            )

            try:
                match_score = int(
                    ai_result.get(
                        "match_score",
                        0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                match_score = 0

            match_score = max(
                0,
                min(
                    match_score,
                    100,
                ),
            )

            title_lower = (
                job["title"].lower()
            )

            title_is_excluded = any(
                word.lower()
                in title_lower
                for word
                in request.excluded_title_words
            )

            ai_eligible = bool(
                ai_result.get(
                    "eligible",
                    False,
                )
            )

            eligible = (
                ai_eligible
                and not title_is_excluded
                and match_score
                >= request.minimum_score
            )

            reason = str(
                ai_result.get(
                    "reason",
                    "",
                )
            )

            if title_is_excluded:
                reason = (
                    "Rejected because the job title "
                    "is not suitable for a fresher."
                )

            ranked_job = RankedJob(
                job_id=job_id,

                title=job["title"],

                company=job.get(
                    "company",
                    "",
                ),

                location=job.get(
                    "location",
                    "",
                ),

                url=job["url"],

                easy_apply=job.get(
                    "easy_apply",
                    False,
                ),

                description=job.get(
                    "description",
                    "",
                ),

                match_score=match_score,

                eligible=eligible,

                matched_skills=(
                    self.make_safe_list(
                        ai_result.get(
                            "matched_skills",
                            [],
                        )
                    )
                ),

                missing_skills=(
                    self.make_safe_list(
                        ai_result.get(
                            "missing_skills",
                            [],
                        )
                    )
                ),

                reason=reason,
            )

            ranked_jobs.append(
                ranked_job
            )

        ranked_jobs.sort(
            key=lambda job: (
                job.match_score
            ),
            reverse=True,
        )

        storage.write(
            "ranked_jobs",
            [
                job.model_dump()
                for job in ranked_jobs
            ],
        )

        best_jobs = [
            job
            for job in ranked_jobs
            if job.eligible
        ][:request.max_results]

        storage.write(
            "best_jobs",
            [
                job.model_dump()
                for job in best_jobs
            ],
        )

        print(
            "Total new jobs ranked:",
            len(ranked_jobs),
        )

        print(
            "Best eligible new jobs:",
            len(best_jobs),
        )

        return best_jobs


job_ranking_service = (
    JobRankingService()
)
