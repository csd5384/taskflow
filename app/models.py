"""Request and response models for the to-do API."""

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """Payload for creating a to-do."""

    title: str = Field(min_length=1, max_length=200)


class TodoUpdate(BaseModel):
    """Payload for updating a to-do. Every field is optional."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


class Todo(BaseModel):
    """A stored to-do item."""

    id: int
    title: str
    done: bool = False
