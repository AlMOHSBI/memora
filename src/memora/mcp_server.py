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
