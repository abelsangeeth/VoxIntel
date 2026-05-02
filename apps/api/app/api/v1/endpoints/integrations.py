"""Integrations endpoints — Phase 5.

  POST /integrations/zoom/webhook   → Zoom App event receiver
  POST /integrations/slack/webhook  → Slack Events API receiver
"""

import hashlib
import hmac
import json
import time
import uuid

import httpx
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.db.models import Conversation

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Zoom webhook ──────────────────────────────────────────────────────────────

@router.post(
    "/zoom/webhook",
    status_code=status.HTTP_200_OK,
    summary="Zoom App event receiver",
)
async def zoom_webhook(
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Receives Zoom webhook events.

    Supported events:
      - meeting.started  → create a Conversation record
      - meeting.ended    → enqueue summarisation job

    Zoom validates the endpoint with a URL-validation challenge on first setup.
    """
    body = await request.body()

    # ── Zoom URL-validation challenge ─────────────────────────────────────
    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

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

    if event == "meeting.started":
        conv = Conversation(
            id=uuid.uuid4(),
            title=topic,
            source="zoom",
            external_id=meeting_id,
            status="active",
        )
        db.add(conv)
        await db.flush()
        logger.info("zoom.meeting.started", meeting_id=meeting_id, conv_id=str(conv.id))

    elif event == "meeting.ended":
        from sqlalchemy import select

        result = await db.execute(
            select(Conversation).where(Conversation.external_id == meeting_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            from datetime import datetime, timezone

            conv.status = "ended"
            conv.ended_at = datetime.now(timezone.utc)
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
    """
    Receives Slack Events API payloads.

    Handles:
      - url_verification challenge
      - app_mention events (future: slash-command RAG queries)
    """
    body = await request.body()
    _verify_slack_signature(request, body)

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Slack URL verification
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    event = payload.get("event", {})
    logger.info("slack.event.received", type=event.get("type"))

    return {"ok": True}


async def post_summary_to_slack(channel: str, summary_text: str, action_items: list[str]) -> None:
    """Post meeting summary to a Slack channel. Called after session ends."""
    if not settings.SLACK_BOT_TOKEN:
        logger.warning("slack.no_token — skipping post")
        return

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📋 Meeting Summary"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary_text[:2900]},
        },
    ]
    if action_items:
        items_md = "\n".join(f"• {i}" for i in action_items)
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Action Items:*\n{items_md}"},
            }
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


# ── Internal helpers ──────────────────────────────────────────────────────────

def _verify_slack_signature(request: Request, body: bytes) -> None:
    """Raise 403 if the Slack request signature is invalid."""
    if not settings.SLACK_SIGNING_SECRET:
        return  # skip in dev

    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")

    if abs(time.time() - int(ts or 0)) > 300:
        raise HTTPException(status_code=403, detail="Request too old")

    base = f"v0:{ts}:{body.decode()}"
    expected = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=403, detail="Invalid Slack signature")


def _enqueue_summarise(conversation_id: str) -> None:
    try:
        from app.tasks_proxy import summarize_session_task

        summarize_session_task.delay(conversation_id)
    except Exception as exc:
        logger.error("enqueue_summarise.failed", error=str(exc))
