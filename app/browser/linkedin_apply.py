import asyncio
import re
from playwright.async_api import Locator, Page, async_playwright

from app.browser.linkedin_login import (
    linkedin_login_service,
)
from app.core.config import get_settings
from app.schemas.application_schema import (
    ApplicationResult,
    PrepareApplicationRequest,
)
from app.services.resume_service import (
    resume_service,
)
from app.utils.json_storage import storage


class LinkedInApplyService:
    def __init__(self):
        self.settings = get_settings()

    async def save_screenshot(
        self,
        page: Page,
        job_id: str,
    ) -> str:
        """
        Screenshots are intentionally not stored
        on the local computer.
        """

        return ""

    async def prepare_application(
        self,
        request: PrepareApplicationRequest,
    ) -> ApplicationResult:
        profile = (
            resume_service
            .get_profile()
            .model_dump()
        )

        if not profile:
            raise ValueError(
                "Resume profile not found. "
                "Analyze resume first."
            )

        best_jobs = storage.read(
            "best_jobs",
            [],
        )

        selected_job = next(
            (
                job
                for job in best_jobs
                if str(job.get("job_id"))
                == str(request.job_id)
            ),
            None,
        )

        if not selected_job:
            raise ValueError(
                "Job ID not found in best_jobs.json"
            )

        resume_file = await asyncio.to_thread(
            resume_service.get_resume_upload_payload
        )

        session_state = (
            linkedin_login_service
            .get_session_state()
        )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                slow_mo=300,
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
                    f"Opening job: "
                    f"{selected_job['title']}"
                )

                await page.goto(
                    selected_job["url"],
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                apply_button = (
                    await self.find_easy_apply_button(
                        page
                    )
                )

                if not apply_button:
                    screenshot = (
                        await self.save_screenshot(
                            page,
                            request.job_id,
                        )
                    )

                    return ApplicationResult(
                        job_id=request.job_id,
                        title=selected_job["title"],
                        company=selected_job.get(
                            "company",
                            "",
                        ),
                        status="easy_apply_not_found",
                        message=(
                            "Easy Apply button not found."
                        ),
                        screenshot=screenshot,
                    )

                await apply_button.click(
                    timeout=20000
                )

                await asyncio.sleep(3)

                await self.click_continue_applying(
                    page
                )

                for step in range(1, 11):
                    print(
                        f"Application step: {step}"
                    )

                    area = (
                        await self.get_application_area(
                            page
                        )
                    )

                    await self.fill_contact_details(
                        area,
                        profile,
                    )

                    await self.upload_resume(
                        area,
                        resume_file,
                    )

                    await self.scroll_modal_to_bottom(
                        area
                    )

                    submit_button = (
                        await self.find_button(
                            page,
                            area,
                            r"submit\s*application|submit",
                        )
                    )

                    if submit_button:
                        return await self.final_review(
                            page,
                            request,
                            selected_job,
                        )

                    unanswered_fields = (
                        await self.get_unanswered_required_fields(
                            area
                        )
                    )

                    if unanswered_fields:
                        self.print_required_questions(
                            unanswered_fields
                        )

                        result = (
                            await self.wait_for_manual_input(
                                page,
                                request.review_seconds,
                            )
                        )

                        if result == "submit":
                            return await self.final_review(
                                page,
                                request,
                                selected_job,
                            )

                        if result == "continue":
                            continue

                        screenshot = (
                            await self.save_screenshot(
                                page,
                                request.job_id,
                            )
                        )

                        return ApplicationResult(
                            job_id=request.job_id,
                            title=selected_job["title"],
                            company=selected_job.get(
                                "company",
                                "",
                            ),
                            status="needs_user_input",
                            message=(
                                "Required questions were not "
                                "answered before time ended."
                            ),
                            screenshot=screenshot,
                        )

                    next_button = (
                        await self.find_button(
                            page,
                            area,
                            r"^\s*(next|continue|next step|continue to next step|review|review application|review your application|save and continue)\s*$",
                        )
                    )

                    if next_button:
                        print(
                            "Clicking Next/Continue..."
                        )

                        await next_button.click(
                            timeout=20000
                        )

                        await asyncio.sleep(2)

                        new_area = (
                            await self.get_application_area(
                                page
                            )
                        )

                        has_errors = (
                            await self.has_validation_errors(
                                new_area
                            )
                        )

                        unanswered_after_click = (
                            await self.get_unanswered_required_fields(
                                new_area
                            )
                        )

                        if (
                            has_errors
                            or unanswered_after_click
                        ):
                            if unanswered_after_click:
                                self.print_required_questions(
                                    unanswered_after_click
                                )
                            else:
                                print()
                                print(
                                    "LinkedIn requires a manual "
                                    "answer before continuing."
                                )
                                print()

                            result = (
                                await self.wait_for_manual_input(
                                    page,
                                    request.review_seconds,
                                )
                            )

                            if result == "submit":
                                return await self.final_review(
                                    page,
                                    request,
                                    selected_job,
                                )

                            if result == "continue":
                                continue

                            screenshot = (
                                await self.save_screenshot(
                                    page,
                                    request.job_id,
                                )
                            )

                            return ApplicationResult(
                                job_id=request.job_id,
                                title=selected_job["title"],
                                company=selected_job.get(
                                    "company",
                                    "",
                                ),
                                status="needs_user_input",
                                message=(
                                    "Manual questions were not "
                                    "answered before time ended."
                                ),
                                screenshot=screenshot,
                            )

                        continue

                    await self.print_unanswered_fields(
                        area
                    )

                    result = (
                        await self.wait_for_manual_input(
                            page,
                            request.review_seconds,
                        )
                    )

                    if result == "submit":
                        return await self.final_review(
                            page,
                            request,
                            selected_job,
                        )

                    if result == "continue":
                        continue

                    screenshot = (
                        await self.save_screenshot(
                            page,
                            request.job_id,
                        )
                    )

                    return ApplicationResult(
                        job_id=request.job_id,
                        title=selected_job["title"],
                        company=selected_job.get(
                            "company",
                            "",
                        ),
                        status="needs_user_input",
                        message=(
                            "Manual fields not completed "
                            "before time ended."
                        ),
                        screenshot=screenshot,
                    )

                screenshot = await self.save_screenshot(
                    page,
                    request.job_id,
                )

                return ApplicationResult(
                    job_id=request.job_id,
                    title=selected_job["title"],
                    company=selected_job.get(
                        "company",
                        "",
                    ),
                    status="needs_user_input",
                    message=(
                        "Application has too many steps."
                    ),
                    screenshot=screenshot,
                )

            finally:
                await context.close()
                await browser.close()

    async def find_easy_apply_button(
        self,
        page: Page,
    ):
        selectors = [
            "button[aria-label*='Easy Apply' i]:visible",
            "a[aria-label*='Easy Apply' i]:visible",
            "button:has-text('Easy Apply'):visible",
            "button:has-text('Continue applying'):visible",
        ]

        for selector in selectors:
            button = page.locator(
                selector
            ).first

            try:
                if (
                    await button.count() > 0
                    and await button.is_visible()
                ):
                    print(
                        f"Apply button found with: "
                        f"{selector}"
                    )

                    return button

            except Exception:
                continue

        return None

    async def click_continue_applying(
        self,
        page: Page,
    ):
        button = page.locator(
            "button:has-text('Continue applying'), "
            "a:has-text('Continue applying')"
        ).first

        try:
            if (
                await button.count() > 0
                and await button.is_visible()
            ):
                print(
                    "Clicking Continue applying..."
                )

                await button.click(
                    timeout=15000
                )

                await asyncio.sleep(2)

        except Exception:
            pass

    async def get_application_area(
        self,
        page: Page,
    ) -> Locator:
        modal = page.locator(
            "div[role='dialog'], "
            ".jobs-easy-apply-modal, "
            ".artdeco-modal, "
            ".modal"
        ).last

        try:
            if (
                await modal.count() > 0
                and await modal.is_visible()
            ):
                return modal

        except Exception:
            pass

        form = page.locator(
            "form"
        ).last

        try:
            if await form.count() > 0:
                return form

        except Exception:
            pass

        return page.locator(
            "body"
        )

    async def scroll_modal_to_bottom(
        self,
        area: Locator,
    ):
        """
        Scroll modal content so footer buttons
        can become visible.
        """

        try:
            await area.evaluate(
                """
                () => {
                    const scrollables =
                        document.querySelectorAll(
                            'div, section, [role="dialog"]'
                        );

                    scrollables.forEach(element => {
                        if (
                            element.scrollHeight >
                            element.clientHeight + 50
                        ) {
                            element.scrollTop =
                                element.scrollHeight;
                        }
                    });
                }
                """
            )

            await asyncio.sleep(2)

        except Exception as error:
            print(
                "Scroll error:",
                str(error)[:100],
            )

    async def fill_contact_details(
        self,
        area: Locator,
        profile: dict,
    ):
        contact = profile.get(
            "contact",
            {},
        )

        full_name = contact.get(
            "full_name",
            "",
        )

        name_parts = full_name.split()

        await self.fill_field(
            area,
            "first.*name",
            name_parts[0]
            if name_parts
            else "",
        )

        await self.fill_field(
            area,
            "last.*name",
            " ".join(name_parts[1:])
            if len(name_parts) > 1
            else "",
        )

        await self.fill_field(
            area,
            "email",
            contact.get(
                "email",
                "",
            ),
        )

        phone = re.sub(
            r"\D",
            "",
            contact.get(
                "phone",
                "",
            ),
        )[-10:]

        await self.fill_field(
            area,
            "phone|mobile|tel",
            phone,
        )

        await self.fill_field(
            area,
            "city|location",
            contact.get(
                "location",
                "",
            ),
        )

    async def fill_field(
        self,
        area: Locator,
        pattern: str,
        value: str,
    ):
        if not value:
            return

        field = area.get_by_label(
            re.compile(
                pattern,
                re.I,
            )
        ).first

        try:
            if (
                await field.count() > 0
                and await field.is_visible()
                and await field.is_editable()
            ):
                current_value = (
                    await field.input_value()
                )

                if not current_value.strip():
                    await field.fill(
                        value
                    )

                    print(
                        f"Filled {pattern}"
                    )

        except Exception:
            pass

    async def upload_resume(
        self,
        area: Locator,
        resume_file: dict,
    ):
        file_input = area.locator(
            "input[type='file']"
        ).first

        try:
            if await file_input.count() > 0:
                await file_input.set_input_files(
                    files=[
                        resume_file
                    ]
                )

                print(
                    "Resume uploaded from Supabase:",
                    resume_file.get(
                        "name",
                        "resume",
                    ),
                )

                await asyncio.sleep(1.5)

        except Exception as error:
            print(
                "Resume upload skipped:",
                error,
            )

    async def find_button(
        self,
        page: Page,
        area: Locator,
        pattern: str,
    ):
        regex = re.compile(
            pattern,
            re.I,
        )

        button = area.get_by_role(
            "button",
            name=regex,
        ).last

        try:
            if (
                await button.count() > 0
                and await button.is_visible()
                and await button.is_enabled()
            ):
                return button

        except Exception:
            pass

        button = page.get_by_role(
            "button",
            name=regex,
        ).last

        try:
            if (
                await button.count() > 0
                and await button.is_visible()
                and await button.is_enabled()
            ):
                return button

        except Exception:
            pass

        button = area.locator(
            "button, a[role='button']"
        ).filter(
            has_text=regex
        ).last

        try:
            if (
                await button.count() > 0
                and await button.is_visible()
                and await button.is_enabled()
            ):
                return button

        except Exception:
            pass

        return None

    async def get_field_label(
        self,
        field: Locator,
    ) -> str:
        """
        Get a readable label for a required field.
        """

        try:
            aria_label = await field.get_attribute(
                "aria-label"
            )

            if aria_label:
                return " ".join(
                    aria_label.split()
                )

            placeholder = await field.get_attribute(
                "placeholder"
            )

            if placeholder:
                return " ".join(
                    placeholder.split()
                )

            name = await field.get_attribute(
                "name"
            )

            label_text = await field.evaluate(
                """
                element => {
                    if (element.id) {
                        const label =
                            document.querySelector(
                                `label[for="${CSS.escape(element.id)}"]`
                            );

                        if (label && label.innerText) {
                            return label.innerText;
                        }
                    }

                    const fieldset =
                        element.closest("fieldset");

                    if (fieldset) {
                        const legend =
                            fieldset.querySelector("legend");

                        if (legend && legend.innerText) {
                            return legend.innerText;
                        }
                    }

                    const parentLabel =
                        element.closest("label");

                    if (
                        parentLabel
                        && parentLabel.innerText
                    ) {
                        return parentLabel.innerText;
                    }

                    return "";
                }
                """
            )

            cleaned_label = " ".join(
                str(label_text).split()
            )

            if cleaned_label:
                return cleaned_label

            if name:
                return name

        except Exception:
            pass

        return "Required question"

    async def field_is_answered(
        self,
        field: Locator,
    ) -> bool:
        """
        Check whether a required input, select,
        radio group or checkbox has an answer.
        """

        try:
            return bool(
                await field.evaluate(
                    """
                    element => {
                        const type =
                            (element.type || "")
                            .toLowerCase();

                        if (type === "radio") {
                            const root =
                                element.closest("form")
                                || element.closest(
                                    '[role="dialog"]'
                                )
                                || document;

                            const radios =
                                Array.from(
                                    root.querySelectorAll(
                                        'input[type="radio"]'
                                    )
                                );

                            return radios.some(
                                radio =>
                                    radio.name
                                    === element.name
                                    && radio.checked
                            );
                        }

                        if (type === "checkbox") {
                            return element.checked;
                        }

                        if (
                            element.tagName
                            === "SELECT"
                        ) {
                            return Boolean(
                                String(
                                    element.value || ""
                                ).trim()
                            );
                        }

                        return Boolean(
                            String(
                                element.value || ""
                            ).trim()
                        );
                    }
                    """
                )
            )

        except Exception:
            return True

    async def get_unanswered_required_fields(
        self,
        area: Locator,
    ) -> list[str]:
        """
        Return labels for required questions
        that still have no answer.
        """

        required_fields = area.locator(
            "input[required]:visible, "
            "input[aria-required='true']:visible, "
            "textarea[required]:visible, "
            "textarea[aria-required='true']:visible, "
            "select[required]:visible, "
            "select[aria-required='true']:visible"
        )

        unanswered: list[str] = []
        seen_labels: set[str] = set()

        count = await required_fields.count()

        for index in range(count):
            field = required_fields.nth(
                index
            )

            try:
                if await self.field_is_answered(
                    field
                ):
                    continue

                label = await self.get_field_label(
                    field
                )

                normalized_label = (
                    label.strip().lower()
                )

                if (
                    normalized_label
                    in seen_labels
                ):
                    continue

                seen_labels.add(
                    normalized_label
                )

                unanswered.append(
                    label
                )

            except Exception:
                continue

        return unanswered

    async def has_validation_errors(
        self,
        area: Locator,
    ) -> bool:
        """
        Detect LinkedIn validation messages after
        Next or Review was clicked.
        """

        errors = area.locator(
            ".artdeco-inline-feedback--error:visible, "
            "[role='alert']:visible, "
            "[class*='error']:visible"
        )

        try:
            count = await errors.count()

            for index in range(
                min(count, 20)
            ):
                error = errors.nth(
                    index
                )

                text = ""

                try:
                    text = (
                        await error.inner_text()
                    ).strip()

                except Exception:
                    pass

                if text:
                    return True

            return False

        except Exception:
            return False

    def print_required_questions(
        self,
        questions: list[str],
    ):
        print()
        print(
            "Required questions need "
            "your manual answer:"
        )

        for question in questions:
            print(
                f"→ {question}"
            )

        print(
            "The agent is paused."
        )

        print(
            "Answer them in the browser. "
            "The agent will continue automatically."
        )
        print()

    async def print_unanswered_fields(
        self,
        area: Locator,
    ):
        print()
        print(
            "--- Unanswered fields "
            "(fill manually) ---"
        )

        fields = area.locator(
            "input:visible:not([type='hidden']), "
            "textarea:visible, "
            "select:visible"
        )

        count = await fields.count()

        for index in range(count):
            field = fields.nth(
                index
            )

            try:
                field_type = (
                    await field.get_attribute(
                        "type"
                    )
                )

                if field_type == "checkbox":
                    value = ""
                else:
                    value = (
                        await field.input_value()
                    )

                if not value.strip():
                    label = await self.get_field_label(
                        field
                    )

                    print(
                        f"→ {label}"
                    )

            except Exception:
                continue

        print(
            "-----------------------------------"
        )
        print()

    async def wait_for_manual_input(
        self,
        page: Page,
        review_seconds: int,
    ) -> str:
        """
        Pause until the user answers unknown
        questions.

        Returns:
        - continue: Next/Review was clicked
        - submit: final Submit button appeared
        - timeout: the waiting time ended
        """

        print(
            "Waiting for your manual answers..."
        )

        for second in range(
            review_seconds
        ):
            await asyncio.sleep(1)

            area = (
                await self.get_application_area(
                    page
                )
            )

            if second % 5 == 0:
                await self.scroll_modal_to_bottom(
                    area
                )

            submit_button = (
                await self.find_button(
                    page,
                    area,
                    r"submit\s*application|submit",
                )
            )

            if submit_button:
                print(
                    "Submit button detected."
                )

                return "submit"

            unanswered_fields = (
                await self.get_unanswered_required_fields(
                    area
                )
            )

            next_button = (
                await self.find_button(
                    page,
                    area,
                    r"^\s*(next|continue|next step|continue to next step|review|review application|review your application|save and continue)\s*$",
                )
            )

            if (
                next_button
                and not unanswered_fields
            ):
                print(
                    "Manual answers detected."
                )

                print(
                    "Clicking Next/Continue..."
                )

                try:
                    await next_button.click(
                        timeout=20000
                    )

                    await asyncio.sleep(2)

                except Exception:
                    continue

                new_area = (
                    await self.get_application_area(
                        page
                    )
                )

                if await self.has_validation_errors(
                    new_area
                ):
                    print(
                        "LinkedIn still requires "
                        "another manual answer."
                    )

                    continue

                print(
                    "Manual answers accepted. "
                    "Continuing the application."
                )

                return "continue"

            if second % 10 == 0:
                print(
                    f"Waiting for manual answers: "
                    f"{second}/{review_seconds} seconds"
                )

                if unanswered_fields:
                    for field_name in (
                        unanswered_fields
                    ):
                        print(
                            f"→ {field_name}"
                        )

        return "timeout"

    async def submission_message_is_visible(
        self,
        page: Page,
    ) -> bool:
        """
        Look for LinkedIn submission confirmations.
        """

        patterns = [
            r"application sent",
            r"your application was sent",
            r"application submitted",
            r"successfully submitted",
            r"you applied",
        ]

        for pattern in patterns:
            locator = page.get_by_text(
                re.compile(
                    pattern,
                    re.I,
                )
            ).first

            try:
                if (
                    await locator.count() > 0
                    and await locator.is_visible()
                ):
                    print(
                        "Submission confirmation found:",
                        pattern,
                    )

                    return True

            except Exception:
                continue

        alert_locator = page.locator(
            "[role='alert']:visible, "
            ".artdeco-toast-item:visible, "
            ".artdeco-toast-item__message:visible"
        )

        try:
            alert_count = (
                await alert_locator.count()
            )

            for index in range(
                min(alert_count, 10)
            ):
                text = (
                    await alert_locator
                    .nth(index)
                    .inner_text()
                ).strip()

                if re.search(
                    (
                        r"application\s+sent|"
                        r"application\s+submitted|"
                        r"successfully\s+submitted"
                    ),
                    text,
                    re.I,
                ):
                    print(
                        "Submission alert detected:",
                        text,
                    )

                    return True

        except Exception:
            pass

        return False

    async def applied_status_is_visible(
        self,
        page: Page,
    ) -> bool:
        """
        Look for the Applied state on the job page.
        """

        selectors = [
            "button[aria-label*='Applied' i]:visible",
            "button:has-text('Applied'):visible",
            "[aria-label='Applied']:visible",
            ".jobs-s-apply button:has-text('Applied'):visible",
            ".jobs-apply-button--top-card:has-text('Applied'):visible",
        ]

        for selector in selectors:
            locator = page.locator(
                selector
            ).first

            try:
                if (
                    await locator.count() > 0
                    and await locator.is_visible()
                ):
                    print(
                        "Applied status detected."
                    )

                    return True

            except Exception:
                continue

        return False

    async def application_modal_is_visible(
        self,
        page: Page,
    ) -> bool:
        modal = page.locator(
            "div[role='dialog']:visible, "
            ".jobs-easy-apply-modal:visible, "
            ".artdeco-modal:visible"
        ).last

        try:
            return (
                await modal.count() > 0
                and await modal.is_visible()
            )

        except Exception:
            return False

    async def wait_for_manual_submit(
        self,
        page: Page,
        review_seconds: int,
    ) -> bool:
        """
        Wait for the user to click Submit manually.

        The code never clicks the Submit button.
        """

        print()
        print(
            "Review the application carefully."
        )

        print(
            "Click Submit application manually."
        )

        print(
            "The agent will open the next job "
            "after detecting submission."
        )

        modal_was_visible = (
            await self.application_modal_is_visible(
                page
            )
        )

        modal_closed_checks = 0

        for second in range(
            review_seconds
        ):
            await asyncio.sleep(1)

            if page.is_closed():
                print(
                    "Application page was closed."
                )

                return False

            if await self.submission_message_is_visible(
                page
            ):
                return True

            if await self.applied_status_is_visible(
                page
            ):
                return True

            modal_is_visible = (
                await self.application_modal_is_visible(
                    page
                )
            )

            if (
                modal_was_visible
                and not modal_is_visible
            ):
                modal_closed_checks += 1

                if modal_closed_checks >= 3:
                    print(
                        "Easy Apply modal closed after "
                        "the final Submit step."
                    )

                    print(
                        "Treating the application as "
                        "successfully submitted."
                    )

                    return True

            else:
                modal_closed_checks = 0

            if second % 10 == 0:
                print(
                    "Waiting for manual Submit:",
                    f"{second}/{review_seconds} seconds",
                )

        return False

    async def final_review(
        self,
        page: Page,
        request: PrepareApplicationRequest,
        job: dict,
    ) -> ApplicationResult:
        area = await self.get_application_area(
            page
        )

        await self.scroll_modal_to_bottom(
            area
        )

        screenshot = await self.save_screenshot(
            page,
            request.job_id,
        )

        print()
        print(
            "Reached FINAL REVIEW page."
        )

        print(
            "Submit button will NOT be clicked "
            "automatically."
        )

        submitted = (
            await self.wait_for_manual_submit(
                page,
                request.review_seconds,
            )
        )

        if submitted:
            submitted_screenshot = (
                await self.save_screenshot(
                    page,
                    request.job_id,
                )
            )

            print(
                "Returning status: submitted"
            )

            return ApplicationResult(
                job_id=request.job_id,
                title=job["title"],
                company=job.get(
                    "company",
                    "",
                ),
                status="submitted",
                message=(
                    "Manual submission was detected. "
                    "The next application can begin."
                ),
                screenshot=submitted_screenshot,
            )

        print(
            "Returning status: ready_for_review"
        )

        return ApplicationResult(
            job_id=request.job_id,
            title=job["title"],
            company=job.get(
                "company",
                "",
            ),
            status="ready_for_review",
            message=(
                "Submission was not detected before "
                "the review time ended."
            ),
            screenshot=screenshot,
        )


linkedin_apply_service = LinkedInApplyService()
