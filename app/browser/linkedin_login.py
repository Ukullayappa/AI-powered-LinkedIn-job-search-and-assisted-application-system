import asyncio
import re
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
        self.session_state: dict | None = None

    async def login(
        self,
        email: str | None = None,
        password: str | None = None,
    ) -> LinkedInLoginResponse:
        """
        Credentials supplied:
            Create a fresh LinkedIn session.

        No credentials supplied:
            Reuse the in-memory session. The agent
            orchestrator uses this mode.

        The email and password are never saved.
        """

        supplied_email = email.strip() if email else ""
        supplied_password = password if password else ""

        has_credentials = bool(
            supplied_email and supplied_password
        )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                slow_mo=250,
            )

            try:
                if has_credentials:
                    # A fresh login replaces the previous
                    # in-memory browser session.
                    self.session_state = None

                    context = await browser.new_context(
                        viewport={
                            "width": 1440,
                            "height": 900,
                        }
                    )

                    return await self.login_with_credentials(
                        context=context,
                        email=supplied_email,
                        password=supplied_password,
                    )

                context = await self.create_saved_context(
                    browser=browser,
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
                            "Existing in-memory LinkedIn session "
                            "loaded successfully."
                        ),
                        current_url=page.url,
                        session_saved=True,
                    )

                self.session_state = None

                raise ValueError(
                    "The in-memory LinkedIn session "
                    "expired. Enter your LinkedIn email "
                    "and password in the dashboard again."
                )

            finally:
                await browser.close()

    async def login_with_credentials(
        self,
        context: BrowserContext,
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
            raise RuntimeError(
                "Visible LinkedIn login fields were "
                "not found."
            ) from error

        print("LinkedIn email field found.")
        await email_input.fill(email)

        print("LinkedIn password field found.")
        await password_input.fill(password)

        # Select only LinkedIn's normal email/password
        # Sign in button. Do not select social-login
        # buttons such as "Continue with Google".
        sign_in_button = page.get_by_role(
            "button",
            name=re.compile(
                r"^\\s*sign\\s+in\\s*$",
                re.IGNORECASE,
            ),
        ).first

        if await sign_in_button.count() > 0:
            await sign_in_button.wait_for(
                state="visible",
                timeout=30000,
            )

            print(
                "Clicking LinkedIn email/password "
                "Sign in button."
            )

            await sign_in_button.click()

        else:
            # Pressing Enter while focused on the password
            # field submits the email/password form without
            # clicking a Google or Apple login button.
            print(
                "Exact Sign in button was not found. "
                "Submitting from the password field."
            )

            await password_input.press("Enter")

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

        self.session_state = (
            await context.storage_state(
                indexed_db=True,
            )
        )

        return LinkedInLoginResponse(
            status="logged_in",
            message=(
                "LinkedIn login successful. "
                "The browser session is kept in memory "
                "until the backend stops."
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

    def get_session_state(
        self,
    ) -> dict:
        if not self.session_state:
            raise ValueError(
                "LinkedIn session was not found. "
                "Enter your LinkedIn email and password "
                "in the dashboard first."
            )

        return self.session_state

    async def create_saved_context(
        self,
        browser: Browser,
    ) -> BrowserContext:
        try:
            return await browser.new_context(
                storage_state=self.get_session_state(),
                viewport={
                    "width": 1440,
                    "height": 900,
                },
            )
        except Exception as error:
            self.session_state = None
            raise ValueError(
                "The in-memory LinkedIn session could "
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
