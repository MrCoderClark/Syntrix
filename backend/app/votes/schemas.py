from enum import Enum

from pydantic import BaseModel, Field


class VoteRequest(BaseModel):
    value: int = Field(ge=-1, le=1)


class VoteResponse(BaseModel):
    score: int
    user_vote: int


class VoteTargetType(str, Enum):
    post = "post"
    comment = "comment"
    answer = "answer"


class BatchVotesResponse(BaseModel):
    votes: dict[str, int]
