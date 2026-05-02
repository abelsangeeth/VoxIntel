# Phase 5 — Integrations & Polish

**Weeks 17–20 | Status: 🔲 Not started**

## Goal
Plug into tools people already use; harden security; export meeting data.

## Tasks

### Zoom integration
- [ ] Register Zoom OAuth app; configure webhook for `meeting.started` / `meeting.ended`
- [ ] On `meeting.started`: create session, begin streaming audio via Zoom Bot SDK
- [ ] On `meeting.ended`: trigger `analytics.summarize_session`
- [ ] Verify Zoom webhook signature (`x-zm-signature` header)

### Slack bot
- [ ] Register Slack app with `chat:write` + `files:write` scopes
- [ ] After `SessionSummary` saved: post formatted summary to configured channel
- [ ] Slash command `/voxintel recap [session_id]` — fetch and post summary on demand

### Data export
- [ ] `GET /v1/sessions/{id}/export?format=csv|json|pdf`
- [ ] PDF: use `reportlab` or `weasyprint`; include speaker chart + action items
- [ ] Bulk export: `GET /v1/export?from=&to=` — ZIP of all sessions in date range

### Security hardening
- [ ] PII redaction: run `presidio-analyzer` on transcripts before storing; mask names, emails, phone numbers
- [ ] RBAC: `owner`, `member`, `viewer` roles per workspace; enforce in all session/document endpoints
- [ ] Security audit: OWASP ZAP scan against staging; fix all HIGH findings
- [ ] GDPR: `DELETE /v1/sessions/{id}` cascade-deletes all audio, transcripts, embeddings

### Fine-tuning
- [ ] Collect pilot feedback via thumbs up/down on RAG answers
- [ ] Fine-tune domain system prompts based on low-score answers
- [ ] A/B test `gpt-4o` vs `claude-3-5-sonnet` on legal + medical domains

## Done criteria
- Zoom meeting ends → Slack message in #meeting-summaries within 90 s
- PII redactor removes 100% of planted test names/emails from a transcript
- RBAC: `viewer` cannot POST or DELETE; returns 403
- PDF export opens in Adobe and contains all sections
