from pydantic import BaseModel, Field


class VoteRequest(BaseModel):
    value: int = Field(ge=-1, le=1)


class VoteResponse(BaseModel):
    score: int
    user_vote: int
