"""Initial schema — conversations, speakers, utterances, documents.

Revision ID: 001
Revises:
Create Date: 2026-04-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── conversations ─────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="upload"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="created"),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_conversations_external_id", "conversations", ["external_id"])

    # ── speakers ──────────────────────────────────────────────────────────
    op.create_table(
        "speakers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("voice_embedding", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("conversation_id", "label", name="uq_speakers_conv_label"),
    )
    op.create_index("ix_speakers_conversation_id", "speakers", ["conversation_id"])

    # ── utterances ────────────────────────────────────────────────────────
    op.create_table(
        "utterances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "speaker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("speakers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Float, nullable=False),
        sa.Column("end_time", sa.Float, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("sentiment_label", sa.String(20), nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("intent", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_utterances_conversation_id", "utterances", ["conversation_id"])
    op.create_index("ix_utterances_speaker_id", "utterances", ["speaker_id"])
    op.create_index(
        "ix_utterances_conversation_seq",
        "utterances",
        ["conversation_id", "sequence_number"],
    )

    # ── documents ─────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("tags", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("chunk_count", sa.Integer, nullable=True),
        sa.Column("token_count", sa.BigInteger, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── document_chunks ───────────────────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("qdrant_point_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])

    # ── session_summaries ─────────────────────────────────────────────────
    op.create_table(
        "session_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary_text", sa.Text, nullable=False),
        sa.Column("action_items", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("top_intents", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("sentiment_arc", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("webhook_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_session_summaries_conversation_id", "session_summaries", ["conversation_id"]
    )


def downgrade() -> None:
    op.drop_table("session_summaries")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("utterances")
    op.drop_table("speakers")
    op.drop_table("conversations")
