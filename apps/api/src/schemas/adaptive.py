from typing import Literal

from pydantic import BaseModel, ConfigDict

RecommendationStatus = Literal["pending", "in_progress", "completed"]


class RecommendationStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: RecommendationStatus
