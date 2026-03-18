"""Interactive graph visualization using pyvis."""

from __future__ import annotations

import sqlite3
import webbrowser
from pathlib import Path

from pyvis.network import Network

from fougasse.graph.persistence import load_graph

# Color palette
_COLORS = {
    "memory": {
        "text": "#4FC3F7",
        "code": "#81C784",
        "task": "#FFB74D",
        "appointment": "#E57373",
        "idea": "#BA68C8",
        "conversation": "#4DB6AC",
        "topic": "#FFD54F",
    },
    "entity": "#90A4AE",
    "edge": {
        "relates_to": "#546E7A",
        "supersedes": "#E53935",
        "conflicts_with": "#FF6F00",
        "tagged_with": "#37474F",
    },
}


def _get_memory_type(db: sqlite3.Connection, memory_id: str) -> str:
    """Get the type of a memory from DB."""
    row = db.execute("SELECT type FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return row["type"] if row else "text"


def _get_memory_preview(db: sqlite3.Connection, memory_id: str, max_len: int = 80) -> str:
    """Get a preview of memory content."""
    row = db.execute("SELECT content FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not row:
        return memory_id
    content = row["content"]
    return content[:max_len] + "..." if len(content) > max_len else content


def build_graph_html(
    db: sqlite3.Connection,
    output_path: Path,
    vault_id: str | None = None,
    height: str = "900px",
    width: str = "100%",
    bg_color: str = "#1a1a2e",
) -> Path:
    """Build an interactive HTML graph visualization.

    Returns the path to the generated HTML file.
    """
    kg = load_graph(db)

    if kg.node_count == 0:
        # Generate a minimal page
        output_path.write_text(
            "<html><body style='background:#1a1a2e;color:#eee;font-family:sans-serif;"
            "display:flex;align-items:center;justify-content:center;height:100vh'>"
            "<h1>Fougasse — Graphe vide</h1></body></html>",
            encoding="utf-8",
        )
        return output_path

    # Filter by vault if requested
    if vault_id:
        vault_memories = {
            r["id"]
            for r in db.execute(
                "SELECT id FROM memories WHERE vault_id = ?", (vault_id,)
            ).fetchall()
        }
    else:
        vault_memories = None

    # Build pyvis network
    net = Network(
        height=height,
        width=width,
        bgcolor=bg_color,
        font_color="#e0e0e0",
        directed=True,
        select_menu=False,
        filter_menu=False,
    )

    # Physics config for nice layout
    net.set_options("""
    {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.01,
                "springLength": 150,
                "springConstant": 0.02,
                "damping": 0.4
            },
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": true,
                "iterations": 200,
                "updateInterval": 25
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
        },
        "nodes": {
            "font": {
                "size": 12,
                "face": "Inter, system-ui, sans-serif"
            },
            "borderWidth": 2,
            "shadow": true
        },
        "edges": {
            "smooth": {
                "type": "continuous",
                "forceDirection": "none"
            },
            "arrows": {
                "to": {"enabled": true, "scaleFactor": 0.5}
            },
            "font": {
                "size": 9,
                "color": "#78909C",
                "face": "Inter, system-ui, sans-serif"
            }
        }
    }
    """)

    # Add nodes
    for node_id, attrs in kg.graph.nodes(data=True):
        node_type = attrs.get("node_type", "memory")
        label = attrs.get("label", node_id)
        pagerank = attrs.get("pagerank", 0.0)
        community_id = attrs.get("community_id")

        # Skip if vault filter and not in vault
        if node_type == "memory" and vault_memories is not None and node_id not in vault_memories:
            continue

        if node_type == "memory":
            mem_type = _get_memory_type(db, node_id)
            color = _COLORS["memory"].get(mem_type, "#4FC3F7")
            preview = _get_memory_preview(db, node_id)
            size = 15 + pagerank * 500  # Scale by PageRank
            shape = "dot"
            title = (
                f"<b>{label[:60]}</b><br>"
                f"<i>Type:</i> {mem_type}<br>"
                f"<i>PageRank:</i> {pagerank:.4f}<br>"
                f"<i>Community:</i> {community_id}<br>"
                f"<hr>{preview}"
            )
            display_label = label[:30] + "..." if len(label) > 30 else label
        else:
            # Entity node (tag)
            color = _COLORS["entity"]
            size = 10
            shape = "diamond"
            tag_name = label if not node_id.startswith("tag:") else node_id[4:]
            title = f"<b>Tag: {tag_name}</b>"
            display_label = tag_name

        net.add_node(
            node_id,
            label=display_label,
            title=title,
            color=color,
            size=size,
            shape=shape,
            borderWidthSelected=3,
        )

    # Add edges
    added_nodes = {n["id"] for n in net.nodes}
    for source, target, attrs in kg.graph.edges(data=True):
        if source not in added_nodes or target not in added_nodes:
            continue

        relation = attrs.get("relation", "relates_to")
        weight = attrs.get("weight", 1.0)
        color = _COLORS["edge"].get(relation, "#546E7A")

        # Thicker edges for stronger relations
        edge_width = 1 + weight * 2

        # Dashes for tagged_with (less important visually)
        dashes = relation == "tagged_with"

        net.add_edge(
            source,
            target,
            title=f"{relation} (w={weight:.2f})",
            color=color,
            width=edge_width,
            dashes=dashes,
            label="" if relation == "tagged_with" else relation,
        )

    # Inject custom header
    net.html = None  # Reset
    net.save_graph(str(output_path))

    # Post-process: fullscreen + branding
    html = output_path.read_text(encoding="utf-8")

    # Force fullscreen: replace pyvis default 900px height + strip margins
    import re

    # Replace pyvis CSS block height: 900px → 100vh
    html = re.sub(
        r"(#mynetwork\s*\{[^}]*?)height:\s*\d+px",
        r"\1height: 100vh",
        html,
        flags=re.DOTALL,
    )
    # Replace pyvis CSS width: 100% → 100vw
    html = re.sub(
        r"(#mynetwork\s*\{[^}]*?)width:\s*100%",
        r"\1width: 100vw",
        html,
        flags=re.DOTALL,
    )
    # Remove border on #mynetwork
    html = re.sub(
        r"(#mynetwork\s*\{[^}]*?)border:\s*1px solid lightgray;",
        r"\1border: none;",
        html,
        flags=re.DOTALL,
    )
    # Replace inline style on div if present
    html = re.sub(
        r'(<div\s+id\s*=\s*"mynetwork"\s+style\s*=\s*")[^"]*(")',
        r"\1width:100vw;height:100vh;\2",
        html,
    )
    # Strip bootstrap card padding + center headers
    html = html.replace("<center>", "").replace("</center>", "")
    html = re.sub(r"<h1>\s*</h1>", "", html)

    fullscreen_css = """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { overflow: hidden; width: 100vw; height: 100vh; background: #1a1a2e; }
        .card { border: none !important; background: none !important; }
        .card-body { padding: 0 !important; }
    </style>
    """
    html = html.replace("</head>", fullscreen_css + "</head>")

    branding = """
    <div style="position:fixed;top:10px;left:10px;z-index:9999;
                background:rgba(26,26,46,0.9);padding:12px 20px;
                border-radius:8px;border:1px solid #333;
                font-family:Inter,system-ui,sans-serif;color:#e0e0e0">
        <strong style="font-size:16px">Fougasse</strong>
        <span style="color:#78909C;margin-left:8px;font-size:12px">Knowledge Graph</span>
    </div>
    <div style="position:fixed;bottom:10px;left:10px;z-index:9999;
                background:rgba(26,26,46,0.9);padding:8px 14px;
                border-radius:6px;border:1px solid #333;
                font-family:Inter,system-ui,sans-serif;color:#78909C;font-size:11px">
        <span style="color:#4FC3F7">&#9679;</span> Memory &nbsp;
        <span style="color:#90A4AE">&#9670;</span> Tag &nbsp;
        | &nbsp;
        <span style="color:#546E7A">&#8212;</span> relates_to &nbsp;
        <span style="color:#E53935">&#8212;</span> supersedes &nbsp;
        <span style="color:#FF6F00">&#8212;</span> conflicts_with
    </div>
    """
    html = html.replace("</body>", branding + "</body>")
    output_path.write_text(html, encoding="utf-8")

    return output_path


def open_graph(
    db: sqlite3.Connection,
    output_path: Path | None = None,
    vault_id: str | None = None,
    open_browser: bool = True,
) -> Path:
    """Build and optionally open the graph visualization."""
    if output_path is None:
        output_path = Path.home() / ".fougasse" / "graph.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_graph_html(db, output_path, vault_id=vault_id)

    if open_browser:
        webbrowser.open(f"file://{output_path.resolve()}")

    return output_path
