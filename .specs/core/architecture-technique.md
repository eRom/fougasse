# Architecture Technique — core

**Date** : 2026-03-17
**Statut** : Decide
**Contexte** : brainstorming.md, architecture-fonctionnelle.md, stack-technique.md

## Probleme architectural
Concevoir un moteur de memoire persistante locale qui stocke 100K+ souvenirs heterogenes (texte, code, taches, idees), les relie dans un graphe de connaissances dynamique, et les restitue en <50ms via un serveur MCP. Le tout sans serveur externe, sans cloud, cross-platform, dans un seul processus Python.

## Flux principal

```
[LLM Client]                                [Fougasse MCP Server]
     |                                              |
     |-- tool_call(fougasse_remember) ------------->|
     |                                              |-- validate input (Pydantic)
     |                                              |-- generate embedding (BGE-Base)
     |                                              |-- store in SQLite + sqlite-vec
     |                                              |-- update FTS5 index
     |                                              |-- update knowledge graph (NetworkX)
     |                                              |-- check contradictions
     |                                              |-- return {id, status, warnings}
     |<---------------------------------------------|
     |
     |-- tool_call(fougasse_recall) --------------->|
     |                                              |-- embed query (BGE-Base)
     |                                              |-- parallel: vec KNN + FTS5 BM25
     |                                              |-- parallel: graph traversal + temporal
     |                                              |-- RRF fusion (SQL)
     |                                              |-- optional: cross-encoder rerank
     |                                              |-- boost vitality scores
     |                                              |-- return {memories[], scores[]}
     |<---------------------------------------------|
```

## Decisions architecturales

### Decision 1 : Monolithe single-process
**Probleme** : Fougasse a besoin de SQLite, sqlite-vec, NetworkX, sentence-transformers dans le meme processus.
**Options** :
  - Option A : Single process Python avec tout en memoire → simple, rapide, un seul fichier de config
  - Option B : Multi-process (serveur embeddings separe, serveur graphe separe) → scalable, isole les crashes
**Choix** : Option A — single process
**Raison** : C'est une app locale single-user. La complexite multi-process n'apporte rien. SQLite est mono-writer de toute facon. Le graphe NetworkX en memoire est ultra-rapide. Les embeddings via sentence-transformers sont thread-safe.

### Decision 2 : SQLite comme source de verite unique
**Probleme** : On a des memoires, des vecteurs, un graphe, des metadonnees. Ou stocker quoi ?
**Options** :
  - Option A : Tout dans SQLite (memoires + vecteurs via sqlite-vec + graphe serialise + FTS5) → un seul fichier, backup trivial
  - Option B : SQLite pour metadonnees + ChromaDB pour vecteurs + fichiers pour graphe → separation des concerns
**Choix** : Option A — tout dans SQLite
**Raison** : sqlite-vec + FTS5 + tables relationnelles dans un seul fichier .db. Le backup c'est `cp memory.db memory.db.bak`. La migration c'est un script SQL. Cross-platform garanti. ChromaDB ajouterait un process separe et une dependance lourde.

### Decision 3 : Graphe en memoire + sync SQLite
**Probleme** : NetworkX est in-memory. Comment persister le graphe ?
**Options** :
  - Option A : Graphe serialise en SQLite (tables `graph_nodes`, `graph_edges`), charge au demarrage, sync sur ecriture
  - Option B : Export GraphML periodique dans un fichier
  - Option C : Neo4j embarque
**Choix** : Option A — SQLite persistence
**Raison** : Coherent avec la decision 2 (SQLite unique). Le graphe 100K noeuds + ~500K aretes charge en ~200ms dans NetworkX. Les ecritures sont peu frequentes (une memoire = 1-5 edges). Le sync est negligeable.

### Decision 4 : Recherche hybride 4 canaux en SQL + Python
**Probleme** : Comment fusionner semantique, BM25, graphe et temporel efficacement ?
**Options** :
  - Option A : Tout en SQL (RRF via FULL OUTER JOIN entre vec0 et FTS5) + graphe/temporel en Python
  - Option B : Tout en Python (extraire les candidats, scorer en Python)
**Choix** : Option A — SQL pour vec+FTS, Python pour graphe+temporel
**Raison** : sqlite-vec et FTS5 ont un RRF natif en SQL (documente dans les exemples officiels). C'est plus rapide que de tout faire en Python. Les canaux graphe (PageRank spreading) et temporel (fenetres valid_from/to) sont plus naturels en Python avec NetworkX.

### Decision 5 : Embeddings charges au startup via lifespan
**Probleme** : Le modele BGE-Base fait ~450MB. On ne peut pas le charger a chaque requete.
**Options** :
  - Option A : Lifespan FastMCP — charge au demarrage, partage via contexte
  - Option B : Lazy loading au premier appel
