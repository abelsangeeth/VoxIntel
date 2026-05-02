# Phase 2 — Domain-Aware RAG Pipeline

**Weeks 6–9 | Status: 🔲 Not started**

## Goal
Build the retrieval → augmentation → generation loop grounded in a private knowledge base.

## Tasks
- [ ] Document ingestion: `POST /v1/documents` → `rag.ingest_document` task → Qdrant
- [ ] Text extraction: PDF (pypdf), DOCX (python-docx), plain text
- [ ] Chunking: `RecursiveCharacterTextSplitter` (512 tok, 64 overlap)
- [ ] Embedding: `text-embedding-3-small` → 1536-dim vectors
- [ ] Qdrant collection setup with cosine distance
- [ ] RAG query function: embed → top-5 search → inject context → GPT-4o
- [ ] Wire RAG into session: `POST /v1/sessions/{id}/query` endpoint
- [ ] Domain system prompt: configurable per-session (legal, medical, ops, etc.)
- [ ] Source citation in LLM responses (return `sources[]` array)

## Architecture
```
POST /documents  ──► rag.ingest_document
                         │  extract text
                         │  chunk (512 tok)
                         │  embed (OpenAI)
                         │  upsert Qdrant
                         ▼
                    Document status = "processed"

POST /sessions/{id}/query
        │
        ▼
  embed(question)  →  Qdrant top-5
        │                │
        │   context ◄────┘
        ▼
  GPT-4o (domain system prompt + context + question)
        │
        ▼
  { answer, sources[] }
```

## Done criteria
- Upload a PDF → `status: processed` within 30 s
- Ask "What does clause 4.2 say?" → cited, grounded answer from the document
- Hallucination test: question outside the docs → "I don't have enough information."

## Risks & mitigations
| Risk | Mitigation |
|------|-----------|
| OpenAI cost per embedding batch | Batch up to 2048 texts per API call; cache embeddings by SHA-256 |
| Qdrant OOM on large corpora | Use `on_disk_payload=True` in collection config |
| Prompt injection via document content | Sanitise doc text; use `role: system` context injection only |
