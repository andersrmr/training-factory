from typing import Any

from pydantic import BaseModel, Field


class TrainingState(BaseModel):
    request: dict[str, Any]
    brief: dict[str, Any] = Field(default_factory=dict)
    curriculum: dict[str, Any] = Field(default_factory=dict)
    lab: dict[str, Any] = Field(default_factory=dict)
    slides: dict[str, Any] = Field(default_factory=dict)
    qa: dict[str, Any] = Field(default_factory=dict)
    packaging: dict[str, Any] = Field(default_factory=dict)
    revision_count: int = 0
