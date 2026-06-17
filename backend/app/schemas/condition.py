"""Feature 3 — Condition Explainer schemas."""
from pydantic import BaseModel, Field


class ConditionOut(BaseModel):
    name: str
    status: str | None = None


class ExplainRequest(BaseModel):
    condition: str = Field(min_length=1, max_length=200)
    level: str = Field(default="simple", pattern="^(simple|moderate|detailed)$")


class ExplanationOut(BaseModel):
    condition: str
    level: str
    explanation: str
    disclaimer: str
