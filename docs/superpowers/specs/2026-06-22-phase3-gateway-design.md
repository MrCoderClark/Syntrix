# Phase 3, Subsystem 1: WebSocket Gateway & Presence Infrastructure — Design Spec

**Date:** 2026-06-22
**Phase:** 3 (Real-time Chat)
**Subsystem:** 1 of 4
**Ships:** Dedicated WS gateway, Redis pub/sub, connection management, presence system, frontend WS client

## Overview

Foundation infrastructure for Syntrix's real-time chat. A standalone Starlette
WebSocket gateway (`gateway/` package) communicates with the existing FastAPI
backend via Redis pub/sub. This subsystem delivers the plumbing — no chat rooms,
messages, or UI yet. After this lands, a user can connect via WebSocket, see
their presence tracked, and observe typing/presence events.

## Subsystem Roadmap (Phase 3)

1. **Gateway & Presence Infrastructure** ← this spec
2. **Chat Rooms & Messages** — room CRUD, message persistence, rich content
3. **Private Rooms, DMs & Private Communities** — invites, DMs, community visibility
4. **Chat UI & Polish** — room list, message view, composer, presence indicators, search

Each subsystem gets its own spec → plan → implementation cycle.

---

## 1. Gateway Architecture

`gateway/` is a standalone Starlette app with its own `pyproject.toml` and
venv. Runs on port 8002 alongside the backend (8001) and frontend (3000).

**Responsibilities:**
- Accept WebSocket connections from authenticated users
- Verify JWT independently (same `JWT_SECRET`, same HS256 algorithm)
- Manage connection lifecycle (connect, heartbeat, disconnect)
- Route messages between clients via Redis pub/sub
- Track presence state in Redis
- Serve no REST endpoints — pure WebSocket

**Communication flow:**

```
Browser <--WS--> Gateway (port 8002) <--Redis pub/sub--> Backend (port 8001)
                                     <--Redis--> Presence state
```

The backend publishes events to Redis when things happen (new message saved,
room created, user kicked). The gateway subscribes and pushes to connected
clients. When a client sends a message, the gateway publishes to Redis, the
backend consumes it, persists to Postgres, then publishes the confirmed message
back through Redis for broadcast.

**The backend persists, not the gateway.** The backend owns all DB access and
authorization. The gateway is a dumb pipe with auth at the door.

## 2. Connection & Authentication

**WebSocket endpoint:** `ws://localhost:8002/ws`

**Auth flow:**
1. Client opens WS connection with the JWT in a query param:
   `ws://localhost:8002/ws?token=<jwt>` (WebSocket API doesn't support cookies
   cross-origin reliably)
2. Gateway verifies JWT signature + expiration using the shared `JWT_SECRET`
3. On success: connection accepted, user added to connection manager, presence
   set to "online"
4. On failure: connection rejected with WS close code 4001 (unauthorized)
5. Token refresh: client must close and reconnect with a fresh token before
   expiry. Gateway sends a `token_expiring` event ~60s before expiration so the
   client can refresh proactively

**Connection manager (in-memory):**
- Maps `user_id → set[WebSocket]` — one user can have multiple tabs/devices
- Maps `room_id → set[user_id]` — who's subscribed to which room
- On disconnect: remove from both maps, update presence

**Heartbeat:**
- Client sends `ping` every 30s
- Gateway responds with `pong`
- If no ping for 90s, gateway closes the connection and sets presence to offline
- Standard WS ping/pong frames, not application-level messages

## 3. Presence System

**Presence states:** online, idle, DND (do not disturb), invisible. Users set
their status explicitly; idle is also auto-set after 5 minutes of no activity
(no messages sent, no heartbeat activity change).

**Storage — Redis:**
- `presence:{user_id}` — hash with `status`, `custom_status` (optional text,
  max 128 chars), `last_seen` (unix timestamp)
- `presence:online` — sorted set, score = last heartbeat timestamp. Used for
  bulk "who's online" queries
- TTL: presence keys expire after 120s. Each heartbeat refreshes the TTL. If the
  gateway crashes, presence auto-clears

**Last-seen:** Updated on every message sent and every heartbeat. Stored as a
unix timestamp. Visible to other users unless status is "invisible."

**Invisible:** User appears offline to others. Gateway still tracks them
internally (they receive messages, typing events, etc.) but their presence is
not broadcast and `last_seen` is not updated publicly.

