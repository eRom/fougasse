# Stack Technique — Fougasse

**Date** : 2026-03-17
**Statut** : Decide
**Contexte** : .specs/core/brainstorming.md

## Resume du besoin
Serveur MCP local + moteur de memoire persistante avec recherche hybride, graphe de connaissances et moteur de vitalite. Cross-platform, full local, 100K+ memoires, latence <50ms P50.

## Stacks considerees
| Stack | Priorise | Coute | Apprentissage |
|-------|----------|-------|---------------|
| **Python** | Ecosysteme ML/IA natif (sentence-transformers, NetworkX), MCP SDK mature (FastMCP), packaging pip universel | Performance brute vs Rust/Go | Faible (Romain connait) |
| **TypeScript** | Coherence avec Cruchot, ecosysteme npm | Ecosysteme ML/embeddings immature, ONNX plus complexe, NetworkX n'existe pas | Faible |
| **Rust** | Performance extreme (2.7ms latence), cross-compile natif | Temps de dev x3-5, ecosysteme MCP immature, graphe libraries limitees | Eleve |
| **Python + Rust core** | Le meilleur des deux mondes | Complexite de build, PyO3 bindings, CI/CD double | Eleve |

## Stack retenue
**Python**
L'ecosysteme ML/IA de Python est imbattable pour ce projet : sentence-transformers pour les embeddings, NetworkX pour le graphe, sqlite-vec/FTS5 pour la recherche hybride — tout tourne en local sans friction. Le SDK MCP Python (FastMCP) est la reference officielle. Et pip/uv rendent le cross-platform trivial. La performance de Python est largement suffisante : sqlite-vec fait 17ms sur 1M vecteurs, et le bottleneck sera l'embedding (~22ms), pas le code.

## Choix techniques concrets

### Couche MCP & API
| Brique | Choix | Alternative |
|--------|-------|-------------|
| Serveur MCP | `mcp` SDK Python (FastMCP) v1.12+ | mcp-server custom |
| Transport | stdio (principal) + SSE localhost (optionnel) | streamable-http |
| Serialisation | JSON (standard MCP) | MessagePack |

### Couche stockage
| Brique | Choix | Alternative |
|--------|-------|-------------|
| DB principale | SQLite 3.46+ avec FTS5 + WAL | PostgreSQL (trop lourd pour local) |
| Recherche vectorielle | sqlite-vec v0.1+ (extension C, zero deps) | ChromaDB (process separe), LanceDB |
| Recherche plein texte | SQLite FTS5 (BM25 natif) | Whoosh, tantivy |
| Fusion scores | RRF en SQL natif (JOIN FTS + vec) | WRRF custom en Python |
| ORM / Query builder | Aucun — SQL brut via `sqlite3` stdlib | SQLAlchemy, Peewee |
| Migrations | Scripts SQL versiones (`migrations/001_init.sql`) | Alembic |

### Couche embeddings & ML
| Brique | Choix | Alternative |
|--------|-------|-------------|
| Modele d'embedding | `sentence-transformers` avec `BGE-Base-v1.5` (110M params, 768 dims, 22.5ms/1K) | MiniLM-L6-v2 (plus rapide, moins precis), Nomic (plus precis, plus lent) |
| Runtime inference | PyTorch (CPU) via sentence-transformers | ONNX Runtime (plus rapide mais setup plus complexe) |
| Reranking (P1) | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cohere Rerank (cloud) |

### Couche graphe de connaissances
| Brique | Choix | Alternative |
|--------|-------|-------------|
| Graphe in-memory | NetworkX 3.x | igraph (plus rapide mais API moins intuitive) |
| Persistence graphe | Serialise dans SQLite (table edges + nodes) | GraphML fichier, Neo4j (trop lourd) |
| Communautes | Algorithme Leiden via `leidenalg` | Louvain via `community` |
| Centralite | PageRank (NetworkX natif) | Betweenness centrality |
| Points d'articulation | Tarjan (NetworkX natif) | — |

### Couche CLI
| Brique | Choix | Alternative |
|--------|-------|-------------|
| Framework CLI | Click 8.x | Typer (plus moderne mais dep Click), argparse |
| Output formatage | Rich (tables, progress, couleurs) | Textual (TUI complete — overkill) |

### Couche dev & qualite
| Brique | Choix | Alternative |
|--------|-------|-------------|
| Gestionnaire deps | uv (rapide, lockfile) | pip + pip-tools, poetry |
| Tests | pytest + pytest-cov | unittest |
| Linting | ruff (lint + format, ultra-rapide) | black + flake8 + isort |
| Types | mypy en mode strict | pyright |
| CI | GitHub Actions (matrix: macOS, Windows, Linux) | — |
| Packaging | PyPI via `hatch` + `hatchling` | setuptools, flit |

## Tooling concret
| Outil | Role | Installation |
|-------|------|-------------|
| uv | Gestionnaire de deps et venvs | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| ruff | Lint + format | `uv add --dev ruff` |
| pytest | Tests | `uv add --dev pytest pytest-cov` |
| mypy | Type checking | `uv add --dev mypy` |
| hatch | Build + publish PyPI | `uv add --dev hatch hatchling` |
| pre-commit | Hooks git | `uv add --dev pre-commit` |

## Ce qu'on ne fait PAS avec cette stack
- Pas de serveur web/API REST (MCP + CLI suffisent)
- Pas de frontend web (pas de React, pas de dashboard — hors scope core)
- Pas de base de donnees externe (pas de PostgreSQL, Redis, Neo4j)
- Pas de containerisation (pas de Docker — c'est une app locale)
- Pas de Rust/C natif (sqlite-vec est deja en C, le reste en Python pur)
- Pas d'ORM (SQL brut pour le controle et la performance)
- Pas de LangChain/LangGraph (overhead inutile pour un serveur MCP passif)