**Choix** : Option A — lifespan
**Raison** : Le MCP SDK supporte nativement le pattern lifespan avec typing. Le modele est charge une fois, partage entre tous les tool calls. Le cold start est ~3-5s (acceptable pour un serveur local qui tourne en continu).

### Decision 6 : Vaults = isolation par namespace SQLite
**Probleme** : Comment isoler les memoires par vault sans multiplier les fichiers DB ?
**Options** :
  - Option A : Un fichier SQLite par vault (isolation physique)
  - Option B : Un seul fichier avec colonne `vault_id` sur chaque table + vec0 metadata filtering
**Choix** : Option B — colonne vault_id
**Raison** : Avec sqlite-vec, on peut filtrer par metadata dans la requete KNN (`WHERE vault_id = ?`). Un seul fichier = backup simple, pas de gestion multi-DB. L'isolation est logique, pas physique. Si un vault doit etre exporte, un `SELECT WHERE vault_id = X` suffit.

### Decision 7 : Detection de contradictions par heuristique semantique
**Probleme** : Sheaf Cohomology est puissant mais extremement complexe a implementer.
**Options** :
  - Option A : Heuristique : haute similarite + negation/inversion detectee → warning
  - Option B : Sheaf Cohomology complete
  - Option C : Pas de detection, on fait confiance au LLM
**Choix** : Option A — heuristique
**Raison** : On cherche la similarite cosinus >0.85 dans le meme vault, puis on verifie la negation via des patterns simples (presence de "ne...pas", "plus", "annule", "remplace"). Couvre 80% des cas. Sheaf Cohomology pourra etre ajoutee en P3 si le besoin emerge.

### Decision 8 : Moteur de vitalite ACT-R simplifie
**Probleme** : La dynamique de Langevin sur la boule de Poincare est elegante mais complexe.
**Options** :
  - Option A : ACT-R simplifie : `vitality = sum(t_i^-0.5)` ou t_i = temps depuis le i-eme acces
  - Option B : Langevin complet avec Riemannian manifold
  - Option C : Simple compteur d'acces + TTL
**Choix** : Option A — ACT-R simplifie
**Raison** : Science cognitive prouvee, formule simple, pas de TTL arbitraire. Le calcul est O(n) avec n = nombre d'acces (cache en pratique). L'avantage sur le compteur simple : une memoire accedee 10 fois il y a 1 an declinera, tandis qu'une memoire accedee 2 fois cette semaine restera active. C'est le comportement desire.

## Structure du projet

```
fougasse/
  pyproject.toml
  CLAUDE.md
  README.md                          # Documentation en francais
  LICENSE
  src/
    fougasse/
      __init__.py                    # Version, metadata
      __main__.py                    # Entry point `python -m fougasse`
      server.py                      # MCP server (MCPServer + lifespan + tools)
      cli.py                         # Click CLI (status, prune, export, import, vaults)
      config.py                      # Configuration (TOML + defaults)
      models.py                      # Pydantic models (Memory, Vault, SearchResult, etc.)
      embeddings.py                  # Sentence-transformers wrapper (load, encode, batch)
      storage/
        __init__.py
        database.py                  # SQLite connection, WAL, migrations
        memory_store.py              # CRUD memories (insert, update, delete, get)
        vector_store.py              # sqlite-vec operations (insert, KNN search)
        fts_store.py                 # FTS5 operations (index, BM25 search)
        migrations.py                # Migration runner
      retrieval/
        __init__.py
        hybrid_search.py             # 4-channel search orchestrator
        rrf_fusion.py                # Reciprocal Rank Fusion (SQL + Python)
        temporal_search.py           # Temporal window filtering
        graph_search.py              # Graph-based retrieval (spreading activation)
        reranker.py                  # Cross-encoder reranking (P1)
      graph/
        __init__.py
        knowledge_graph.py           # NetworkX graph management
        entity_linker.py             # Tag/entity-based edge creation
        contradiction_detector.py    # Semantic contradiction heuristic
        community_detector.py        # Leiden clustering
        persistence.py               # Graph <-> SQLite sync
      vitality/
        __init__.py
        decay_engine.py              # ACT-R vitality calculator
        consolidation.py             # Memory merging and archival
        scheduler.py                 # Periodic vitality update process
  migrations/
    001_init.sql                     # Core tables, vec0, FTS5, graph tables
    002_vitality.sql                 # Vitality tracking tables
    003_versioning.sql               # Memory version history
  tests/
    conftest.py                      # Fixtures (in-memory DB, mock embeddings)
    test_storage/
    test_retrieval/
    test_graph/
    test_vitality/
    test_server.py                   # MCP tool integration tests
    test_cli.py                      # CLI command tests
  .specs/                            # Ce dossier
  .github/
    workflows/
      ci.yml                         # Test matrix: macOS, Windows, Linux
```

