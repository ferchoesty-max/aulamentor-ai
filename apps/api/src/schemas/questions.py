from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReinforcementActivity(BaseModel):
    """Lectura o ejercicio práctico asociado a una pregunta (lo usa el algoritmo de recomendación)."""

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
