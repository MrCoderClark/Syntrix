from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.auth.oauth import register_oauth_providers
from app.auth.router import router as auth_router
from app.communities.router import router as communities_router
from app.config import get_settings
from app.profiles.router import router as profiles_router
from app.storage.router import router as storage_router

settings = get_settings()

app = FastAPI(title="Syntrix", version="0.1.0")

app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)

register_oauth_providers()

app.include_router(auth_router)
app.include_router(communities_router)
app.include_router(profiles_router)
app.include_router(storage_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
