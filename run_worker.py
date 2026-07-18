from __future__ import annotations

import asyncio
from getpass import getpass

from app.browser.linkedin_login import (
    linkedin_login_service,
)
from app.core.config import get_settings
from app.schemas.agent_schema import (
    AgentStartRequest,
)
from app.services.agent_orchestrator import (
    agent_orchestrator,
)
from app.services.agent_state_service import (
    agent_state_service,
)


settings = get_settings()


async def login_to_linkedin() -> None:
    email = settings.linkedin_email.strip()

    password = (
        settings.linkedin_password
        .get_secret_value()
    )

    if not email:
        email = input(
            "LinkedIn email: "
        ).strip()

    if not password:
        password = getpass(
            "LinkedIn password: "
        )

    if not email or not password:
        raise ValueError(
            "LinkedIn email and password "
            "are required."
        )

    result = await linkedin_login_service.login(
        email=email,
        password=password,
    )

    password = ""

    if result.status != "logged_in":
        raise RuntimeError(
            result.message
        )

    print()
    print(result.message)
    print()


async def run_worker() -> None:
    if settings.cloud_mode:
        raise RuntimeError(
            "CLOUD_MODE must be false on the "
            "Windows worker."
        )

    print("ApplyPilot Windows worker")
    print("-------------------------")
    print(
        "LinkedIn credentials remain on this "
        "computer."
    )
    print()

    await login_to_linkedin()

    print(
        "Worker is connected to Supabase."
    )
    print(
        "Waiting for a queued agent run..."
    )
    print(
        "Press Ctrl+C to stop the worker."
    )
    print()

    while True:
        queued_state = (
            agent_state_service
            .claim_next_queued()
        )

        if not queued_state:
            await asyncio.sleep(
                settings.worker_poll_seconds
            )
            continue

        run_id = queued_state["run_id"]

        request = (
            AgentStartRequest.model_validate(
                queued_state.get(
                    "settings",
                    {},
                )
            )
        )

        print(
            f"Claimed run: {run_id}"
        )
        print(
            "Starting LinkedIn job workflow..."
        )

        await agent_orchestrator.run_workflow(
            request
        )

        completed_state = (
            agent_state_service.get()
        )

        print(
            "Run finished with status:",
            completed_state.get(
                "status",
                "unknown",
            ),
        )
        print()
        print(
            "Waiting for another queued run..."
        )


def main() -> None:
    try:
        asyncio.run(
            run_worker()
        )
    except KeyboardInterrupt:
        print()
        print("Windows worker stopped.")
    except Exception as error:
        print()
        print(
            "Windows worker failed:",
            error,
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()