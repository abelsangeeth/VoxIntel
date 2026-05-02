# Phase 3 — Conversation Analytics

**Weeks 10–12 | Status: 🔲 Not started**

## Goal
Layer business intelligence on the transcript stream — sentiment, intent, summaries, trends.

## Tasks
- [ ] Sentiment: run `cardiffnlp/twitter-roberta-base-sentiment` per utterance in worker; store `sentiment_label` + `sentiment_score`
- [ ] Intent classification: GPT-4o-mini one-shot prompt → store `intent` on Utterance
- [ ] Auto-summarization: `analytics.summarize_session` kicks off when `Conversation.status` → `ended`; writes `SessionSummary` row
- [ ] Webhook: after summary saved, POST JSON payload to `Conversation.metadata.webhook_url` if set
- [ ] Trend endpoint: `GET /v1/analytics/topics?from=&to=` — keyword freq + BERTopic clustering across sessions
- [ ] Speaker sentiment arc endpoint: `GET /v1/sessions/{id}/analytics`

## Webhook payload schema
```json
{
  "conversation_id": "uuid",
  "summary": "string",
  "action_items": ["string"],
  "top_intents": [{"intent": "string", "count": int}],
  "sentiment_arc": [{"seq": int, "label": "string", "score": float}]
}
```

## Done criteria
- Session ends → webhook fires within 60 s with valid JSON payload
- `sentiment_arc` shows measurable variation across a 10-min meeting
- BERTopic surfaces ≥3 coherent topics across 5 test sessions

## Risks & mitigations
| Risk | Mitigation |
|------|-----------|
| Sentiment model GPU memory | Run as separate worker queue; use `int8` quantisation |
| LLM cost per utterance (intent) | Batch intents; use `gpt-4o-mini` not `gpt-4o` |
| Webhook delivery failure | Store `webhook_sent=false`; retry with exponential backoff |
