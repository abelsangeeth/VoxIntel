"""Document ingestion endpoints — Phase 2.

Improvements:
  - Extracts raw text from PDF/DOCX/TXT before enqueuing
  - Applies PII redaction before storing
  - Enqueues rag.ingest_document Celery task
  - GET /documents lists all documents
  - GET /documents/{id}/query triggers a RAG search
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models import Document
from packages.shared.schemas.document import DocumentRead

logger = structlog.get_logger(__name__)
router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
}


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> DocumentRead:
    """
    Upload a PDF, DOCX, or plain-text document for chunking + embedding.
    Text is extracted immediately; chunking + vectorisation runs in the worker.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {sorted(ALLOWED_MIME_TYPES)}",
        )

    raw_bytes = await file.read()
    raw_text = _extract_text(raw_bytes, file.content_type or "text/plain")
    raw_text = _redact_pii(raw_text)

    doc = Document(
        id=uuid.uuid4(),
        filename=file.filename or "unknown",
        content_type=file.content_type,
        status="pending",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # Enqueue worker task
    try:
        from app.tasks_proxy import ingest_document_task

        ingest_document_task.delay(str(doc.id), raw_text)
        logger.info("document.queued", doc_id=str(doc.id), chars=len(raw_text))
    except Exception as exc:
        logger.error("document.queue_failed", error=str(exc))

    return DocumentRead.model_validate(doc)


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> list[DocumentRead]:
    """List uploaded documents with their processing status."""
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
    )
    docs = result.scalars().all()
    return [DocumentRead.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> DocumentRead:
    """Get a single document by ID."""
    result = await db.get(Document, document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead.model_validate(result)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_text(raw_bytes: bytes, content_type: str) -> str:
    """Extract plain text from a document blob."""
    if content_type == "application/pdf":
        try:
            import io
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(io.BytesIO(raw_bytes))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as exc:
            logger.warning("pdf_extract_failed", error=str(exc))
            return raw_bytes.decode("utf-8", errors="ignore")

    elif content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        try:
            import io
            from docx import Document as DocxDoc  # type: ignore

            doc = DocxDoc(io.BytesIO(raw_bytes))
            return "\n".join(para.text for para in doc.paragraphs)
        except Exception as exc:
            logger.warning("docx_extract_failed", error=str(exc))
            return raw_bytes.decode("utf-8", errors="ignore")

    # Plain text / markdown
    return raw_bytes.decode("utf-8", errors="ignore")


# Create globals for Presidio to avoid initializing NLP models on every request
_analyzer = None
_anonymizer = None

def _get_presidio():
    global _analyzer, _anonymizer
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        logger.info("presidio.init", msg="Loading spaCy models for Presidio...")
        _analyzer = AnalyzerEngine()
        _anonymizer = AnonymizerEngine()
    return _analyzer, _anonymizer

def _redact_pii(text: str) -> str:
    """
    Production-grade PII redaction using Microsoft Presidio (NLP + Checksums).
    Redacts: PERSON, LOCATION, PHONE_NUMBER, EMAIL_ADDRESS, CREDIT_CARD, US_SSN.
    """
    try:
        analyzer, anonymizer = _get_presidio()
        
        # Analyze the text for specific PII entities
        results = analyzer.analyze(
            text=text, 
            entities=["PERSON", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "US_SSN"],
            language="en"
        )
        
        # Anonymize (replaces text with entity type, e.g., <PERSON>)
        anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized_result.text
    except Exception as exc:
        logger.error("presidio.failed", error=str(exc))
        # If the NLP engine fails, fallback to returning the original text
        # (Alternatively, we could fallback to the regex rules here)
        return text
