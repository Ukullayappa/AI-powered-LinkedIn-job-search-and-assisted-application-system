import re
from pathlib import Path
from urllib.parse import urlencode, urljoin

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    Playwright,
    async_playwright,
)

from app.browser import selectors
from app.core.config import get_settings
from app.schemas.job_schema import (
    ApplicationPreferences,
    CollectedJob,
    JobFilters,
    RankedJob,
)


class LinkedInAutomation:
    def __init__(self) -> None:
        self.settings = get_settings()

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.settings.linkedin_headless,
            slow_mo=150,
        )

        context_options = {
            "viewport": {
                "width": 1440,
                "height": 900,
            }
        }

        if self.settings.linkedin_auth_state.exists():
            context_options["storage_state"] = str(
                self.settings.linkedin_auth_state
            )

        self.context = await self.browser.new_context(
            **context_options
        )

        self.page = await self.context.new_page()

        await self.login()

        return self

    async def __aexit__(
        self,
        exception_type,
        exception,
        traceback,
    ) -> None:
        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

    def require_page(self) -> Page:
        if self.page is None:
            raise RuntimeError(
                "Browser page is not available."
            )

        return self.page

    async def login(self) -> None:
        page = self.require_page()

        await page.goto(
            "https://www.linkedin.com/feed/",
            wait_until="domcontentloaded",
        )

        if (
            "/login" not in page.url.lower()
            and await page.locator("nav").count() > 0
        ):
            return

        await page.goto(
            "https://www.linkedin.com/login",
            wait_until="domcontentloaded",
        )

        await page.locator("#username").fill(
            self.settings.linkedin_email
        )

        await page.locator("#password").fill(
            self.settings.linkedin_password.get_secret_value()
        )

        await page.get_by_role(
            "button",
            name=re.compile("sign in", re.I),
        ).click()

        await page.wait_for_load_state(
            "domcontentloaded"
        )

        security_url_words = [
            "checkpoint",
            "challenge",
            "captcha",
        ]

        if any(
            word in page.url.lower()
            for word in security_url_words
        ):
            raise RuntimeError(
                "LinkedIn security verification detected. "
                "Complete it manually."
            )

        if "/login" in page.url.lower():
            raise RuntimeError(
                "LinkedIn login failed."
            )

        if self.context is None:
            raise RuntimeError(
                "Browser context is unavailable."
            )

        await self.context.storage_state(
            path=str(
                self.settings.linkedin_auth_state
            )
        )

    def create_search_url(
        self,
        keyword: str,
        filters: JobFilters,
    ) -> str:
        seconds = (
            filters.date_posted_days
            * 24
            * 60
            * 60
        )

        parameters = {
            "keywords": keyword,
            "location": filters.location,
            "f_TPR": f"r{seconds}",
        }

        if filters.easy_apply_only:
            parameters["f_AL"] = "true"

        experience_codes = {
            "Internship": "1",
            "Entry level": "2",
            "Associate": "3",
        }

        selected_experience_codes = [
            experience_codes[level]
            for level in filters.experience_levels
            if level in experience_codes
        ]

        if selected_experience_codes:
            parameters["f_E"] = ",".join(
                selected_experience_codes
            )

        return (
            "https://www.linkedin.com/jobs/search/?"
            + urlencode(parameters)
        )

    async def find_first_locator(
        self,
        root: Page | Locator,
        selector_list: list[str],
    ) -> Locator:
        for selector in selector_list:
            locator = root.locator(selector)

            if await locator.count() > 0:
                return locator

        return root.locator(
            "__missing_selector__"
        )

    async def get_optional_text(
        self,
        root: Page | Locator,
        selector_list: list[str],
    ) -> str:
        locator = await self.find_first_locator(
            root,
            selector_list,
        )

        if await locator.count() == 0:
            return ""

        try:
            text = await locator.first.inner_text()

            return re.sub(
                r"\s+",
                " ",
                text,
            ).strip()

        except Exception:
            return ""

    def get_job_id(self, url: str) -> str:
        match = re.search(
            r"/jobs/view/(?:[^/]*-)?(\d+)",
            url,
        )

        if match:
            return match.group(1)

        return str(abs(hash(url)))

    async def collect_jobs(
        self,
        filters: JobFilters,
        fallback_keywords: list[str],
    ) -> list[CollectedJob]:
        page = self.require_page()

        keywords = (
            filters.keywords
            or fallback_keywords
            or ["Associate Software Engineer"]
        )

        collected_jobs: dict[
            str,
            CollectedJob,
        ] = {}

        for keyword in keywords:
            if (
                len(collected_jobs)
                >= self.settings.max_jobs_to_collect
            ):
                break

            search_url = self.create_search_url(
                keyword,
                filters,
            )

            await page.goto(
                search_url,
                wait_until="domcontentloaded",
            )

            await page.wait_for_timeout(1500)

            for _ in range(4):
                await page.mouse.wheel(
                    0,
                    1400,
                )

                await page.wait_for_timeout(500)

            cards = await self.find_first_locator(
                page,
                selectors.JOB_CARD_SELECTORS,
            )

            card_count = await cards.count()

            for index in range(card_count):
                if (
                    len(collected_jobs)
                    >= self.settings.max_jobs_to_collect
                ):
                    break

                card = cards.nth(index)

                try:
                    title_link = (
                        await self.find_first_locator(
                            card,
                            selectors.JOB_TITLE_SELECTORS,
                        )
                    )

                    href = await title_link.first.get_attribute(
                        "href"
                    )

                    title = (
                        await title_link.first.inner_text()
                    ).strip()

                    if not href or not title:
                        continue

                    job_url = urljoin(
                        "https://www.linkedin.com",
                        href.split("?")[0],
                    )

                    job_id = self.get_job_id(
                        job_url
                    )

                    if job_id in collected_jobs:
                        continue

                    company = await self.get_optional_text(
                        card,
                        selectors.COMPANY_SELECTORS,
                    )

                    location = await self.get_optional_text(
                        card,
                        selectors.LOCATION_SELECTORS,
                    )

                    await title_link.first.click()

                    await page.wait_for_timeout(800)

                    description = await self.get_optional_text(
                        page,
                        selectors.JOB_DESCRIPTION_SELECTORS,
                    )

                    easy_apply_locator = (
                        await self.find_first_locator(
                            page,
                            selectors.EASY_APPLY_BUTTON_SELECTORS,
                        )
                    )

                    easy_apply = (
                        await easy_apply_locator.count()
                        > 0
                    )

                    full_job_text = (
                        f"{title} {description}"
                    ).lower()

                    excluded = any(
                        keyword.lower() in full_job_text
                        for keyword
                        in filters.excluded_keywords
                    )

                    if excluded:
                        continue

                    collected_jobs[job_id] = CollectedJob(
                        job_id=job_id,
                        title=title,
                        company=company,
                        location=location,
                        url=job_url,
                        description=description[:15000],
                        easy_apply=easy_apply,
                    )

                except Exception:
                    continue

        return list(
            collected_jobs.values()
        )

    async def apply_to_job(
        self,
        job: RankedJob,
        resume_path: Path,
        preferences: ApplicationPreferences,
        auto_submit: bool,
    ) -> dict:
        page = self.require_page()

        await page.goto(
            job.url,
            wait_until="domcontentloaded",
        )

        await page.wait_for_timeout(1000)

        easy_apply_button = (
            await self.find_first_locator(
                page,
                selectors.EASY_APPLY_BUTTON_SELECTORS,
            )
        )

        if await easy_apply_button.count() == 0:
            return {
                "status": "skipped",
                "message": "Easy Apply was not found.",
                "unknown_questions": [],
            }

        await easy_apply_button.first.click()

        await page.wait_for_timeout(700)

        unknown_questions: list[str] = []

        for _ in range(12):
            modal = await self.find_first_locator(
                page,
                selectors.APPLICATION_MODAL_SELECTORS,
            )

            if await modal.count() == 0:
                return {
                    "status": "failed",
                    "message": "Application modal disappeared.",
                    "unknown_questions": [],
                }

            file_inputs = modal.locator(
                "input[type='file']"
            )

            for index in range(
                await file_inputs.count()
            ):
                try:
                    await file_inputs.nth(
                        index
                    ).set_input_files(
                        str(resume_path)
                    )
                except Exception:
                    pass

            text_inputs = modal.locator(
                "input:not([type='hidden'])"
                ":not([type='file'])"
                ":not([type='radio'])"
                ":not([type='checkbox']), textarea"
            )

            for index in range(
                await text_inputs.count()
            ):
                field = text_inputs.nth(index)

                try:
                    if not await field.is_editable():
                        continue

                    current_value = (
                        await field.input_value()
                    ).strip()

                    if current_value:
                        continue

                    label = (
                        await field.get_attribute(
                            "aria-label"
                        )
                        or await field.get_attribute(
                            "placeholder"
                        )
                        or ""
                    )

                    answer = self.answer_question(
                        label,
                        preferences,
                    )

                    required = (
                        await field.get_attribute(
                            "required"
                        )
                        is not None
                    )

                    if answer is not None:
                        await field.fill(answer)

                    elif required:
                        unknown_questions.append(
                            label
                            or f"Required field {index + 1}"
                        )

                except Exception:
                    continue

            submit_button = page.get_by_role(
                "button",
                name=re.compile(
                    r"^(submit application|submit)$",
                    re.I,
                ),
            )

            if await submit_button.count() > 0:
                if unknown_questions:
                    return {
                        "status": "waiting_for_user",
                        "message": (
                            "Unknown required questions remain."
                        ),
                        "unknown_questions": list(
                            set(unknown_questions)
                        ),
                    }

                if not auto_submit:
                    return {
                        "status": "ready_for_review",
                        "message": (
                            "Application filled. "
                            "Stopped before final submission."
                        ),
                        "unknown_questions": [],
                    }

                await submit_button.first.click()

                return {
                    "status": "submitted",
                    "message": (
                        "Application submit button clicked."
                    ),
                    "unknown_questions": [],
                }

            next_button = page.get_by_role(
                "button",
                name=re.compile(
                    r"^(next|continue|review)$",
                    re.I,
                ),
            )

            if await next_button.count() == 0:
                return {
                    "status": "waiting_for_user",
                    "message": (
                        "Next application action "
                        "could not be identified."
                    ),
                    "unknown_questions": list(
                        set(unknown_questions)
                    ),
                }

            await next_button.first.click()

            await page.wait_for_timeout(700)

        return {
            "status": "failed",
            "message": (
                "Application exceeded maximum steps."
            ),
            "unknown_questions": list(
                set(unknown_questions)
            ),
        }

    def answer_question(
        self,
        label: str,
        preferences: ApplicationPreferences,
    ) -> str | None:
        normalized_label = label.lower()

        text_answers = [
            (
                ["phone", "mobile"],
                preferences.phone,
            ),
            (
                ["city"],
                preferences.city,
            ),
            (
                [
                    "years of experience",
                    "years experience",
                ],
                preferences.years_of_experience,
            ),
            (
                ["notice period"],
                preferences.notice_period,
            ),
            (
                ["current salary"],
                preferences.current_salary,
            ),
            (
                ["expected salary"],
                preferences.expected_salary,
            ),
            (
                ["linkedin"],
                preferences.linkedin_url,
            ),
            (
                ["github"],
                preferences.github_url,
            ),
            (
                ["portfolio", "website"],
                preferences.portfolio_url,
            ),
        ]

        for keywords, answer in text_answers:
            if (
                answer
                and any(
                    keyword in normalized_label
                    for keyword in keywords
                )
            ):
                return answer

        boolean_answers = [
            (
                [
                    "authorized to work",
                    "work authorization",
                ],
                preferences.work_authorized,
            ),
            (
                [
                    "require sponsorship",
                    "need sponsorship",
                ],
                preferences.requires_sponsorship,
            ),
            (
                ["willing to relocate"],
                preferences.willing_to_relocate,
            ),
            (
                [
                    "work onsite",
                    "work on-site",
                ],
                preferences.willing_to_work_onsite,
            ),
        ]

        for keywords, answer in boolean_answers:
            if any(
                keyword in normalized_label
                for keyword in keywords
            ):
                if answer is None:
                    return None

                return "Yes" if answer else "No"

        return None