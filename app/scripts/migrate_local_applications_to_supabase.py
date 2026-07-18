from __future__ import annotations

import json
from pathlib import Path

from app.repositories.application_repository import (
    application_repository,
)


def main() -> None:
    local_path = Path(
        "data/applications.json"
    )

    if not local_path.is_file():
        print(
            "No local application history was found."
        )
        return

    try:
        applications = json.loads(
            local_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        json.JSONDecodeError,
        OSError,
    ) as error:
        raise RuntimeError(
            "Local applications.json could "
            "not be read."
        ) from error

    if not isinstance(
        applications,
        list,
    ):
        raise ValueError(
            "Local applications.json must "
            "contain a list."
        )

    migrated_count = 0

    for application in applications:
        if not isinstance(
            application,
            dict,
        ):
            continue

        if not application.get(
            "job_id"
        ):
            continue

        application_repository.save_submitted(
            application
        )

        migrated_count += 1

    print(
        "Applications migrated to Supabase:",
        migrated_count,
    )


if __name__ == "__main__":
    main()