**Typing indicators:**
- Client sends `typing_start` when user begins typing in a room
- Gateway broadcasts `user_typing` to other room members
- Auto-expires after 3s if no follow-up `typing_start`
- `typing_stop` sent explicitly when user clears the input or sends the message
- Typing state is ephemeral — in-memory only, not persisted to Redis

**Presence broadcast:**
- When a user's status changes, gateway publishes to Redis channel
  `presence:{user_id}`
- Other gateway instances (future scaling) subscribe and push to relevant clients
- Clients receive presence updates only for users in their current room list
  (not all users globally)

## 4. Redis Pub/Sub Contract

### Channels

| Channel pattern | Publisher | Subscriber | Purpose |
|---|---|---|---|
| `room:{room_id}` | Backend, Gateway | Gateway | Messages, edits, deletes in a room |
| `dm:{conversation_id}` | Backend | Gateway | Direct message events |
| `presence:{user_id}` | Gateway | Gateway | Status changes (multi-instance sync) |
| `system:{user_id}` | Backend | Gateway | Per-user system events (kicked, invited, room created) |

### Message envelope

Every Redis message is JSON with a standard wrapper:

```json
{
  "type": "message.created",
  "room_id": "uuid",
  "payload": { ... },
  "ts": 1719014400
}
```

### Event types

| Type | Direction | Payload |
|---|---|---|
| `message.created` | backend → gateway → clients | message object |
| `message.edited` | backend → gateway → clients | message id + new content |
| `message.deleted` | backend → gateway → clients | message id |
| `typing.start` | client → gateway → room members | user_id, room_id |
| `typing.stop` | client → gateway → room members | user_id, room_id |
| `presence.update` | gateway → gateway(s) → clients | user_id, status, last_seen |
| `room.user_joined` | backend → gateway → room members | user_id, room_id |
| `room.user_left` | backend → gateway → room members | user_id, room_id |
| `system.invited` | backend → gateway → target user | room_id, invited_by |
| `system.kicked` | backend → gateway → target user | room_id, reason |
| `token_expiring` | gateway → client | seconds_remaining |

### Client → server messages

Go through the WebSocket as JSON with the same `type` + `payload` structure.
The gateway validates the shape, then either handles locally (typing, presence)
or publishes to Redis for the backend to consume and persist.

### Backend consumption

The backend runs a Redis subscriber in a background task (asyncio) that listens
for `client.send_message` events, validates, persists to Postgres, then
publishes the confirmed `message.created` back to Redis for broadcast.

## 5. Docker & Dev Setup

**Redis container** added to the existing Supabase Docker Compose stack:

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

No auth for local dev (same as Supabase Postgres). Production would add
`requirepass`.

**Gateway process:** Runs locally via `uv run uvicorn gateway.main:app --port 8002`.
Not containerized in dev (matches the project convention: backend/frontend run
locally, only infra is Docker).

**Frontend proxy:** Next.js `next.config.js` gets a new rewrite rule to proxy
`/ws` to `localhost:8002`, so the browser connects to `localhost:3000/ws` and
Next.js forwards it. Avoids CORS issues and keeps the client unaware of the
gateway port.

**Environment variables (gateway):**
- `JWT_SECRET` — same value as backend
- `REDIS_URL` — `redis://localhost:6379/0`
- `GATEWAY_PORT` — default 8002

**`make dev` update:** Starts the gateway process alongside backend and
frontend. Three terminal processes total (backend 8001, gateway 8002, frontend
3000) plus Docker for Postgres/Storage/Redis.

## 6. Scope

### In scope

- `gateway/` package: Starlette app, JWT verification, connection manager
- Redis container added to Docker Compose
- Presence system (online/idle/DND/invisible, last-seen, typing indicators)
- Redis pub/sub contract (channels, envelope format, event types)
- Frontend WebSocket client utility (connect, reconnect, heartbeat, token refresh)
- Dev setup updates (Next.js proxy, `make dev`, env vars)
- Basic connection test (connect, auth, heartbeat, presence round-trip)

### Out of scope (later subsystems)

- Chat rooms, room CRUD, room membership (Subsystem 2)
- Messages, message persistence, rich content (Subsystem 2)
- Private rooms, invites, DMs (Subsystem 3)
- Private communities (Subsystem 3)
- Chat UI — room list, message view, composer (Subsystem 4)
- Message search (Subsystem 4)
- Notifications (not in Phase 3 scope)
