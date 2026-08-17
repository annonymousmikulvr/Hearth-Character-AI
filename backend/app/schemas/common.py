from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class IdResponse(BaseModel):
    id: str
