from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import Community, Post

from .schemas import SimilarBodyRequest, SimilarQuestionItem, SimilarQuestionsResponse

router = APIRouter(prefix="/api/communities/{slug}/questions", tags=["similarity"])

LIMIT = 5
TRGM_THRESHOLD = 0.3
TSRANK_THRESHOLD = 0.1


async def _get_community(slug: str, session: AsyncSession) -> Community:
    result = await session.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community


def _base_filter(community_id):
    return [
        Post.community_id == community_id,
        Post.post_type == "question",
        Post.deleted_at.is_(None),
        Post.removed_at.is_(None),
    ]


@router.get("/similar", response_model=SimilarQuestionsResponse)
async def similar_by_title(
    slug: str,
    title: str = Query(min_length=10, max_length=300),
    session: AsyncSession = Depends(get_session),
):
    community = await _get_community(slug, session)

    similarity = func.word_similarity(title, Post.title).label("similarity")
    stmt = (
        select(Post, similarity)
        .where(
            *_base_filter(community.id),
            func.word_similarity(title, Post.title) >= TRGM_THRESHOLD,
        )
        .order_by(similarity.desc())
        .limit(LIMIT)
    )
    result = await session.execute(stmt)
    rows = result.all()

    return SimilarQuestionsResponse(
        items=[
            SimilarQuestionItem(
                id=row.Post.id,
                title=row.Post.title,
                score=row.Post.score,
                answer_count=row.Post.answer_count,
                has_accepted_answer=row.Post.has_accepted_answer,
                similarity=round(float(row.similarity), 3),
            )
            for row in rows
        ]
    )


@router.post("/similar", response_model=SimilarQuestionsResponse)
async def similar_by_body(
    slug: str,
    body: SimilarBodyRequest,
    session: AsyncSession = Depends(get_session),
):
    community = await _get_community(slug, session)

    search_text = f"{body.title} {body.body_text}".strip()
    ts_query = func.plainto_tsquery("english", search_text)
    ts_rank = func.ts_rank_cd(Post.search_vector, ts_query).label("ts_rank")
    trgm_sim = func.word_similarity(body.title, Post.title).label("trgm_sim")
    combined = (ts_rank + trgm_sim).label("combined_score")

    stmt = (
        select(Post, combined)
        .where(
            *_base_filter(community.id),
            (func.ts_rank_cd(Post.search_vector, ts_query) >= TSRANK_THRESHOLD)
            | (func.word_similarity(body.title, Post.title) >= TRGM_THRESHOLD),
        )
        .order_by(combined.desc())
        .limit(LIMIT)
    )
    result = await session.execute(stmt)
    rows = result.all()

    return SimilarQuestionsResponse(
        items=[
            SimilarQuestionItem(
                id=row.Post.id,
                title=row.Post.title,
                score=row.Post.score,
                answer_count=row.Post.answer_count,
                has_accepted_answer=row.Post.has_accepted_answer,
                similarity=round(float(row.combined_score), 3),
            )
            for row in rows
        ]
    )
