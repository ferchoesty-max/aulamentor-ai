from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

def normalize_topics(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        topic = " ".join(raw.split())
        if not 2 <= len(topic) <= 80:
            raise ValueError("cada tema debe tener entre 2 y 80 caracteres")
        key = topic.casefold()
        if key in seen:
            raise ValueError(f"el tema '{topic}' está repetido")
        seen.add(key)
        cleaned.append(topic)
    return cleaned
class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9._-]+$")
    description: str = Field(default="", max_length=1000)
    topics: list[str] = Field(min_length=1, max_length=30)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("topics")
    @classmethod
    def clean_topics(cls, value: list[str]) -> list[str]:
        return normalize_topics(value)
class CourseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    topics: Optional[list[str]] = Field(default=None, min_length=1, max_length=30)
    status: Optional[Literal["active", "archived"]] = None

    @field_validator("topics")
    @classmethod
    def clean_topics(cls, value):
        return normalize_topics(value) if value is not None else value

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("envía al menos un campo para actualizar")
        return self
