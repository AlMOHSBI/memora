# Memora source bundle

---
## src/memora/api.py

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .config import get_settings
from .db import Database
from .providers import build_summarizer, ProviderError
from .service import MemoryService


settings = get_settings()
db = Database(settings.database_path)
service: MemoryService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    db.initialize()
    service = MemoryService(db, build_summarizer(settings))
    yield


app = FastAPI(
    title="Memora API",
    version="0.1.0",
    description="Local-first persistent memory API for AI agents.",
    lifespan=lifespan,
)


def get_service() -> MemoryService:
    if service is None:
        raise HTTPException(503, "Memora is starting.")
    return service


class EventIn(BaseModel):
    agent: str = Field(min_length=1, max_length=100)
    project: str | None = None
    session_id: str | None = None
    content: str = Field(min_length=1, max_length=50000)
    event_type: str = "note"
    metadata: dict = Field(default_factory=dict)


class MemoryIn(BaseModel):
    content: str = Field(min_length=1, max_length=50000)
    project: str | None = None
    memory_type: str = "fact"
    importance: float = Field(default=0.5, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    source: str = "api"
    summary: str | None = None


class SessionIn(BaseModel):
    agent: str = "generic"
    project: str | None = None
    external_id: str | None = None
    title: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "memora", "version": "0.1.0"}


@app.post("/v1/sessions")
def create_session(body: SessionIn):
    svc = get_service()
    return {"session_id": svc.start_session(body.agent, body.project, body.external_id, body.title)}


@app.post("/v1/events")
def create_event(body: EventIn):
    svc = get_service()
    try:
        session_id = body.session_id or svc.start_session(body.agent, body.project)
        event_id = svc.add_event(session_id, body.content, body.event_type, body.metadata)
        return {"event_id": event_id, "session_id": session_id}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/v1/memories")
def create_memory(body: MemoryIn):
    try:
        memory_id = get_service().add_memory(
            body.content, body.project, body.memory_type, body.importance,
            body.tags, body.source, summary=body.summary
        )
        return {"memory_id": memory_id}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/v1/memories")
def list_memories(project: str | None = None,
                  limit: int = Query(default=100, ge=1, le=500)):
    return {"results": get_service().list_memories(project, limit)}


@app.patch("/v1/memories/{memory_id}")
def update_memory(memory_id: str, body: MemoryIn):
    try:
        updated = get_service().update_memory(
            memory_id, body.content, body.summary
        )
        if not updated:
            raise HTTPException(404, "Memory not found.")
        return {"updated": True, "memory_id": memory_id}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/v1/memories/search")
def search_memories(q: str = Query(min_length=1), project: str | None = None,
                    limit: int = Query(default=10, ge=1, le=100)):
    return {"results": get_service().search(q, project, limit)}


@app.get("/v1/context")
def get_context(project: str | None = None, q: str = "recent project decisions",
                limit: int = Query(default=8, ge=1, le=30)):
    return {"context": get_service().session_context(project, q, limit)}


@app.post("/v1/sessions/{session_id}/summarize")
async def summarize_session(session_id: str):
    try:
        memory_id, summary = await get_service().summarize_session(session_id)
        return {"memory_id": memory_id, "summary": summary}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(502, str(exc)) from exc
## src/memora/cli.py

from __future__ import annotations

import argparse
import asyncio
import json

from .config import get_settings
from .db import Database
from .providers import build_summarizer
from .service import MemoryService


def build_service() -> MemoryService:
    settings = get_settings()
    db = Database(settings.database_path)
    db.initialize()
    return MemoryService(db, build_summarizer(settings))


