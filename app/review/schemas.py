from pydantic import BaseModel, Field


class ReviewDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject|request_changes)$")
    note: str = ""
