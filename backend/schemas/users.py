from uuid import UUID

from pydantic import BaseModel

class User(BaseModel):
    id: UUID
    name: str
    #TODO finish the User model