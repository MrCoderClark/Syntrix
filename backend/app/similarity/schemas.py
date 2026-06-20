from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SimilarQuestionItem(BaseModel):
    id: UUID
    title: str
    score: int
    answer_count: int
    has_accepted_answer: bool
    similarity: float


class SimilarQuestionsResponse(BaseModel):
    items: list[SimilarQuestionItem]


class SimilarBodyRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body_text: str = Field(max_length=10000, default="")
