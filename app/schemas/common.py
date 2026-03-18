from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseSchema):
    message: str


class ErrorResponse(BaseSchema):
    detail: str


class Timestamped(BaseSchema):
    created_at: datetime
    updated_at: datetime
