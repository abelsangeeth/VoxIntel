"""Worker task unit tests — no real services required."""


def test_split_text_produces_chunks():
    from apps.worker.app.tasks.rag import _split_text

    long_text = "Hello world. " * 400
    chunks = _split_text(long_text)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert "text" in chunk
        assert "index" in chunk


def test_run_sentiment_stub():
    """Sentiment should return (label, score) without a GPU."""
    from apps.worker.app.tasks.analytics import _run_sentiment

    label, score = _run_sentiment("I love this product!")
    assert label in {"positive", "neutral", "negative"}
    assert 0.0 <= score <= 1.0