## Modele de donnees technique

```sql
-- Table principale des memoires
CREATE TABLE memories (
    id TEXT PRIMARY KEY,              -- UUID v7
    content TEXT NOT NULL,
    type TEXT NOT NULL,                -- text, code, task, appointment, idea, conversation, topic
    vault_id TEXT NOT NULL DEFAULT 'default',
    source_agent TEXT,                 -- ex: "claude-code", "cursor", "cruchot"
    metadata JSON,                     -- flexible key-value
    vitality_score REAL DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,          -- ISO 8601
    updated_at TEXT NOT NULL,
    FOREIGN KEY (vault_id) REFERENCES vaults(id)
);

-- Vaults (namespaces)
CREATE TABLE vaults (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);

-- Tags (many-to-many)
CREATE TABLE tags (
    memory_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (memory_id, tag),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Historique d'acces (pour ACT-R)
CREATE TABLE access_log (
    memory_id TEXT NOT NULL,
    accessed_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Versions (historique des modifications)
CREATE TABLE memory_versions (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    version_number INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Graphe de connaissances : noeuds
CREATE TABLE graph_nodes (
    id TEXT PRIMARY KEY,               -- memory_id ou entity_id
    node_type TEXT NOT NULL,            -- 'memory' ou 'entity'
    label TEXT NOT NULL,
    pagerank REAL DEFAULT 0.0,
    community_id INTEGER,
    created_at TEXT NOT NULL
);

-- Graphe de connaissances : aretes
CREATE TABLE graph_edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,             -- relates_to, supersedes, conflicts_with, tagged_with
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id, relation),
    FOREIGN KEY (source_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
);

-- Recherche vectorielle (sqlite-vec)
CREATE VIRTUAL TABLE vec_memories USING vec0(
    memory_id TEXT,
    vault_id TEXT,
    embedding float[768],
    +is_archived INTEGER
);

-- Recherche plein texte (FTS5)
CREATE VIRTUAL TABLE fts_memories USING fts5(
    content,
    tags,
    content=memories,
    content_rowid=rowid
);

-- Donnees comportementales (RGPD-separe dans learning.db)
-- Table: search_patterns (queries frequentes, resultats cliques)
-- Table: feedback (memoires jugees utiles/inutiles par l'utilisateur)
```

## Securite (Security by Design)

### Authentification & Autorisation
- Pas d'auth (single-user, local only)
- Le serveur MCP ecoute uniquement via stdio (pas de port reseau)
- SSE optionnel : bind sur 127.0.0.1 uniquement, jamais 0.0.0.0

### Validation des entrees
- Tous les tool inputs valides par Pydantic models (types, longueurs, formats)
- Content : max 100KB par memoire (configurable)
- Tags : max 20 par memoire, alphanum + tirets seulement
- Vault ID : alphanum + tirets, max 64 chars
- SQL : parameterized queries exclusivement

### Protection des donnees
- DB files dans `~/.fougasse/` avec permissions 700 (user-only)
- Soft-delete par defaut (flag `is_archived`)
- Hard-delete explicite via CLI `fougasse prune --hard`
- Export complet via `fougasse export` (JSON, droit d'acces RGPD)
- Donnees comportementales separees dans `learning.db`
- Chiffrement optionnel : SQLCipher si configure (P3)

### Surface d'attaque & Mitigations
| Point d'entree | Menace | Mitigation |
|-----------------|--------|------------|
| MCP stdio | Memory poisoning via LLM malveillant | Provenance tracking (source_agent), scoring confiance P3 |
| MCP tool inputs | Injection SQL | Pydantic validation + parameterized queries |
| DB files sur disque | Acces non autorise | Permissions fichier 700, chiffrement optionnel |
| Modele d'embedding | Model supply chain attack | Pin de la version du modele, hash verification |
| Dependencies Python | Supply chain attack | uv.lock pinne, dependabot alerts |

## Risques architecturaux
| Risque | Probabilite | Impact | Mitigation |
|--------|-------------|--------|------------|
| Graphe NetworkX trop gros en RAM (>500K noeuds) | Faible (horizon 5+ ans) | Moyen — OOM | Monitoring taille, archivage agressif, migration igraph si necessaire |
| sqlite-vec brute-force trop lent a >500K vecteurs | Faible | Moyen — latence | Partitionnement par vault, pre-filtrage par metadata |
| Modele embedding deprecie / meilleur modele disponible | Moyen | Eleve — re-indexation complete | Script de re-indexation, dual-index temporaire pendant migration |
| WAL lock contention (CLI + MCP simultanees) | Faible | Faible | WAL + busy_timeout, CLI read-only par defaut |
| Incompatibilite cross-platform sqlite-vec | Faible | Eleve | Test CI matrix sur 3 OS, wheels pre-build par sqlite-vec |
