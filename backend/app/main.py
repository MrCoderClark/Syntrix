from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.auth.oauth import register_oauth_providers
from app.auth.router import router as auth_router
from app.comments.router import router as comments_router
from app.communities.router import router as communities_router
from app.config import get_settings
from app.feeds.router import router as feeds_router
from app.posts.og import router as og_router
from app.posts.router import router as posts_router
from app.profiles.router import router as profiles_router
from app.search.router import router as search_router
from app.storage.router import router as storage_router
from app.votes.router import router as votes_router

settings = get_settings()

app = FastAPI(title="Syntrix", version="0.1.0")

app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)

register_oauth_providers()

app.include_router(auth_router)
app.include_router(comments_router)
app.include_router(communities_router)
app.include_router(feeds_router)
app.include_router(og_router)
app.include_router(posts_router)
app.include_router(profiles_router)
app.include_router(search_router)
app.include_router(storage_router)
app.include_router(votes_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
