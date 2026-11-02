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
