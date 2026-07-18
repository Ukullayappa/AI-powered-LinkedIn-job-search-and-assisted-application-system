import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


@lru_cache
def get_supabase_client() -> Client:
    """
    Create one reusable Supabase client.

    The URL and secret key are loaded only from
    backend environment variables.
    """

    supabase_url = os.getenv(
        "SUPABASE_URL",
        "",
    ).strip()

    supabase_secret_key = os.getenv(
        "SUPABASE_SECRET_KEY",
        "",
    ).strip()

    if not supabase_url:
        raise ValueError(
            "SUPABASE_URL is missing in .env"
        )

    if not supabase_secret_key:
        raise ValueError(
            "SUPABASE_SECRET_KEY is missing in .env"
        )

    return create_client(
        supabase_url,
        supabase_secret_key,
    )


supabase_client = get_supabase_client()