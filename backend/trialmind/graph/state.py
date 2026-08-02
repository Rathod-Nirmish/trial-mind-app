from datetime import datetime
from pydantic import BaseModel, Field
from trialmind.db import SearchHit


class TraceEvent(BaseModel):
    agent: str
    at: datetime = Field(default_factory=datetime.utcnow)
    summary: str
    payload: dict = Field(default_factory=dict)


class CheckResult(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)


class AgentState(BaseModel):
    question: str
    chunks: list[SearchHit] = Field(default_factory=list)
    draft_answer: str = ""
    check_result: CheckResult | None = None
    iteration: int = 0
    trace: list[TraceEvent] = Field(default_factory=list)
    refined_query: str | None = None
    citation_id_map: dict[str, str] = Field(default_factory=dict)
