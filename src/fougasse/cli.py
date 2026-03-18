"""Fougasse CLI — Administration and management commands."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table

from fougasse import __version__
from fougasse.config import load_config
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import count_memories, delete_memory, list_memories

console = Console()


def _get_db():
    """Get database connection from config."""
    config = load_config()
    config.ensure_dirs()
    return init_database(config.db_path)


@click.group()
@click.version_option(__version__, prog_name="fougasse")
def main() -> None:
    """Fougasse — Moteur de memoire persistante locale pour LLM."""
    pass


@main.command()
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON.")
def status(json_output: bool) -> None:
    """Show Fougasse server status and statistics."""
    config = load_config()
    db = _get_db()

    total = count_memories(db, include_archived=True)
    active = count_memories(db, include_archived=False)
    archived = total - active
    vault_count = db.execute("SELECT COUNT(*) FROM vaults").fetchone()[0]

    db_size = 0
    if config.db_path.exists():
        db_size = config.db_path.stat().st_size

    data = {
        "version": __version__,
        "db_path": str(config.db_path),
        "memory_count": total,
        "active_memories": active,
        "archived_memories": archived,
        "vault_count": vault_count,
        "db_size_bytes": db_size,
        "db_size_mb": round(db_size / (1024 * 1024), 2) if db_size > 0 else 0,
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        table = Table(title="Fougasse Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        for key, val in data.items():
            table.add_row(key, str(val))
        console.print(table)

    db.close()


@main.command()
@click.option("--hard", is_flag=True, help="Permanently delete (not just archive).")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON.")
@click.confirmation_option(prompt="Are you sure you want to prune archived memories?")
def prune(hard: bool, json_output: bool) -> None:
    """Remove archived memories."""
    db = _get_db()
    archived = list_memories(db, include_archived=True)
    archived_only = [m for m in archived if m.is_archived]

    count = 0
    for mem in archived_only:
        delete_memory(db, mem.id, hard=hard)
        count += 1

    result = {"pruned": count, "mode": "hard-delete" if hard else "soft-delete"}

    if json_output:
        click.echo(json.dumps(result))
    else:
        console.print(f"[green]Pruned {count} archived memories[/green] ({'hard' if hard else 'soft'})")

    db.close()


@main.command()
@click.option("--vault", default=None, help="Export only this vault.")
@click.option("--output", "-o", default=None, help="Output file path.")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON (default).")
def export(vault: str | None, output: str | None, json_output: bool) -> None:
    """Export memories to JSON."""
    db = _get_db()
    memories = list_memories(db, vault_id=vault, include_archived=True, limit=999999)

    data = {
        "version": __version__,
        "count": len(memories),
        "vault_filter": vault,
        "memories": [m.model_dump(mode="json") for m in memories],
    }

    json_str = json.dumps(data, indent=2, default=str)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(json_str)
        console.print(f"[green]Exported {len(memories)} memories to {output}[/green]")
    else:
        click.echo(json_str)

    db.close()


@main.command(name="import")
@click.argument("file", type=click.Path(exists=True))
def import_cmd(file: str) -> None:
    """Import memories from a JSON file."""
    from fougasse.models import MemoryCreate, MemoryType

    db = _get_db()

    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    imported = 0
    for mem_data in data.get("memories", []):
        try:
            create = MemoryCreate(
                content=mem_data["content"],
                type=MemoryType(mem_data.get("type", "text")),
                tags=mem_data.get("tags", []),
                vault_id=mem_data.get("vault_id", "default"),
                source_agent=mem_data.get("source_agent"),
                metadata=mem_data.get("metadata"),
            )
            from fougasse.storage.memory_store import insert_memory
            insert_memory(db, create)
            imported += 1
        except Exception as e:
            console.print(f"[yellow]Skipped: {e}[/yellow]")

    console.print(f"[green]Imported {imported} memories from {file}[/green]")
    db.close()


@main.command()
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON.")
def vaults(json_output: bool) -> None:
    """List all vaults."""
    db = _get_db()
    rows = db.execute("SELECT * FROM vaults ORDER BY created_at").fetchall()

    vault_list = []
    for row in rows:
        mc = count_memories(db, vault_id=row["id"])
        vault_list.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "memory_count": mc,
            "created_at": row["created_at"],
        })

    if json_output:
        click.echo(json.dumps(vault_list, indent=2))
    else:
        table = Table(title="Vaults")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Memories", style="yellow")
        table.add_column("Description")
        for v in vault_list:
            table.add_row(v["id"], v["name"], str(v["memory_count"]), v["description"] or "")
        console.print(table)

    db.close()


@main.command()
@click.option("--count", default=1000, help="Number of synthetic memories.")
@click.option("--queries", default=100, help="Number of test queries.")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON.")
def bench(count: int, queries: int, json_output: bool) -> None:
    """Run retrieval benchmark with synthetic data."""
    from fougasse.benchmarks.retrieval_bench import run_benchmark

    console.print(f"[cyan]Running benchmark: {count} memories, {queries} queries...[/cyan]")
    result = run_benchmark(count=count, queries=queries)

    if json_output:
        click.echo(json.dumps(result, indent=2))
    else:
        table = Table(title="Fougasse Benchmark")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        for key, val in result.items():
            table.add_row(key, str(val))
        console.print(table)


@main.command()
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON.")
def stats(json_output: bool) -> None:
    """Show detailed statistics."""
    db = _get_db()

    total = count_memories(db, include_archived=True)
    active = count_memories(db, include_archived=False)

    # By type
    type_rows = db.execute(
        "SELECT type, COUNT(*) as cnt FROM memories WHERE is_archived = 0 GROUP BY type"
    ).fetchall()
    by_type = {r["type"]: r["cnt"] for r in type_rows}

    # By vault
    vault_rows = db.execute(
        "SELECT vault_id, COUNT(*) as cnt FROM memories WHERE is_archived = 0 GROUP BY vault_id"
    ).fetchall()
    by_vault = {r["vault_id"]: r["cnt"] for r in vault_rows}

    # Graph stats
    node_count = db.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
    edge_count = db.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]

    # Top tags
    tag_rows = db.execute(
        "SELECT tag, COUNT(*) as cnt FROM tags GROUP BY tag ORDER BY cnt DESC LIMIT 10"
    ).fetchall()
    top_tags = {r["tag"]: r["cnt"] for r in tag_rows}

    data = {
        "total_memories": total,
        "active_memories": active,
        "archived_memories": total - active,
        "by_type": by_type,
        "by_vault": by_vault,
        "graph_nodes": node_count,
        "graph_edges": edge_count,
        "top_tags": top_tags,
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        table = Table(title="Fougasse Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total memories", str(total))
        table.add_row("Active", str(active))
        table.add_row("Archived", str(total - active))
        table.add_row("Graph nodes", str(node_count))
        table.add_row("Graph edges", str(edge_count))
        table.add_row("By type", json.dumps(by_type))
        table.add_row("By vault", json.dumps(by_vault))
        table.add_row("Top tags", json.dumps(top_tags))
        console.print(table)

    db.close()


if __name__ == "__main__":
    main()
