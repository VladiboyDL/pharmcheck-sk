"""Guards for endpoints that leak data, cost money, or can be turned into a relay.

There is no login here on purpose — a pharmacy kiosk has no user to authenticate,
and the demo has to open from a URL. So the defences are the ones that work without
identity: never return more than the caller needs, make public URLs unguessable, and
cap how often anyone can spend our money.
"""
from __future__ import annotations

import os
import secrets
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

# ── Rate limiting ─────────────────────────────────────────────────────────────
# In-process and per-IP. Behind more than one worker this under-counts, which is
# acceptable: it exists to stop casual abuse and runaway cost, not a botnet.

_HITS: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def rate_limit(request: Request, bucket: str, limit: int, window_secs: int = 60) -> None:
    """Allow `limit` calls per `window_secs` from one address, then refuse."""
    client = request.client.host if request.client else "unknown"
    key = (bucket, client)
    now = time.time()
    hits = _HITS[key]
    while hits and now - hits[0] > window_secs:
        hits.popleft()
    if len(hits) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Priveľa požiadaviek. Skúste o chvíľu znova.",
            headers={"Retry-After": str(window_secs)},
        )
    hits.append(now)


# ── Masking ───────────────────────────────────────────────────────────────────


def mask_name(name: str | None) -> str:
    """"Vladimír Rovčanin" -> "V. R." — enough to recognise a row, not to identify."""
    if not name:
        return "—"
    return " ".join(f"{part[0]}." for part in name.split() if part)


def public_token() -> str:
    """A URL-safe secret for links that are shared but not authenticated."""
    return secrets.token_urlsafe(24)


# ── Origins ───────────────────────────────────────────────────────────────────


def allowed_origins() -> list[str]:
    """Wide-open CORS on an unauthenticated health API lets any page read it.

    Defaults cover local development and the deployed demo; override with
    ALLOWED_ORIGINS (comma-separated) for anything else.
    """
    configured = os.getenv("ALLOWED_ORIGINS", "").strip()
    if configured:
        return [o.strip() for o in configured.split(",") if o.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://pharmcheck-dashboard.onrender.com",
    ]
