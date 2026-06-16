from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from app.config import get_settings

oauth = OAuth()


def register_oauth_providers() -> None:
    settings = get_settings()

    if settings.github_client_id:
        oauth.register(
            name="github",
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            authorize_url="https://github.com/login/oauth/authorize",
            access_token_url="https://github.com/login/oauth/access_token",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )

    if settings.google_client_id:
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if settings.discord_client_id:
        oauth.register(
            name="discord",
            client_id=settings.discord_client_id,
            client_secret=settings.discord_client_secret,
            authorize_url="https://discord.com/api/oauth2/authorize",
            access_token_url="https://discord.com/api/oauth2/token",
            api_base_url="https://discord.com/api/v10/",
            client_kwargs={"scope": "identify email"},
        )


async def fetch_user_info(provider: str, token: dict) -> dict:
    client = oauth.create_client(provider)
    if provider == "github":
        resp = await client.get("user", token=token)
        data = resp.json()
        email = data.get("email")
        if not email:
            emails_resp = await client.get("user/emails", token=token)
            for e in emails_resp.json():
                if e.get("primary") and e.get("verified"):
                    email = e["email"]
                    break
        return {
            "sub": str(data["id"]),
            "email": email,
            "name": data.get("name") or data["login"],
            "avatar_url": data.get("avatar_url"),
        }
    elif provider == "google":
        resp = await client.get("https://openidconnect.googleapis.com/v1/userinfo", token=token)
        data = resp.json()
        return {
            "sub": data["sub"],
            "email": data.get("email"),
            "name": data.get("name", ""),
            "avatar_url": data.get("picture"),
        }
    elif provider == "discord":
        resp = await client.get("users/@me", token=token)
        data = resp.json()
        avatar_url = None
        if data.get("avatar"):
            avatar_url = f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}.png"
        return {
            "sub": data["id"],
            "email": data.get("email"),
            "name": data.get("global_name") or data["username"],
            "avatar_url": avatar_url,
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")
