import asyncio
import re
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from app.core.config import get_settings
from app.schemas.browser_schema import LinkedInLoginResponse


class LinkedInLoginService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def login(
        self,
        email: str | None = None,
        password: str | None = None,
    ) -> LinkedInLoginResponse:
        """
        Credentials supplied:
            Create a fresh LinkedIn session.

        No credentials supplied:
            Reuse the saved session. The agent
            orchestrator uses this mode.

        The email and password are never saved.
        """

        supplied_email = email.strip() if email else ""
        supplied_password = password if password else ""

        has_credentials = bool(
            supplied_email and supplied_password
        )

        auth_state_path = self.settings.linkedin_auth_state
        auth_state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                slow_mo=250,
            )

            try:
                if has_credentials:
                    # A new user may use another LinkedIn
                    # account, so remove the old session.
                    auth_state_path.unlink(missing_ok=True)

                    context = await browser.new_context(
                        viewport={
                            "width": 1440,
                            "height": 900,
                        }
                    )

                    return await self.login_with_credentials(
                        context=context,
                        auth_state_path=auth_state_path,
                        email=supplied_email,
                        password=supplied_password,
                    )

                if not auth_state_path.exists():
                    raise ValueError(
                        "LinkedIn session was not found. "
                        "Enter your LinkedIn email and "
                        "password in the dashboard first."
                    )

                context = await self.create_saved_context(
                    browser=browser,
                    auth_state_path=auth_state_path,
                )

                page = await context.new_page()
                self.configure_page(page)

                await page.goto(
                    "https://www.linkedin.com/feed/",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                await page.wait_for_timeout(2000)

                if await self.is_logged_in(page):
                    return LinkedInLoginResponse(
                        status="logged_in",
                        message=(
                            "Existing LinkedIn session "
                            "loaded successfully."
                        ),
                        current_url=page.url,
                        session_saved=True,
                    )

                auth_state_path.unlink(missing_ok=True)

                raise ValueError(
                    "The saved LinkedIn session expired. "
                    "Enter your LinkedIn email and "
                    "password in the dashboard again."
                )

            finally:
                await browser.close()

    async def login_with_credentials(
        self,
        context: BrowserContext,
        auth_state_path: Path,
        email: str,
        password: str,
    ) -> LinkedInLoginResponse:
        page = await context.new_page()
        self.configure_page(page)

        await self.open_login_form(page)

        email_input = page.locator(
            "#username:visible, "
            "input[name='session_key']:visible, "
            "input[autocomplete='username']:visible, "
            "input[type='email']:visible"
        ).first

        password_input = page.locator(
            "#password:visible, "
            "input[name='session_password']:visible, "
            "input[autocomplete='current-password']:visible, "
            "input[type='password']:visible"
        ).first

        try:
            await email_input.wait_for(
                state="visible",
                timeout=30000,
            )
            await password_input.wait_for(
                state="visible",
                timeout=30000,
            )
        except PlaywrightTimeoutError as error:
            screenshot_path = (
                self.settings.screenshot_directory
                / "linkedin-login-form-not-found.png"
            )
            screenshot_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            await page.screenshot(
                path=str(screenshot_path),
                full_page=True,
            )
            raise RuntimeError(
                "Visible LinkedIn login fields were "
                f"not found. Screenshot: {screenshot_path}"
            ) from error

        print("LinkedIn email field found.")
        await email_input.fill(email)

        print("LinkedIn password field found.")
        await password_input.fill(password)

        sign_in_button = page.locator(
            "button[type='submit']:visible"
        ).first

        if await sign_in_button.count() == 0:
            sign_in_button = page.get_by_role(
                "button",
                name=re.compile(
                    r"sign in",
                    re.IGNORECASE,
                ),
            ).first

        await sign_in_button.wait_for(
            state="visible",
            timeout=30000,
        )

        print("Clicking LinkedIn Sign in button.")
        await sign_in_button.click()

        login_result = await self.wait_for_result(page)

        if login_result == "verification":
            return LinkedInLoginResponse(
                status="verification_required",
                message=(
                    "Complete LinkedIn OTP, CAPTCHA "
                    "or security verification in the "
                    "visible browser."
                ),
                current_url=page.url,
                session_saved=False,
            )

        if login_result == "failed":
            return LinkedInLoginResponse(
                status="failed",
                message=(
                    "LinkedIn login failed. Check "
                    "the email and password."
                ),
                current_url=page.url,
                session_saved=False,
            )

        await context.storage_state(
            path=str(auth_state_path),
            indexed_db=True,
        )

        return LinkedInLoginResponse(
            status="logged_in",
            message=(
                "LinkedIn login successful. "
                "The browser session was saved locally."
            ),
            current_url=page.url,
            session_saved=True,
        )

    def configure_page(self, page: Page) -> None:
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(60000)

    async def open_login_form(self, page: Page) -> None:
        await page.goto(
            "https://www.linkedin.com/login",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(2500)

        visible_email = page.locator(
            "#username:visible, "
            "input[name='session_key']:visible, "
            "input[autocomplete='username']:visible, "
            "input[type='email']:visible"
        )

        if await visible_email.count() > 0:
            return

        print(
            "Direct login form was not visible. "
            "Trying LinkedIn home-page Sign in."
        )

        await page.goto(
            "https://www.linkedin.com/",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(2000)
        await self.accept_cookies_if_present(page)

        sign_in_link = page.get_by_role(
            "link",
            name=re.compile(
                r"sign in",
                re.IGNORECASE,
            ),
        ).first

        if await sign_in_link.count() > 0:
            await sign_in_link.click()
            await page.wait_for_timeout(2000)

    async def accept_cookies_if_present(
        self,
        page: Page,
    ) -> None:
        buttons = [
            page.get_by_role(
                "button",
                name=re.compile(
                    r"accept",
                    re.IGNORECASE,
                ),
            ),
            page.get_by_role(
                "button",
                name=re.compile(
                    r"allow",
                    re.IGNORECASE,
                ),
            ),
        ]

        for locator in buttons:
            try:
                if (
                    await locator.count() > 0
                    and await locator.first.is_visible()
                ):
                    await locator.first.click()
                    await page.wait_for_timeout(500)
                    return
            except Exception:
                continue

    async def create_saved_context(
        self,
        browser: Browser,
        auth_state_path: Path,
    ) -> BrowserContext:
        try:
            return await browser.new_context(
                storage_state=str(auth_state_path),
                viewport={
                    "width": 1440,
                    "height": 900,
                },
            )
        except Exception as error:
            auth_state_path.unlink(missing_ok=True)
            raise ValueError(
                "The saved LinkedIn session could "
                "not be loaded. Login again from "
                "the dashboard."
            ) from error

    async def is_logged_in(self, page: Page) -> bool:
        current_url = page.url.lower()

        if "/login" in current_url:
            return False

        if self.is_security_page(current_url):
            return False

        logged_in_elements = page.locator(
            "a[href*='/mynetwork/']:visible, "
            "a[href*='/messaging/']:visible, "
            "a[href*='/notifications/']:visible"
        )

        if await logged_in_elements.count() > 0:
            return True

        return "/feed" in current_url

    async def wait_for_result(self, page: Page) -> str:
        # Keep the browser available for up to
        # three minutes for OTP or verification.
        for _ in range(180):
            current_url = page.url.lower()

            if self.is_security_page(current_url):
                print(
                    "LinkedIn security verification "
                    "detected. Complete it manually."
                )
                await asyncio.sleep(1)
                continue

            if await self.is_logged_in(page):
                return "success"

            error_locator = page.locator(
                "#error-for-username:visible, "
                "#error-for-password:visible, "
                "[role='alert']:visible"
            )

            if await error_locator.count() > 0:
                try:
                    error_text = (
                        await error_locator
                        .first
                        .inner_text()
                    )
                    if error_text.strip():
                        print(
                            "LinkedIn login error:",
                            error_text,
                        )
                        return "failed"
                except Exception:
                    pass

            await asyncio.sleep(1)

        if self.is_security_page(page.url.lower()):
            return "verification"

        return "failed"

    def is_security_page(self, current_url: str) -> bool:
        markers = [
            "checkpoint",
            "challenge",
            "captcha",
            "verification",
        ]

        return any(
            marker in current_url
            for marker in markers
        )


linkedin_login_service = LinkedInLoginService()
