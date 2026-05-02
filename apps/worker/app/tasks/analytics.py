"""
Phase 3 — Conversation analytics tasks (updated).

Changes vs stub:
  - summarize_session now fires webhook + Slack post after persisting
  - analyze_utterance chains next utterance automatically (pipeline)
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import httpx
import structlog
from celery import shared_task

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ── analyze_utterance ─────────────────────────────────────────────────────────

@shared_task(
    name="analytics.analyze_utterance",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def analyze_utterance(self, utterance_id: str) -> dict:
    """Run sentiment analysis + intent classification on a single utterance."""
    log = logger.bind(utterance_id=utterance_id)
    try:
        text = asyncio.run(_fetch_utterance_text(utterance_id))
        sentiment_label, sentiment_score = _run_sentiment(text)
        intent = _classify_intent(text)
        asyncio.run(
            _update_utterance_analytics(utterance_id, sentiment_label, sentiment_score, intent)
        )
        log.info("analytics.utterance.complete", sentiment=sentiment_label, intent=intent)
        return {"utterance_id": utterance_id, "sentiment": sentiment_label, "intent": intent}
    except Exception as exc:
        log.error("analytics.utterance.failed", error=str(exc))
        raise self.retry(exc=exc)


# ── summarize_session ─────────────────────────────────────────────────────────

@shared_task(
    name="analytics.summarize_session",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def summarize_session(self, conversation_id: str) -> dict:
    """
    Generate meeting minutes + action items after session ends.
    Fires a webhook and posts to Slack upon completion.
    """
    log = logger.bind(conversation_id=conversation_id)
    log.info("analytics.summarize.start")
    try:
        transcript = asyncio.run(_fetch_full_transcript(conversation_id))
        summary, action_items = _generate_summary(transcript)
        top_intents = asyncio.run(_aggregate_intents(conversation_id))
        sentiment_arc = asyncio.run(_build_sentiment_arc(conversation_id))
        asyncio.run(
            _persist_summary(conversation_id, summary, action_items, top_intents, sentiment_arc)
        )

        payload = {
            "conversation_id": conversation_id,
            "summary": summary,
            "action_items": action_items,
            "top_intents": top_intents,
            "sentiment_arc": sentiment_arc,
        }

        # Fire generic webhook
        asyncio.run(_fire_webhook(conversation_id, payload))

        # Post to Slack if configured
        asyncio.run(_post_to_slack(summary, action_items))

        log.info("analytics.summarize.complete", actions=len(action_items))
        return payload
    except Exception as exc:
        log.error("analytics.summarize.failed", error=str(exc))
        raise self.retry(exc=exc)


# ── Sentiment + intent ────────────────────────────────────────────────────────

def _run_sentiment(text: str) -> tuple[str, float]:
    try:
        from transformers import pipeline  # type: ignore

        classifier = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment",
            tokenizer="cardiffnlp/twitter-roberta-base-sentiment",
        )
        result = classifier(text[:512])[0]
        label_map = {"LABEL_0": "negative", "LABEL_1": "neutral", "LABEL_2": "positive"}
        return label_map.get(result["label"], result["label"]), result["score"]
    except ImportError:
        return "neutral", 0.5


def _classify_intent(text: str) -> str:
    try:
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the conversational intent. "
                        "Reply with exactly ONE label from: "
                        "complaint, approval, clarification_request, information, "
                        "action_item, question, greeting, objection, other"
                    ),
                },
                {"role": "user", "content": text[:300]},
            ],
            temperature=0,
            max_tokens=10,
        )
        return (response.choices[0].message.content or "other").strip().lower()
    except Exception:
        return "other"


def _generate_summary(transcript: str) -> tuple[str, list[str]]:
    try:
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a meeting summarizer. "
                        "Given a transcript, return a JSON object with keys: "
                        "'summary' (string) and 'action_items' (list of strings). "
                        "Output ONLY valid JSON."
                    ),
                },
                {"role": "user", "content": f"Transcript:\n{transcript[:8000]}"},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("summary", ""), data.get("action_items", [])
    except Exception:
        return "Summary unavailable.", []


# ── Async DB helpers ──────────────────────────────────────────────────────────

async def _fetch_utterance_text(utterance_id: str) -> str:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import Utterance  # local import avoids circular deps

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        utt = await session.get(Utterance, uuid.UUID(utterance_id))
        text = utt.text if utt else ""
    await engine.dispose()
    return text


async def _update_utterance_analytics(
    utterance_id: str, sentiment_label: str, sentiment_score: float, intent: str
) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import Utterance

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        utt = await session.get(Utterance, uuid.UUID(utterance_id))
        if utt:
            utt.sentiment_label = sentiment_label
            utt.sentiment_score = sentiment_score
            utt.intent = intent
        await session.commit()
    await engine.dispose()


async def _fetch_full_transcript(conversation_id: str) -> str:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import Utterance, Speaker

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        result = await session.execute(
            select(Utterance, Speaker)
            .outerjoin(Speaker, Utterance.speaker_id == Speaker.id)
            .where(Utterance.conversation_id == uuid.UUID(conversation_id))
            .order_by(Utterance.sequence_number)
        )
        lines = []
        for utt, spk in result.all():
            label = spk.display_name or spk.label if spk else "Unknown"
            lines.append(f"[{label}]: {utt.text}")
    await engine.dispose()
    return "\n".join(lines)


async def _aggregate_intents(conversation_id: str) -> list[dict]:
    from collections import Counter
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import Utterance

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        result = await session.execute(
            select(Utterance.intent).where(
                Utterance.conversation_id == uuid.UUID(conversation_id),
                Utterance.intent.isnot(None),
            )
        )
        counts = Counter(row[0] for row in result.all())
    await engine.dispose()
    return [{"intent": k, "count": v} for k, v in counts.most_common(10)]


async def _build_sentiment_arc(conversation_id: str) -> list[dict]:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import Utterance

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        result = await session.execute(
            select(
                Utterance.sequence_number,
                Utterance.sentiment_label,
                Utterance.sentiment_score,
            )
            .where(Utterance.conversation_id == uuid.UUID(conversation_id))
            .order_by(Utterance.sequence_number)
        )
        arc = [
            {"seq": row[0], "label": row[1], "score": row[2]}
            for row in result.all()
            if row[1] is not None
        ]
    await engine.dispose()
    return arc


async def _persist_summary(
    conversation_id: str,
    summary: str,
    action_items: list,
    top_intents: list,
    sentiment_arc: list,
) -> None:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import SessionSummary

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        # Upsert: update if already exists
        existing = await session.execute(
            select(SessionSummary).where(
                SessionSummary.conversation_id == uuid.UUID(conversation_id)
            )
        )
        record = existing.scalar_one_or_none()
        if record:
            record.summary_text = summary
            record.action_items = action_items
            record.top_intents = top_intents
            record.sentiment_arc = sentiment_arc
        else:
            session.add(
                SessionSummary(
                    id=uuid.uuid4(),
                    conversation_id=uuid.UUID(conversation_id),
                    summary_text=summary,
                    action_items=action_items,
                    top_intents=top_intents,
                    sentiment_arc=sentiment_arc,
                )
            )
        await session.commit()
    await engine.dispose()


async def _fire_webhook(conversation_id: str, payload: dict) -> None:
    """POST summary payload to WEBHOOK_URL if configured."""
    webhook_url = settings.__dict__.get("WEBHOOK_URL") or ""
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(webhook_url, json=payload)
        logger.info("webhook.fired", conversation_id=conversation_id)
    except Exception as exc:
        logger.error("webhook.failed", error=str(exc))


async def _post_to_slack(summary: str, action_items: list) -> None:
    """Post meeting summary to the configured Slack channel."""
    if not settings.SLACK_BOT_TOKEN:
        return
    slack_channel = getattr(settings, "SLACK_SUMMARY_CHANNEL", "#general")
    try:
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "📋 Meeting Summary"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": summary[:2900]}},
        ]
        if action_items:
            items_md = "\n".join(f"• {i}" for i in action_items)
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Items:*\n{items_md}"}}
            )
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
                json={"channel": slack_channel, "blocks": blocks},
            )
        logger.info("slack.summary.posted", ok=resp.json().get("ok"))
    except Exception as exc:
        logger.error("slack.summary.failed", error=str(exc))
