from crewai import LLM

from app.core.config import get_settings


def create_llm(
    temperature: float = 0.0,
) -> LLM:
    settings = get_settings()

    api_key = (
        settings.groq_api_key
        .get_secret_value()
        .strip()
    )

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing in .env"
        )

    return LLM(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=90,
        max_retries=2,
    )