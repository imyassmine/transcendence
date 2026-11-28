from pydantic import BaseModel, EmailStr


class GoogleProfile(BaseModel):
    sub: str
    email: EmailStr
    email_verified: bool
    name: str | None = None
