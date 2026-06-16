from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.auth.oauth import register_oauth_providers
from app.auth.router import router as auth_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Syntrix", version="0.1.0")

app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)

register_oauth_providers()

app.include_router(auth_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
