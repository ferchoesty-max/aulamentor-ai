from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
class ReinforcementActivity(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=1000)

def normalize_topic(value: str) -> str:
    return " ".join(value.split())

def clean_options(values: list[str]) -> list[str]:
    options = [" ".join(item.split()) for item in values]
    if any(not 1 <= len(item) <= 200 for item in options):
        raise ValueError("cada opción debe tener entre 1 y 200 caracteres")
    if len({item.casefold() for item in options}) != len(options):
        raise ValueError("las 4 opciones deben ser distintas entre sí")
    return options
class QuestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    topic: str = Field(min_length=2, max_length=80)
    difficulty: int = Field(ge=1, le=3, strict=True)  # 1 básico, 2 intermedio, 3 avanzado
    statement: str = Field(min_length=5, max_length=500)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3, strict=True)
    reinforcement_activity: Optional[ReinforcementActivity] = None

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, value: str) -> str:
        return normalize_topic(value)

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        return clean_options(value)
class QuestionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    topic: Optional[str] = Field(default=None, min_length=2, max_length=80)
    difficulty: Optional[int] = Field(default=None, ge=1, le=3, strict=True)
    statement: Optional[str] = Field(default=None, min_length=5, max_length=500)
    options: Optional[list[str]] = Field(default=None, min_length=4, max_length=4)
    correct_index: Optional[int] = Field(default=None, ge=0, le=3, strict=True)
    reinforcement_activity: Optional[ReinforcementActivity] = None
    active: Optional[bool] = None

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, value):
        return normalize_topic(value) if value is not None else value

    @field_validator("options")
    @classmethod
    def validate_options(cls, value):
        return clean_options(value) if value is not None else value

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("envía al menos un campo para actualizar")
        return self
