# Connecting MCP-capable agents

Memora exposes three MCP tools when installed with the `mcp` extra:

- `memory_search(query, project?, limit?)`
- `memory_save(content, project?, memory_type?, importance?)`
- `session_context(query, project?)`

Install Memora in a Python environment and ensure the `memora-mcp` executable is on PATH:

```bash
pip install -e ".[mcp]"
```

The generic MCP stdio server command is:

```bash
memora-mcp
```

Configure your agent's MCP client to launch that command. Exact configuration-file names and
JSON schemas differ by agent/version; follow that agent's current MCP documentation rather than
copying a config intended for a different client. The server uses the same local SQLite database
as the Memora CLI/API.

For an isolated virtual environment, configure the MCP client to launch the absolute path to the
virtual environment's executable (`.venv/bin/memora-mcp` on macOS/Linux or
`.venv\\Scripts\\memora-mcp.exe` on Windows).
