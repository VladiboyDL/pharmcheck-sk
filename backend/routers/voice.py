"""Voice session brokering for the kiosk.

The browser never sees the ElevenLabs API key. It asks this endpoint for a signed
URL, which is short-lived and scoped to one conversation; the key stays on the
server. When nothing is configured the endpoint says so plainly rather than letting
the kiosk fail silently — the tap flow works either way, so voice is additive.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

SIGNED_URL_ENDPOINT = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"


def _config() -> tuple[str, str]:
    return os.getenv("ELEVENLABS_API_KEY", ""), os.getenv("ELEVENLABS_AGENT_ID", "")


class SessionRequest(BaseModel):
    # Passed to the agent as dynamic variables so it can talk about this patient's
    # actual medicines rather than in generalities.
    patient_name: str | None = None
    medicines: str | None = None
    schedule: str | None = None
    findings: str | None = None


@router.get("/config")
def config():
    """Whether voice is available, without exposing anything secret."""
    api_key, agent_id = _config()
    return {
        "enabled": bool(api_key and agent_id),
        "agent_id": agent_id or None,
        "reason": (
            None
            if api_key and agent_id
            else "Hlasový agent nie je nakonfigurovaný — nastavte ELEVENLABS_API_KEY a ELEVENLABS_AGENT_ID."
        ),
    }


@router.post("/session")
def session(req: SessionRequest):
    """A short-lived signed URL for one conversation, plus this patient's context."""
    api_key, agent_id = _config()
    variables = {
        "patient_name": req.patient_name or "pacient",
        "medicines": req.medicines or "",
        "schedule": req.schedule or "",
        "findings": req.findings or "",
    }

    if not api_key or not agent_id:
        return {
            "enabled": False,
            "reason": "Hlasový agent nie je nakonfigurovaný.",
            "dynamic_variables": variables,
        }

    try:
        url = f"{SIGNED_URL_ENDPOINT}?{urllib.parse.urlencode({'agent_id': agent_id})}"
        request = urllib.request.Request(url, headers={"xi-api-key": api_key})
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read())
        return {
            "enabled": True,
            "agent_id": agent_id,
            "signed_url": data.get("signed_url"),
            "dynamic_variables": variables,
        }
    except Exception as e:
        logger.warning(f"voice session failed: {e}")
        return {
            "enabled": False,
            "reason": "Hlasovú reláciu sa nepodarilo otvoriť.",
            "dynamic_variables": variables,
        }
