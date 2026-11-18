from typing import Annotated
from pydantic import Field

DocId = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")]
