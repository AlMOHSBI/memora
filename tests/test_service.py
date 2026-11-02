from pathlib import Path

import pytest

from memora.db import Database
from memora.providers import LocalExtractiveSummarizer
from memora.service import MemoryService


@pytest.fixture
def service(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    db.initialize()
    return MemoryService(db, LocalExtractiveSummarizer())


def test_create_and_search_memory(service):
    memory_id = service.add_memory(
        "The project backend uses FastAPI and SQLite.",
        project="demo",
        memory_type="decision",
        importance=0.9,
        tags=["backend", "database"],
    )
    results = service.search("FastAPI backend", project="demo")
    assert results
    assert results[0]["id"] == memory_id


def test_event_and_summarize_session(service):
    import asyncio
    session_id = service.start_session("test-agent", "demo")
    service.add_event(session_id, "Implemented the health endpoint.")
    memory_id, summary = asyncio.run(service.summarize_session(session_id))
    assert memory_id.startswith("mem_")
    assert "health endpoint" in summary
