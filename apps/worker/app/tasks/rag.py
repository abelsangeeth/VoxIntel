"""
Phase 2 — RAG pipeline tasks.

Tasks:
  - ingest_document:  chunk → embed → upsert into Qdrant
  - rag_query:        embed query → top-K retrieval → LLM generation
"""

import asyncio
import uuid
from datetime import UTC, datetime

import structlog
from app.core.config import settings
from celery import shared_task

logger = structlog.get_logger(__name__)

CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 64
TOP_K = 5


@shared_task(
    name="rag.ingest_document",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
)
def ingest_document(self, document_id: str, raw_text: str) -> dict:
    """
    Chunk a document's text, embed each chunk, and upsert into Qdrant.

    Args:
        document_id:  UUID string of the Document row.
        raw_text:     Full extracted text of the document.
    """
    log = logger.bind(document_id=document_id)
    log.info("rag.ingest.start", chars=len(raw_text))

    try:
        chunks = _split_text(raw_text)
        embeddings = _embed_batch([c["text"] for c in chunks])
        _upsert_qdrant(document_id, chunks, embeddings)
        asyncio.run(_mark_document_processed(document_id, len(chunks)))
        log.info("rag.ingest.complete", chunk_count=len(chunks))
        return {"document_id": document_id, "chunk_count": len(chunks)}
    except Exception as exc:
        log.error("rag.ingest.failed", error=str(exc))
        raise self.retry(exc=exc)


@shared_task(name="rag.query", bind=True, max_retries=1, acks_late=True)
def rag_query(self, conversation_id: str, question: str) -> dict:
    """
    Answer a question grounded in retrieved document chunks.

    Returns a dict with keys: answer, sources
    """
    log = logger.bind(conversation_id=conversation_id)
    log.info("rag.query.start")

    try:
        query_embedding = _embed_batch([question])[0]
        hits = _search_qdrant(query_embedding, top_k=TOP_K)
        context = "\n\n".join(h["text"] for h in hits)
        answer = _generate(question, context)
        log.info("rag.query.complete", sources=len(hits))
        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": [h["document_id"] for h in hits],
        }
    except Exception as exc:
        log.error("rag.query.failed", error=str(exc))
        raise self.retry(exc=exc)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _split_text(text: str) -> list[dict]:
    """Split text into overlapping chunks using LangChain splitter."""
    try:
        import tiktoken
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        enc = tiktoken.encoding_for_model("gpt-4o")
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-4o",
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        texts = splitter.split_text(text)
        return [
            {"text": t, "token_count": len(enc.encode(t)), "index": i} for i, t in enumerate(texts)
        ]
    except ImportError:
        # Fallback: naive character split
        size = 1500
        return [
            {"text": text[i : i + size], "token_count": size // 4, "index": idx}
            for idx, i in enumerate(range(0, len(text), size - 300))
        ]


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using OpenAI embeddings."""
    try:
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception:
        # Stub: return zero vectors for offline dev
        logger.warning("embedding stub — returning zero vectors")
        return [[0.0] * 1536 for _ in texts]


def _upsert_qdrant(document_id: str, chunks: list[dict], embeddings: list[list[float]]) -> None:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)

    # Create collection if it doesn't exist
    existing = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embeddings[i],
            payload={
                "document_id": document_id,
                "chunk_index": chunk["index"],
                "text": chunk["text"],
                "token_count": chunk["token_count"],
            },
        )
        for i, chunk in enumerate(chunks)
    ]
    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)


def _search_qdrant(query_vector: list[float], top_k: int) -> list[dict]:
    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )
    return [{"text": r.payload["text"], "document_id": r.payload["document_id"]} for r in results]


def _generate(question: str, context: str) -> str:
    try:
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise domain assistant. "
                        "Answer ONLY based on the provided context. "
                        "If the answer is not in the context, say 'I don't have enough information.'"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.1,
            max_tokens=800,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("llm.stub", error=str(exc))
        return f"[LLM stub] Context retrieved: {len(context)} chars. Question: {question}"


async def _mark_document_processed(document_id: str, chunk_count: int) -> None:
    from app.db.models import Document  # mounted from apps/api/app/db
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as session:
        doc = await session.get(Document, uuid.UUID(document_id))
        if doc:
            doc.status = "processed"
            doc.chunk_count = chunk_count
            doc.processed_at = datetime.now(UTC)
        await session.commit()
    await engine.dispose()
