"""Fougasse MCP Server — Memory tools for LLM clients."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

from fougasse import __version__
from fougasse.config import FougasseConfig, load_config
from fougasse.embeddings import encode, load_model
from fougasse.models import (
    FougasseStatus,
    MemoryCreate,
    MemoryType,
    SearchQuery,
)
from fougasse.retrieval.hybrid_search import hybrid_search
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import (
    count_memories,
    delete_memory,
    insert_memory,
)
from fougasse.storage.vector_store import delete_vector, ensure_vec_table, insert_vector


@dataclass
class AppContext:
    """Application context with database and config."""

    db: sqlite3.Connection
    config: FougasseConfig
    start_time: float


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize database and embedding model on startup."""
    config = load_config()
    config.ensure_dirs()

    # Initialize database
    db = init_database(config.db_path)
    ensure_vec_table(db, dim=config.embedding_dim)

    # Pre-load embedding model
    load_model(config.model_name, cache_dir=config.models_dir)

    start_time = time.time()

    try:
        yield AppContext(db=db, config=config, start_time=start_time)
    finally:
        db.close()


mcp = FastMCP(
    "Fougasse",
    instructions="Fougasse is a persistent local memory engine. Use fougasse_remember to store information, fougasse_recall to retrieve it, fougasse_forget to delete, and fougasse_status to check health.",
    lifespan=app_lifespan,
)


@mcp.tool()
async def fougasse_remember(
    content: str,
    type: str = "text",
    tags: list[str] | None = None,
    vault_id: str = "default",
    source_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store a new memory in Fougasse.

    Args:
        content: The text content to memorize (max 100KB).
        type: Memory type - one of: text, code, task, appointment, idea, conversation, topic.
        tags: Optional list of tags for categorization.
        vault_id: Vault namespace (default: "default").
        source_agent: Identifier of the calling agent/client.
        metadata: Optional key-value metadata.

    Returns:
        The created memory with its ID and status.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    try:
        mem_type = MemoryType(type)
    except ValueError:
        return {"error": f"Invalid type '{type}'. Valid: {[t.value for t in MemoryType]}"}

    data = MemoryCreate(
        content=content,
        type=mem_type,
        tags=tags or [],
        vault_id=vault_id,
        source_agent=source_agent,
        metadata=metadata,
    )

    # Insert memory
    mem = insert_memory(app.db, data)

    # Generate and store embedding
    embedding = encode(content)
    insert_vector(app.db, mem.id, vault_id, embedding)

    return {
        "status": "stored",
        "id": mem.id,
        "type": mem.type.value,
        "vault_id": mem.vault_id,
        "tags": mem.tags,
        "created_at": mem.created_at.isoformat() if hasattr(mem.created_at, 'isoformat') else str(mem.created_at),
    }


@mcp.tool()
async def fougasse_recall(
    query: str,
    vault_id: str | None = None,
    type_filter: str | None = None,
    tags_filter: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search and retrieve relevant memories.

    Args:
        query: Natural language search query.
        vault_id: Optional vault to search in (default: all vaults).
        type_filter: Optional type filter (text, code, task, etc.).
        tags_filter: Optional tags to filter by.
        limit: Maximum number of results (default: 10).

    Returns:
        List of matching memories with relevance scores.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    tf = None
    if type_filter:
        try:
            tf = MemoryType(type_filter)
        except ValueError:
            return {"error": f"Invalid type_filter '{type_filter}'."}

    search_query = SearchQuery(
        query=query,
        vault_id=vault_id,
        type_filter=tf,
        tags_filter=tags_filter,
        limit=limit,
    )

    result = hybrid_search(app.db, search_query)

    return {
        "results": [
            {
                "id": r.memory.id,
                "content": r.memory.content,
                "type": r.memory.type.value,
                "tags": r.memory.tags,
                "vault_id": r.memory.vault_id,
                "source_agent": r.memory.source_agent,
                "score": round(r.score, 4),
                "match_sources": r.match_sources,
                "created_at": str(r.memory.created_at),
            }
            for r in result.results
        ],
        "total_count": result.total_count,
        "search_time_ms": result.search_time_ms,
    }


@mcp.tool()
async def fougasse_forget(
    memory_id: str,
    hard: bool = False,
) -> dict[str, Any]:
    """Delete a memory.

    Args:
        memory_id: The ID of the memory to delete.
        hard: If True, permanently delete. If False (default), archive (soft-delete).

    Returns:
        Deletion status.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    success = delete_memory(app.db, memory_id, hard=hard)
    if not success:
        return {"error": f"Memory '{memory_id}' not found."}

    if hard:
        delete_vector(app.db, memory_id)

    return {
        "status": "deleted" if hard else "archived",
        "memory_id": memory_id,
    }


@mcp.tool()
async def fougasse_status() -> dict[str, Any]:
    """Get Fougasse server status and statistics.

    Returns:
        Server health, memory counts, and database info.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    total = count_memories(app.db, include_archived=True)
    active = count_memories(app.db, include_archived=False)
    archived = total - active

    # DB size
    db_size = 0
    if app.config.db_path.exists():
        db_size = app.config.db_path.stat().st_size

    vault_count = app.db.execute("SELECT COUNT(*) FROM vaults").fetchone()[0]

    return FougasseStatus(
        version=__version__,
        memory_count=total,
        vault_count=vault_count,
        active_memories=active,
        archived_memories=archived,
        db_size_bytes=db_size,
        uptime_seconds=round(time.time() - app.start_time, 1),
    ).model_dump()


@mcp.tool()
async def fougasse_vaults(
    action: str = "list",
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Manage memory vaults (namespaces).

    Args:
        action: One of "list", "create", "delete".
        name: Vault name (required for create/delete).
        description: Optional description (for create).

    Returns:
        Vault operation result.
    """
    ctx = mcp.get_context()
    app: AppContext = ctx.request_context.lifespan_context

    if action == "list":
        rows = app.db.execute("SELECT * FROM vaults ORDER BY created_at").fetchall()
        vaults = []
        for row in rows:
            mc = count_memories(app.db, vault_id=row["id"])
            vaults.append({
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "memory_count": mc,
                "created_at": row["created_at"],
            })
        return {"vaults": vaults}

    if action == "create":
        if not name:
            return {"error": "name is required for create action."}
        vault_id = name.lower().replace(" ", "-")
        try:
            with app.db:
                app.db.execute(
                    "INSERT INTO vaults (id, name, description) VALUES (?, ?, ?)",
                    (vault_id, name, description),
                )
        except sqlite3.IntegrityError:
            return {"error": f"Vault '{name}' already exists."}
        return {"status": "created", "vault_id": vault_id, "name": name}

    if action == "delete":
        if not name:
            return {"error": "name is required for delete action."}
        if name == "default":
            return {"error": "Cannot delete the default vault."}
        mc = count_memories(app.db, vault_id=name)
        if mc > 0:
            return {"error": f"Vault '{name}' has {mc} memories. Delete them first or use force."}
        with app.db:
            app.db.execute("DELETE FROM vaults WHERE id = ? OR name = ?", (name, name))
        return {"status": "deleted", "name": name}

    return {"error": f"Unknown action '{action}'. Use: list, create, delete."}


def run_server() -> None:
    """Run the Fougasse MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
