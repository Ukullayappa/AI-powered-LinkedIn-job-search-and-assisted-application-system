import re
from urllib.parse import urlencode

from playwright.async_api import (
    Locator,
    async_playwright,
)

from app.browser.linkedin_login import (
    linkedin_login_service,
)
from app.core.config import get_settings
from app.schemas.job_schema import (
    JobItem,
    JobSearchRequest,
)
from app.services.application_tracking_service import (
    application_tracking_service,
)


class LinkedInSearchService:
    def __init__(self):
        self.settings = get_settings()

        # Raw collected jobs live only in memory.
        # They are cleared when the backend restarts.
        self.latest_jobs: list[dict] = []

    def get_latest_jobs(
        self,
    ) -> list[dict]:
        return [
            dict(job)
            for job in self.latest_jobs
        ]

    def create_search_url(
        self,
        request: JobSearchRequest,
    ) -> str:
        seconds = (
            request.date_posted_days
            * 24
            * 60
            * 60
        )

        filters = {
            "keywords": request.keywords,
            "location": request.location,
            "f_TPR": f"r{seconds}",
        }

        if request.easy_apply_only:
            filters["f_AL"] = "true"

        query_string = urlencode(
            filters
        )

        return (
            "https://www.linkedin.com/jobs/search/?"
            + query_string
        )

    async def get_text(
        self,
        locator: Locator,
    ) -> str:
        """
        Safely read text from a locator.
        """

        try:
            if await locator.count() == 0:
                return ""

            text = await locator.first.inner_text()

            return " ".join(
                text.split()
            )

        except Exception:
            return ""

    def get_job_id(
        self,
        url: str,
    ) -> str:
        """
        Get LinkedIn job ID from the URL.
        """

        match = re.search(
            r"/jobs/view/(?:[^/]*-)?(\d+)",
            url,
        )

        if match:
            return match.group(1)

        return str(
            abs(hash(url))
        )

    async def scroll_jobs(
        self,
        page,
    ):
        """
        Scroll the job-results section so more
        LinkedIn cards are loaded.
        """

        job_list = page.locator(
            ".jobs-search-results-list"
        ).first

        for _ in range(8):
            if await job_list.count() > 0:
                await job_list.evaluate(
                    """
                    element => {
                        element.scrollTop =
                            element.scrollHeight;
                    }
                    """
                )

            else:
                await page.mouse.wheel(
                    0,
                    1500,
                )

            await page.wait_for_timeout(
                800
            )

    async def search_jobs(
        self,
        request: JobSearchRequest,
    ) -> list[JobItem]:
        session_state = (
            linkedin_login_service
            .get_session_state()
        )

        submitted_job_ids = (
            application_tracking_service
            .get_submitted_job_ids()
        )

        print(
            "Previously submitted jobs remembered:",
            len(submitted_job_ids),
        )

        search_url = self.create_search_url(
            request
        )

        async with async_playwright() as playwright:
            # Job search stays invisible.
            browser = await playwright.chromium.launch(
                headless=True,
            )

            context = await browser.new_context(
                storage_state=session_state,
                viewport={
                    "width": 1440,
                    "height": 900,
                },
            )

            page = await context.new_page()

            try:
                print(
                    "Opening LinkedIn job search "
                    "in hidden mode..."
                )

                await page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                await page.wait_for_timeout(
                    3000
                )

                if "/login" in page.url.lower():
                    raise ValueError(
                        "LinkedIn session expired. "
                        "Login again."
                    )

                await self.scroll_jobs(
                    page
                )

                job_cards = page.locator(
                    "li.jobs-search-results__list-item"
                )

                if await job_cards.count() == 0:
                    job_cards = page.locator(
                        "[data-occludable-job-id]"
                    )

                total_cards = (
                    await job_cards.count()
                )

                print(
                    "Job cards found:",
                    total_cards,
                )

                collected_jobs: dict[
                    str,
                    JobItem,
                ] = {}

                skipped_submitted = 0

                for index in range(
                    total_cards
                ):
                    if (
                        len(collected_jobs)
                        >= request.max_jobs
                    ):
                        break

                    card = job_cards.nth(
                        index
                    )

                    try:
                        title_link = card.locator(
                            "a[href*='/jobs/view/']"
                        ).first

                        if (
                            await title_link.count()
                            == 0
                        ):
                            continue

                        title = await self.get_text(
                            title_link
                        )

                        href = (
                            await title_link
                            .get_attribute("href")
                        )

                        if not title or not href:
                            continue

                        if href.startswith(
                            "http"
                        ):
                            job_url = href
                        else:
                            job_url = (
                                "https://www.linkedin.com"
                                + href
                            )

                        job_url = job_url.split(
                            "?"
                        )[0]

                        job_id = self.get_job_id(
                            job_url
                        )

                        # Important:
                        # never collect a job that was
                        # already submitted earlier.
                        if (
                            job_id
                            in submitted_job_ids
                        ):
                            skipped_submitted += 1

                            print(
                                "Skipped submitted job:",
                                title,
                            )

                            continue

                        company = await self.get_text(
                            card.locator(
                                ".job-card-container__primary-description, "
                                ".artdeco-entity-lockup__subtitle"
                            )
                        )

                        location = await self.get_text(
                            card.locator(
                                ".job-card-container__metadata-item, "
                                ".artdeco-entity-lockup__caption"
                            )
                        )

                        card_text = await self.get_text(
                            card
                        )

                        easy_apply = (
                            "easy apply"
                            in card_text.lower()
                        )

                        job = JobItem(
                            job_id=job_id,
                            title=title,
                            company=company,
                            location=location,
                            url=job_url,
                            easy_apply=easy_apply,
                        )

                        collected_jobs[
                            job_id
                        ] = job

                        print(
                            f"Collected new job: {title}"
                        )

                    except Exception as error:
                        print(
                            "Skipped one job card:",
                            error,
                        )

                        continue

                jobs = list(
                    collected_jobs.values()
                )

                print(
                    "Submitted jobs skipped:",
                    skipped_submitted,
                )

                self.latest_jobs = [
                    job.model_dump()
                    for job in jobs
                ]

                print(
                    "New jobs collected in memory:",
                    len(jobs),
                )

                return jobs

            finally:
                await context.close()
                await browser.close()


linkedin_search_service = (
    LinkedInSearchService()
)
