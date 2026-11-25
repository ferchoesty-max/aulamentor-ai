from pydantic import BaseModel, ConfigDict, Field
from src.schemas.common import DocId

class AnswerItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question_id: DocId
    selected_index: int = Field(ge=0, le=3, strict=True)

class AttemptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    course_id: DocId
    answers: list[AnswerItem] = Field(min_length=1, max_length=100)
