from pydantic import BaseModel, Field, SecretStr, field_validator


class LinkedInLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=500)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        cleaned = value.strip()
        if "@" not in cleaned:
            raise ValueError("Enter a valid LinkedIn email address.")
        return cleaned


class LinkedInLoginResponse(BaseModel):
    status: str
    message: str
    current_url: str = ""
    session_saved: bool = False
