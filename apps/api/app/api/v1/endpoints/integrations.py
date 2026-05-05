"""Integrations endpoints — per-user OAuth for Zoom & Slack.

Routes:
  GET  /integrations/zoom/connect    → redirect user to Zoom OAuth authorization URL
  GET  /integrations/zoom/callback   → Zoom redirects here after user approves; stores tokens
  GET  /integrations/zoom/status     → returns whether current user has connected Zoom
  DELETE /integrations/zoom/disconnect → removes the user's Zoom tokens
  POST /integrations/zoom/webhook    → receives Zoom meeting events (platform-level)
  POST /integrations/slack/webhook   → receives Slack events (platform-level)
"""

import hashlib
import hmac
import json
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import structlog
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models import Conversation, User, UserIntegration
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)
router = APIRouter()

ZOOM_AUTH_URL = "https://zoom.us/oauth/authorize"
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"

# Frontend URL for post-OAuth redirect
FRONTEND_URL = "https://vox-intel.vercel.app"


# ── Response schemas ───────────────────────────────────────────────────────────


class IntegrationStatus(BaseModel):
    provider: str
    connected: bool
    provider_email: str | None = None
    connected_at: datetime | None = None


# ── Zoom OAuth: Connect ────────────────────────────────────────────────────────


@router.get("/zoom/connect", summary="Start Zoom OAuth flow for current user")
async def zoom_connect(
    current_user: User = Depends(get_current_user),
) -> RedirectResponse:
    """
    Generates a Zoom OAuth authorization URL and redirects the user to Zoom.
    Embeds the user's ID in the 'state' parameter so we know who to link on callback.
    """
    if not settings.ZOOM_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zoom integration is not configured on this server.",
        )

    state = f"{current_user.id}:{secrets.token_urlsafe(16)}"
    redirect_uri = f"{settings.API_BASE_URL}/v1/integrations/zoom/callback"

    params = (
        f"response_type=code"
        f"&client_id={settings.ZOOM_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    return RedirectResponse(url=f"{ZOOM_AUTH_URL}?{params}")


# ── Zoom OAuth: Callback ───────────────────────────────────────────────────────


@router.get("/zoom/callback", summary="Zoom OAuth callback — stores user tokens")
async def zoom_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Zoom redirects here after the user approves.
    Exchanges the authorization code for access + refresh tokens and
    stores them against the user identified by 'state'.
    """
    # Extract user_id from state
    try:
        user_id_str, _ = state.split(":", 1)
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state parameter")

    redirect_uri = f"{settings.API_BASE_URL}/v1/integrations/zoom/callback"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            ZOOM_TOKEN_URL,
            params={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code != 200:
        logger.error("zoom.token_exchange_failed", status=resp.status_code, body=resp.text)
        return RedirectResponse(url=f"{FRONTEND_URL}/settings?zoom=error&msg=token_exchange_failed")

    token_data = resp.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    scope = token_data.get("scope", "")

    # Fetch Zoom user profile to get their Zoom email/ID
    zoom_email: str | None = None
    zoom_user_id: str | None = None
    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"{ZOOM_API_BASE}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_resp.status_code == 200:
            profile = profile_resp.json()
            zoom_email = profile.get("email")
            zoom_user_id = profile.get("id")

    # Upsert the integration record
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == user_id,
            UserIntegration.provider == "zoom",
        )
    )
    integration = result.scalar_one_or_none()

    if integration:
        integration.access_token = access_token
        integration.refresh_token = refresh_token
        integration.scope = scope
        integration.expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        integration.provider_email = zoom_email
        integration.provider_user_id = zoom_user_id
        integration.updated_at = datetime.now(UTC)
    else:
        integration = UserIntegration(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="zoom",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            scope=scope,
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            provider_email=zoom_email,
            provider_user_id=zoom_user_id,
        )
        db.add(integration)

    await db.flush()
    logger.info("zoom.connected", user_id=str(user_id), zoom_email=zoom_email)

    return RedirectResponse(url=f"{FRONTEND_URL}/settings?zoom=connected&tab=integrations")


# ── Zoom: Status ───────────────────────────────────────────────────────────────


@router.get("/zoom/status", response_model=IntegrationStatus, summary="Check Zoom connection status")
async def zoom_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntegrationStatus:
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == current_user.id,
            UserIntegration.provider == "zoom",
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        return IntegrationStatus(provider="zoom", connected=False)

    return IntegrationStatus(
        provider="zoom",
        connected=True,
        provider_email=integration.provider_email,
        connected_at=integration.created_at,
    )


# ── Zoom: Disconnect ───────────────────────────────────────────────────────────


@router.delete(
    "/zoom/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disconnect Zoom from current user account",
)
async def zoom_disconnect(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == current_user.id,
            UserIntegration.provider == "zoom",
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        await db.delete(integration)
        await db.flush()
        logger.info("zoom.disconnected", user_id=str(current_user.id))


# ── Zoom platform webhook (meeting.started / meeting.ended) ───────────────────


@router.post(
    "/zoom/webhook",
    status_code=status.HTTP_200_OK,
    summary="Zoom meeting event receiver (platform webhook)",
)
async def zoom_webhook(
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    body = await request.body()

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Zoom URL-validation challenge
    if payload.get("event") == "endpoint.url_validation":
        plain = payload["payload"]["plainToken"]
        signature = hmac.new(
            settings.ZOOM_CLIENT_SECRET.encode(),
            plain.encode(),
            hashlib.sha256,
        ).hexdigest()
        return {"plainToken": plain, "encryptedToken": signature}

    event = payload.get("event", "")
    meeting_payload = payload.get("payload", {}).get("object", {})
    meeting_id = str(meeting_payload.get("id", ""))
    topic = meeting_payload.get("topic", "Zoom Meeting")
    host_email = meeting_payload.get("host_email", "")

    if event == "meeting.started":
        # Find which VoxIntel user owns this Zoom account
        owner_id = await _find_owner_by_zoom_email(db, host_email)

        conv = Conversation(
            id=uuid.uuid4(),
            title=topic,
            source="zoom",
            external_id=meeting_id,
            status="active",
            owner_id=owner_id,
        )
        db.add(conv)
        await db.flush()
        logger.info("zoom.meeting.started", meeting_id=meeting_id, owner=str(owner_id))

    elif event == "meeting.ended":
        result = await db.execute(
            select(Conversation).where(Conversation.external_id == meeting_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.status = "ended"
            conv.ended_at = datetime.now(UTC)
            await db.flush()
            background.add_task(_enqueue_summarise, str(conv.id))
            logger.info("zoom.meeting.ended", meeting_id=meeting_id)

    return {"received": True}


# ── Slack webhook ─────────────────────────────────────────────────────────────


@router.post(
    "/slack/webhook",
    status_code=status.HTTP_200_OK,
    summary="Slack Events API receiver",
)
async def slack_webhook(request: Request) -> dict:
    body = await request.body()
    _verify_slack_signature(request, body)

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    event = payload.get("event", {})
    logger.info("slack.event.received", type=event.get("type"))
    return {"ok": True}


# ── Internal helpers ───────────────────────────────────────────────────────────


async def _find_owner_by_zoom_email(db: AsyncSession, zoom_email: str) -> uuid.UUID | None:
    """Look up which VoxIntel user has connected the Zoom account with this email."""
    if not zoom_email:
        return None
    result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.provider == "zoom",
            UserIntegration.provider_email == zoom_email,
        )
    )
    integration = result.scalar_one_or_none()
    return integration.user_id if integration else None


async def post_summary_to_slack(channel: str, summary_text: str, action_items: list[str]) -> None:
    """Post meeting summary to a Slack channel."""
    if not settings.SLACK_BOT_TOKEN:
        logger.warning("slack.no_token — skipping post")
        return

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "📋 Meeting Summary"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": summary_text[:2900]}},
    ]
    if action_items:
        items_md = "\n".join(f"• {i}" for i in action_items)
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Items:*\n{items_md}"}}
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
            json={"channel": channel, "blocks": blocks},
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error("slack.post_failed", error=data.get("error"))


def _verify_slack_signature(request: Request, body: bytes) -> None:
    if not settings.SLACK_SIGNING_SECRET:
        return

    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")

    if abs(time.time() - int(ts or 0)) > 300:
        raise HTTPException(status_code=403, detail="Request too old")

    base = f"v0:{ts}:{body.decode()}"
    expected = (
        "v0="
        + hmac.new(
            settings.SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256
        ).hexdigest()
    )
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=403, detail="Invalid Slack signature")


def _enqueue_summarise(conversation_id: str) -> None:
    try:
        from app.tasks_proxy import summarize_session_task

        summarize_session_task.delay(conversation_id)
    except Exception as exc:
        logger.error("enqueue_summarise.failed", error=str(exc))
