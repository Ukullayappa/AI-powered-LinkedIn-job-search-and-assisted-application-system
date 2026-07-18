import json
from pathlib import Path

from app.repositories.profile_repository import (
    profile_repository,
)


PROFILE_FILE = Path("data/profile.json")


def load_local_profile() -> dict:
    """
    Read the existing local profile JSON.
    """

    if not PROFILE_FILE.is_file():
        raise FileNotFoundError(
            "data/profile.json was not found. "
            "Upload and analyze a resume first."
        )

    profile_data = json.loads(
        PROFILE_FILE.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(profile_data, dict):
        raise ValueError(
            "data/profile.json must contain "
            "a JSON object."
        )

    if not profile_data:
        raise ValueError(
            "data/profile.json is empty."
        )

    return profile_data


def migrate_profile() -> None:
    """
    Copy the local profile into Supabase.
    """

    print(
        "Reading local profile..."
    )

    profile_data = load_local_profile()

    print(
        "Saving profile to Supabase..."
    )

    saved_profile = profile_repository.save(
        profile_data
    )

    print(
        "Profile saved successfully."
    )

    print(
        "Profile ID:",
        saved_profile.get("id"),
    )

    print(
        "Full name:",
        saved_profile.get("full_name"),
    )

    print(
        "Email:",
        saved_profile.get("email"),
    )


if __name__ == "__main__":
    migrate_profile()