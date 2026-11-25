from pydantic import BaseModel, ConfigDict
from src.schemas.common import DocId

class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    course_id: DocId
