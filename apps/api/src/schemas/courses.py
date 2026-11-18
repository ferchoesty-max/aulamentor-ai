from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_topics(values: list[str]) -> list[str]:
    """Limpia espacios, valida longitud y rechaza temas repetidos (sin distinguir mayúsculas)."""
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
