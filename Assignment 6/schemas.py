"""
schemas.py — Pydantic v2 contracts for all role boundaries.

Every input and output that crosses a role boundary (Memory ↔ Perception ↔ Decision ↔ Action)
is typed with one of these models. No free-form dicts pass between roles.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    kind: Literal["fact", "preference", "tool_outcome", "scratchpad"]
    keywords: list[str]
    descriptor: str          # one short human-readable line
    value: dict              # structured payload extracted by LLM or construction
    artifact_id: str | None = None   # handle into artifact store e.g. "art:abc123..."
    source: str
    run_id: str
    goal_id: str | None = None
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Artifact(BaseModel):
    id: str                  # "art:<sha256[:16]>"
    content_type: str
    size_bytes: int
    source: str
    descriptor: str


class Goal(BaseModel):
    id: str                  # stable across iterations: "g1", "g2", ...
    text: str                # short imperative statement
    done: bool = False
    attach_artifact_id: str | None = None


class Observation(BaseModel):
    goals: list[Goal]

    @property
    def all_done(self) -> bool:
        return len(self.goals) > 0 and all(g.done for g in self.goals)

    def next_unfinished(self) -> Goal | None:
        for g in self.goals:
            if not g.done:
                return g
        return None


class ToolCall(BaseModel):
    name: str
    arguments: dict


class DecisionOutput(BaseModel):
    answer: str | None = None
    tool_call: ToolCall | None = None

    @property
    def is_answer(self) -> bool:
        return self.answer is not None


class ActionResult(BaseModel):
    descriptor: str
    artifact_id: str | None = None


class ActionEvent(BaseModel):
    kind: Literal["action"] = "action"
    iter: int
    goal_id: str
    tool: str
    arguments: dict
    result_descriptor: str
    artifact_id: str | None = None


class AnswerEvent(BaseModel):
    kind: Literal["answer"] = "answer"
    iter: int
    goal_id: str
    text: str


HistoryEvent = ActionEvent | AnswerEvent
