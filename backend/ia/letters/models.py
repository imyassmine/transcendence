import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .gdpr import Ground


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class LetterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    account_email: str = Field(max_length=254)
    service_name: str = Field(min_length=1, max_length=100)
    domain: str | None = None
    username: str | None = Field(None, max_length=100)
    recipient_email: str | None = Field(None, max_length=254)

    grounds: set[Ground] = {Ground.CONSENT_WITHDRAWN}
    oppose_marketing: bool = True
    inactive_since: date | None = None
    data_public: bool = False
    breached: bool = False

    extra_context: str | None = Field(None, max_length=500)

    @field_validator("account_email", "recipient_email")
    @classmethod
    def check_email(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("adresse e-mail invalide")
        return v


class Letter(BaseModel):
    subject: str
    body: str
    recipient_email: str | None
    legal_refs: list[str]
    generated_by: Literal["llm", "template"]
    warnings: list[str] = []
