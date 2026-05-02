"""Data export endpoint — Phase 5.

Supports exporting session data as:
  - JSON  (default)
  - CSV   (utterances table)
  - PDF   (formatted meeting minutes)
"""

import csv
import io
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models import Conversation, SessionSummary, Speaker, Utterance
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/{session_id}/export",
    summary="Export session data (JSON, CSV, or PDF)",
)
async def export_session(
    session_id: uuid.UUID,
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> Response:
    """
    Export meeting minutes, utterances, and analytics for a session.

    - **json**: Full structured payload (summary + utterances)
    - **csv**:  Flat spreadsheet of speaker-attributed utterances
    - **pdf**:  Formatted meeting minutes report
    """
    conv = await db.get(Conversation, session_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Fetch utterances with speaker names
    utt_result = await db.execute(
        select(Utterance, Speaker)
        .outerjoin(Speaker, Utterance.speaker_id == Speaker.id)
        .where(Utterance.conversation_id == session_id)
        .order_by(Utterance.sequence_number)
    )
    rows = utt_result.all()

    # Fetch summary if present
    sum_result = await db.execute(
        select(SessionSummary).where(SessionSummary.conversation_id == session_id)
    )
    summary = sum_result.scalar_one_or_none()

    if format == "json":
        return _export_json(conv, rows, summary)
    elif format == "csv":
        return _export_csv(conv, rows)
    else:
        return _export_pdf(conv, rows, summary)


# ── Formatters ────────────────────────────────────────────────────────────────


def _export_json(conv: Conversation, rows: list, summary) -> Response:
    import json

    payload = {
        "session_id": str(conv.id),
        "title": conv.title,
        "status": conv.status,
        "created_at": conv.created_at.isoformat(),
        "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
        "summary": {
            "text": summary.summary_text if summary else None,
            "action_items": summary.action_items if summary else [],
            "top_intents": summary.top_intents if summary else [],
            "sentiment_arc": summary.sentiment_arc if summary else [],
        },
        "utterances": [
            {
                "seq": utt.sequence_number,
                "speaker": spk.display_name or spk.label if spk else "Unknown",
                "start": utt.start_time,
                "end": utt.end_time,
                "text": utt.text,
                "sentiment": utt.sentiment_label,
                "intent": utt.intent,
            }
            for utt, spk in rows
        ],
    }
    return Response(
        content=json.dumps(payload, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="session_{conv.id}.json"'},
    )


def _export_csv(conv: Conversation, rows: list) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "sequence",
            "speaker",
            "start_s",
            "end_s",
            "text",
            "confidence",
            "language",
            "sentiment",
            "sentiment_score",
            "intent",
        ]
    )
    for utt, spk in rows:
        writer.writerow(
            [
                utt.sequence_number,
                spk.display_name or spk.label if spk else "Unknown",
                utt.start_time,
                utt.end_time,
                utt.text,
                utt.confidence,
                utt.language,
                utt.sentiment_label,
                utt.sentiment_score,
                utt.intent,
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="session_{conv.id}.csv"'},
    )


def _export_pdf(conv: Conversation, rows: list, summary) -> Response:
    """Generate a minimal PDF meeting-minutes report using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Meeting Minutes: {conv.title}", styles["Title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                f"Session ID: {conv.id} | Status: {conv.status} | "
                f"Date: {conv.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.5 * cm))

        # Summary
        if summary:
            story.append(Paragraph("Summary", styles["Heading2"]))
            story.append(Paragraph(summary.summary_text or "—", styles["Normal"]))
            story.append(Spacer(1, 0.3 * cm))

            if summary.action_items:
                story.append(Paragraph("Action Items", styles["Heading2"]))
                for item in summary.action_items:
                    story.append(Paragraph(f"• {item}", styles["Normal"]))
            story.append(Spacer(1, 0.5 * cm))

        # Transcript table
        if rows:
            story.append(Paragraph("Transcript", styles["Heading2"]))
            tdata = [["#", "Speaker", "Time", "Text"]]
            for utt, spk in rows[:200]:  # cap at 200 rows for PDF size
                tdata.append(
                    [
                        str(utt.sequence_number),
                        spk.display_name or spk.label if spk else "?",
                        f"{utt.start_time:.1f}s",
                        utt.text[:120],
                    ]
                )
            t = Table(tdata, colWidths=[1 * cm, 3 * cm, 2 * cm, 11 * cm])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightyellow]),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(t)

        doc.build(story)
        buf.seek(0)
        return Response(
            content=buf.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="session_{conv.id}.pdf"'},
        )
    except ImportError:
        # ReportLab not installed — return a plain-text fallback
        lines = [f"Meeting Minutes: {conv.title}\n"]
        if summary:
            lines.append(f"\nSUMMARY\n{summary.summary_text}\n")
            lines.append("\nACTION ITEMS\n" + "\n".join(f"- {i}" for i in summary.action_items))
        lines.append("\nTRANSCRIPT\n")
        for utt, spk in rows:
            label = spk.display_name or spk.label if spk else "Unknown"
            lines.append(f"[{label}] {utt.text}")
        return Response(
            content="\n".join(lines),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="session_{conv.id}.txt"'},
        )