def main() -> None:
    parser = argparse.ArgumentParser(prog="memora", description="Memora local memory engine")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize local database")
    serve = sub.add_parser("serve", help="Start local HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    project = sub.add_parser("project", help="Manage projects")
    project_sub = project.add_subparsers(dest="action", required=True)
    project_create = project_sub.add_parser("create")
    project_create.add_argument("name")
    project_create.add_argument("--path")

    session = sub.add_parser("session", help="Manage sessions")
    session_sub = session.add_subparsers(dest="action", required=True)
    session_start = session_sub.add_parser("start")
    session_start.add_argument("--agent", default="manual")
    session_start.add_argument("--project")
    session_start.add_argument("--title")

    event = sub.add_parser("event", help="Record agent activity")
    event_sub = event.add_subparsers(dest="action", required=True)
    event_add = event_sub.add_parser("add")
    event_add.add_argument("--session", required=True)
    event_add.add_argument("--text", required=True)
    event_add.add_argument("--type", default="note")

    memory = sub.add_parser("memory", help="Manage memories")
    memory_sub = memory.add_subparsers(dest="action", required=True)
    memory_add = memory_sub.add_parser("add")
    memory_add.add_argument("--project")
    memory_add.add_argument("--text", required=True)
    memory_add.add_argument("--type", default="fact")
    memory_add.add_argument("--importance", type=float, default=0.5)

    search = sub.add_parser("search", help="Search saved memories")
    search.add_argument("query")
    search.add_argument("--project")
    search.add_argument("--limit", type=int, default=10)

    summarize = sub.add_parser("summarize", help="Summarize a session into memory")
    summarize.add_argument("--session", required=True)

    args = parser.parse_args()
    settings = get_settings()

    if args.command == "init":
        Database(settings.database_path).initialize()
        print(f"Memora database initialized: {settings.database_path}")
        return
    if args.command == "serve":
        import uvicorn
        uvicorn.run("memora.api:app", host=args.host, port=args.port, reload=False)
        return

    svc = build_service()
    if args.command == "project" and args.action == "create":
        print(svc.create_project(args.name, args.path))
    elif args.command == "session" and args.action == "start":
        print(svc.start_session(args.agent, args.project, title=args.title))
    elif args.command == "event" and args.action == "add":
        print(svc.add_event(args.session, args.text, args.type))
    elif args.command == "memory" and args.action == "add":
        print(svc.add_memory(args.text, args.project, args.type, args.importance))
    elif args.command == "search":
        print(json.dumps(svc.search(args.query, args.project, args.limit),
                         ensure_ascii=False, indent=2))
    elif args.command == "summarize":
        memory_id, summary = asyncio.run(svc.summarize_session(args.session))
        print(json.dumps({"memory_id": memory_id, "summary": summary},
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


## src/memora/config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_path: Path
    summarizer_provider: str
    summarizer_model: str
    openai_api_key: str | None
    anthropic_api_key: str | None


def get_settings() -> Settings:
    load_dotenv()
    data_dir = Path(os.getenv("MEMORA_DATA_DIR", Path.home() / ".memora"))
    data_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        database_path=data_dir / "memora.sqlite3",
        summarizer_provider=os.getenv("MEMORA_SUMMARIZER_PROVIDER", "none"),
        summarizer_model=os.getenv("MEMORA_SUMMARIZER_MODEL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
## src/memora/config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _expand(value: str) -> Path:
    return Path(value).expanduser().resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    ai_provider: str
    api_base_url: str
    api_key: str
    api_model: str
    ollama_base_url: str
    ollama_model: str
    allow_remote_ai: bool

    @property
    def database_path(self) -> Path:
        return self.data_dir / "memora.sqlite3"


def get_settings() -> Settings:
    return Settings(
        data_dir=_expand(os.getenv("MEMORA_DATA_DIR", "~/.memora")),
        ai_provider=os.getenv("MEMORA_AI_PROVIDER", "none").strip().lower(),
        api_base_url=os.getenv("MEMORA_API_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        api_key=os.getenv("MEMORA_API_KEY", ""),
        api_model=os.getenv("MEMORA_API_MODEL", ""),
        ollama_base_url=os.getenv("MEMORA_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("MEMORA_OLLAMA_MODEL", ""),
        allow_remote_ai=os.getenv("MEMORA_ALLOW_REMOTE_AI", "false").lower() == "true",
    )


## src/memora/connectors/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentEvent:
    agent: str
    content: str
    event_type: str = "note"
    project: str | None = None
    external_session_id: str | None = None
    metadata: dict[str, Any] | None = None


class AgentConnector(ABC):
    """Contract implemented by native agent integrations."""

    name: str
    capabilities: set[str] = set()

    @abstractmethod
    async def install(self) -> None:
        """Install or configure the integration with explicit user consent."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return whether the integration can communicate with its agent."""


## src/memora/connectors/__init__.py

# Empty package initializer.


## src/memora/db.py

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL DEFAULT 'generic',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    root_path TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    project_id TEXT REFERENCES projects(id),
    external_id TEXT,
    title TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    source_session_id TEXT REFERENCES sessions(id) ON DELETE SET NULL,
    memory_type TEXT NOT NULL DEFAULT 'fact',
    content TEXT NOT NULL,
    summary TEXT,
    importance REAL NOT NULL DEFAULT 0.5,
    tags_json TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)


## src/memora/mcp_server.py

from __future__ import annotations

from .config import get_settings
from .db import Database
from .providers import build_summarizer
from .service import MemoryService


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit('Install MCP support with: pip install -e ".[mcp]"') from exc

    settings = get_settings()
    db = Database(settings.database_path)
    db.initialize()
    service = MemoryService(db, build_summarizer(settings))
    mcp = FastMCP("Memora")

    @mcp.tool()
    def memory_search(query: str, project: str | None = None, limit: int = 8) -> list[dict]:
        """Search durable memories relevant to the supplied query."""
        return service.search(query, project, limit)

    @mcp.tool()
    def memory_save(content: str, project: str | None = None,
                    memory_type: str = "fact", importance: float = 0.6) -> str:
        """Save a durable fact, decision, constraint, or task as memory."""
        return service.add_memory(content, project, memory_type, importance, source="mcp")

    @mcp.tool()
    def session_context(query: str, project: str | None = None) -> str:
        """Retrieve concise context to help continue a project."""
        return service.session_context(project, query)

    mcp.run()


if __name__ == "__main__":
    main()