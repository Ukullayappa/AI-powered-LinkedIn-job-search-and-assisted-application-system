from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "ApplyPilot AI"

    # AI model
    groq_api_key: SecretStr = SecretStr("")

    llm_model: str = (
        "openai/llama-3.3-70b-versatile"
    )

    llm_base_url: str = (
        "https://api.groq.com/openai/v1"
    )

    # LinkedIn
    linkedin_email: str = ""
    linkedin_password: SecretStr = SecretStr("")
    linkedin_headless: bool = False

    # Application automation
    auto_submit: bool = False

    max_applications_per_run: int = Field(
        default=5,
        ge=1,
        le=5,
    )

    minimum_match_score: int = Field(
        default=70,
        ge=0,
        le=100,
    )

    # Only ranked job details are stored locally.
    data_directory: Path = Path("data")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def create_directories(self) -> None:
        self.data_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.create_directories()
    return settings
