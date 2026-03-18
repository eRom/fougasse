# Fougasse — Best Practices & Stack Guidelines

## Project Identity
- **Name**: Fougasse
- **Type**: MCP memory server + CLI (Python)
- **Language**: Code and CLI in English, docs/README in French
- **License**: Open-source (MIT or Apache-2.0)

## Python / uv
- Use `uv` for dependency management, not pip or poetry
- Python 3.11+ required (match sqlite-vec compatibility)
- Use `pyproject.toml` with hatchling build backend
- No `setup.py`, no `requirements.txt` — `uv.lock` is the lockfile
- Run commands via `uv run` (e.g., `uv run pytest`, `uv run fougasse`)
- Virtual env managed by uv automatically (`.venv/`)

## MCP SDK (FastMCP)
- Use `MCPServer` (not deprecated `FastMCP`) from `mcp.server.mcpserver` for new code
- Always use `async def` for tools — even if the body is synchronous
- Use `Context` parameter for logging: `await ctx.info()`, `await ctx.warning()`
- Use `lifespan` async context manager for DB connections (init on startup, cleanup on shutdown)
- Transport: stdio (default for Claude Code/Cursor) + SSE on localhost (optional)
- Tool names: `fougasse_remember`, `fougasse_recall`, `fougasse_forget`, `fougasse_explore`, `fougasse_status`, `fougasse_update`, `fougasse_vaults`
- Return JSON objects from tools, not plain strings
- Use Pydantic models for tool input validation (MCP SDK does this natively)

## SQLite
- Always enable WAL mode: `PRAGMA journal_mode=WAL`
- Always enable foreign keys: `PRAGMA foreign_keys=ON`
- Use `sqlite3` from stdlib — no ORM
- Parameterized queries ONLY — never string interpolation (SQL injection)
- Use `with db:` context manager for transactions (auto-commit/rollback)
- Migrations: numbered SQL files in `migrations/` dir, applied in order
- DB files: `~/.fougasse/memory.db` (main), `~/.fougasse/learning.db` (behavioral, GDPR-separated)
- sqlite-vec: load via `sqlite_vec.load(db)` after enabling extensions

## sqlite-vec
- Vectors stored as binary BLOBs via `struct.pack("%sf" % len(vector), *vector)`
- Use `vec0` virtual tables with `float[768]` for BGE-Base embeddings
- KNN search: `WHERE embedding MATCH ? ORDER BY distance LIMIT k`
- Metadata filtering: add auxiliary columns to vec0 table (genre, type, vault, etc.)
- RRF fusion: use SQL `FULL OUTER JOIN` between FTS5 and vec0 results with `1/(k+rank)` formula
- Never use `cosine` distance explicitly — sqlite-vec uses L2 by default, normalize vectors at insert time for cosine equivalence

## sentence-transformers (Embeddings)
- Model: `BAAI/bge-base-en-v1.5` (768 dims, ~110M params)
- Load once at startup via lifespan, reuse across requests
- Normalize embeddings at encoding time: `model.encode(text, normalize_embeddings=True)`
- Batch encoding when possible: `model.encode([text1, text2, ...])`
- Device: auto-detect (MPS on Mac, CPU on others) via `device="mps" if torch.backends.mps.is_available() else "cpu"`
- Cache the model in `~/.fougasse/models/` (avoid re-download)

## NetworkX (Knowledge Graph)
- Graph persisted in SQLite (edges table + nodes table), loaded into NetworkX at startup
- Use `nx.DiGraph()` (directed graph for `supersedes`, `relates_to`, `conflicts_with`)
- PageRank: `nx.pagerank(G)` — run periodically, cache results
- Tarjan articulation points: `nx.articulation_points(G.to_undirected())`
- Leiden communities: via `leidenalg` on `igraph` conversion (NetworkX -> igraph bridge)
- Keep graph in memory, sync to SQLite on writes (not on reads)

## Click (CLI)
- Entry point: `fougasse` command group
- Subcommands: `status`, `prune`, `export`, `import`, `vaults`, `stats`
- Use Rich for formatted output (tables, colors, progress bars)
- JSON output mode: `--json` flag for machine-readable output
- Config file: `~/.fougasse/config.toml`

## Testing
- pytest with `conftest.py` for shared fixtures (in-memory DB, test embeddings)
- Use `tmp_path` fixture for isolated DB files in tests
- Mock embeddings in unit tests (fixed vectors) — only integration tests use real model
- Target: >80% coverage on core modules (storage, retrieval, graph)
- Test matrix: macOS, Windows, Linux on GitHub Actions

## Code Style
- ruff for linting AND formatting (no black, no isort)
- mypy strict mode — no `Any` types in public APIs
- Docstrings: Google style (for the public API only)
- No classes where functions suffice — prefer functional style
- Async where IO-bound (DB, file), sync where CPU-bound (graph algorithms)

## File Structure Convention
```
src/fougasse/
  __init__.py
  server.py          # MCP server entry point
  cli.py             # Click CLI entry point
  storage/           # SQLite + sqlite-vec layer
  retrieval/         # Search, fusion, reranking
  graph/             # NetworkX knowledge graph
  vitality/          # Decay, consolidation engine
  models.py          # Pydantic data models
  config.py          # Configuration management
  embeddings.py      # Sentence-transformers wrapper
migrations/
  001_init.sql
tests/
```

## Security Rules
- NEVER expose network ports by default (stdio transport only)
- NEVER log memory content at INFO level (only at DEBUG)
- NEVER store API keys in config files (use env vars or OS keychain)
- Parameterized SQL queries ONLY
- Validate all MCP tool inputs via Pydantic
- Soft-delete by default, hard-delete requires explicit flag
- Provenance tracking on every write (source_agent, timestamp)

## Contexte projet (.memory)

Au demarrage de chaque session, lis ces fichiers pour charger le contexte du projet :
- .memory/architecture.md
- .memory/key-files.md
- .memory/patterns.md
- .memory/gotchas.md

Apres lecture, affiche un resume compact :
- Projet : [nom/type]
- Stack : [technos principales]
- Fichiers cles : [nombre]
- Gotchas : [nombre]
- Pret a travailler.
