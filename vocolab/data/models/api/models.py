from datetime import datetime
from typing import Optional

from pydantic import BaseModel, AnyHttpUrl, Field


class NewModelIdRequest(BaseModel):
    description: str
    gpu_budget: str
    train_set: str
    authors: str
    institution: str
    team: str
    paper_url: Optional[AnyHttpUrl]
    code_url: Optional[AnyHttpUrl]
    created_at: datetime = Field(default_factory=lambda: datetime.now())
