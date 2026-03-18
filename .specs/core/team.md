# Team Orchestration — Fougasse core

> **Date** : 2026-03-18
> **Genere depuis** : TEAM-ANALYSIS.md + TASKS.md
> **Verdict** : OUI PARTIEL — 5 agents, 5 vagues, ~25% gain

## Lancement

### Prerequis
- Warp terminal ouvert
- tmux installe (`brew install tmux` si necessaire)

### Commandes
```bash
# 1. Creer une session tmux
tmux new -s fougasse-core

# 2. Lancer Claude Code avec ce prompt
cat .specs/core/team.md | claude
```

---

## Instructions d'orchestration

Tu es le **leader** d'une agent team. Tu dois orchestrer 5 agents pour realiser 43 taches du projet Fougasse.

### Contexte projet
Fougasse est un serveur MCP local + moteur de memoire persistante qui centralise le contexte entre tous les clients LLM (Claude Desktop, Claude Code, Cursor, etc.). Stack Python, stockage SQLite + sqlite-vec, embeddings BGE-Base via sentence-transformers, graphe NetworkX, CLI Click. Full local, cross-platform.

### Regles d'orchestration
1. Tu es le leader. Tu ne codes PAS toi-meme (sauf T01 si applicable).
2. Tu crees la team, les taches, spawn les agents, et tu coordonnes.
3. Chaque agent travaille dans son perimetre de fichiers — AUCUN chevauchement.
4. Tu respectes le sequencage par vagues — ne lance pas une vague avant que la precedente soit terminee.
5. Aux points de synchronisation, tu valides que tout est OK avant de continuer.
6. Si un agent echoue, tu diagnostiques et relances — tu ne passes PAS a la vague suivante.
7. Chaque agent doit lire CLAUDE.md avant de commencer.

### Etape 1 : Creer la team

Utilise TeamCreate :
- team_name: "fougasse-core"
- description: "Fougasse MCP memory server — core development"

### Etape 2 : Creer les taches

Cree chaque tache avec TaskCreate puis configure les dependances avec TaskUpdate (addBlockedBy).

Voir **Annexe** en fin de fichier pour le detail complet de chaque tache.

### Etape 3 : Spawner les agents

#### Agent 1 : storage-agent

```
Utilise Agent avec :
- name: "storage-agent"
- team_name: "fougasse-core"
- subagent_type: "general-purpose"
- model: "sonnet"
- mode: "bypassPermissions"
- prompt: |
    Tu es l'agent storage-agent. Tu fais partie de la team fougasse-core.

    TON PERIMETRE : src/fougasse/storage/ + migrations/
    TES TACHES : T03, T05, T07, T08, T11

    REGLES :
    - Ne modifie JAMAIS de fichiers en dehors de src/fougasse/storage/ et migrations/
    - Apres chaque tache terminee, marque-la completed avec TaskUpdate
    - Puis consulte TaskList pour prendre la prochaine tache non bloquee
    - Si tu es bloque, envoie un message au leader via SendMessage
    - Respecte les criteres d'acceptation de chaque tache
    - Lis CLAUDE.md avant de commencer

    CONTEXTE TECHNIQUE :
    - SQLite avec WAL mode et foreign keys
    - Parameterized queries ONLY — zero string interpolation
    - sqlite-vec pour les vecteurs (float[768], struct.pack pour serialisation)
    - FTS5 pour BM25 avec triggers de sync
    - Migrations : scripts SQL numerotes dans migrations/
    - Tests avec DB in-memory (pytest, tmp_path)
    - Permissions 700 sur ~/.fougasse/
```

#### Agent 2 : retrieval-agent

```
Utilise Agent avec :
- name: "retrieval-agent"
- team_name: "fougasse-core"
- subagent_type: "general-purpose"
- model: "sonnet"
- mode: "bypassPermissions"
- prompt: |
    Tu es l'agent retrieval-agent. Tu fais partie de la team fougasse-core.

    TON PERIMETRE : src/fougasse/retrieval/
    TES TACHES : T09, T18, T19, T20, T21

    REGLES :
    - Ne modifie JAMAIS de fichiers en dehors de src/fougasse/retrieval/
    - Apres chaque tache terminee, marque-la completed avec TaskUpdate
    - Puis consulte TaskList pour prendre la prochaine tache non bloquee
    - Si tu es bloque, envoie un message au leader via SendMessage
    - Respecte les criteres d'acceptation de chaque tache
    - Lis CLAUDE.md avant de commencer

    CONTEXTE TECHNIQUE :
    - RRF fusion : SQL FULL OUTER JOIN entre vec0 et FTS5 avec 1/(k+rank)
    - 4 canaux en P1 : semantique (vec KNN), BM25 (FTS5), graphe (spreading activation), temporel
    - Poids configurables par canal (defaut 1.0)
    - Cross-encoder reranker : ms-marco-MiniLM-L-6-v2 (lazy loading)
    - Fallback gracieux si un canal echoue
    - Tests avec corpus de memoires connues
```

#### Agent 3 : graph-agent

```
Utilise Agent avec :
- name: "graph-agent"
- team_name: "fougasse-core"
- subagent_type: "general-purpose"
- model: "sonnet"
- mode: "bypassPermissions"
- prompt: |
    Tu es l'agent graph-agent. Tu fais partie de la team fougasse-core.

    TON PERIMETRE : src/fougasse/graph/
    TES TACHES : T15, T16, T17, T22, T23

    REGLES :
    - Ne modifie JAMAIS de fichiers en dehors de src/fougasse/graph/
    - Apres chaque tache terminee, marque-la completed avec TaskUpdate
    - Puis consulte TaskList pour prendre la prochaine tache non bloquee
    - Si tu es bloque, envoie un message au leader via SendMessage
    - Respecte les criteres d'acceptation de chaque tache
    - Lis CLAUDE.md avant de commencer

    CONTEXTE TECHNIQUE :
    - NetworkX DiGraph pour le graphe de connaissances
    - Persistance dans SQLite (tables graph_nodes, graph_edges)
    - Types de relations : relates_to, supersedes, conflicts_with, tagged_with
    - PageRank via nx.pagerank(), articulation points via Tarjan
    - Leiden communities via leidenalg (conversion NetworkX → igraph)
    - Sync incrementale : ecrire dans SQLite a chaque modification du graphe
    - Contradiction detector : similarite >0.85 + patterns de negation
```

#### Agent 4 : vitality-agent

```
Utilise Agent avec :
- name: "vitality-agent"
- team_name: "fougasse-core"
- subagent_type: "general-purpose"
- model: "sonnet"
- mode: "bypassPermissions"
- prompt: |
    Tu es l'agent vitality-agent. Tu fais partie de la team fougasse-core.

    TON PERIMETRE : src/fougasse/vitality/
    TES TACHES : T27, T28, T29, T30, T31, T32, T34

    REGLES :
    - Ne modifie JAMAIS de fichiers en dehors de src/fougasse/vitality/
    - Exception : T28 modifie hybrid_search.py et memory_store.py (access logging)
    - Apres chaque tache terminee, marque-la completed avec TaskUpdate
    - Puis consulte TaskList pour prendre la prochaine tache non bloquee
    - Si tu es bloque, envoie un message au leader via SendMessage
    - Respecte les criteres d'acceptation de chaque tache
    - Lis CLAUDE.md avant de commencer

    CONTEXTE TECHNIQUE :
    - Modele ACT-R : vitality = sum(t_i^-0.5), t_i = temps depuis le i-eme acces
    - Seuil d'archivage configurable (defaut 0.1)
    - Soft-delete (is_archived=1), jamais hard-delete automatique
    - Consolidation : similarite >0.9 → fusion, lien supersedes
    - Resurrection : memoire archivee retrouvee → desarchiver + boost vitality
    - Scheduler asyncio pour le decay periodique (defaut toutes les 6h)
```

#### Agent 5 : server-agent

```
Utilise Agent avec :
- name: "server-agent"
- team_name: "fougasse-core"
- subagent_type: "general-purpose"
- model: "sonnet"
- mode: "bypassPermissions"
- prompt: |
    Tu es l'agent server-agent. Tu fais partie de la team fougasse-core.

    TON PERIMETRE : src/fougasse/server.py + src/fougasse/cli.py
    TES TACHES : T10, T24, T25, T33, T37

    REGLES :
    - Ne modifie JAMAIS de fichiers en dehors de server.py et cli.py
    - Apres chaque tache terminee, marque-la completed avec TaskUpdate
    - Puis consulte TaskList pour prendre la prochaine tache non bloquee
    - Si tu es bloque, envoie un message au leader via SendMessage
    - Respecte les criteres d'acceptation de chaque tache
    - Lis CLAUDE.md avant de commencer

    CONTEXTE TECHNIQUE :
    - MCP SDK Python : MCPServer avec lifespan async context manager
    - Tools : fougasse_remember, fougasse_recall, fougasse_forget, fougasse_status, fougasse_explore, fougasse_update, fougasse_vaults
    - Transport stdio (principal), SSE localhost optionnel
    - Pydantic models pour validation de tous les inputs
    - Click pour CLI admin (status, prune, export, import, vaults, stats)
    - Rich pour output formatte, --json pour machine-readable
    - Ne jamais logger le contenu des memoires a INFO (seulement DEBUG)
```

### Etape 4 : Gestion des vagues

#### Vague 0 — Bootstrap (leader seul)
Le leader execute T01 (scaffolding) lui-meme, puis lance T02, T03, T04 en parallele.

**Taches** : T01, T02, T03, T04
**Validation** :
```bash
uv sync
uv run python -m fougasse
uv run pytest tests/test_config.py tests/test_models.py -v
```

#### Vague 1 — P0 core (storage-agent + leader)
- **storage-agent** : T05 → T07 → T08 → T11
- **leader** : T06 (embeddings — necessite avant T07)

**Taches** : T05, T06, T07, T08, T11
**Dependances** : T06 doit etre fait avant T07 (vector store a besoin des embeddings)
**Validation** :
```bash
uv run pytest tests/test_storage/ -v
uv run pytest tests/test_embeddings.py -v
```

#### Vague 2 — P0 integration (retrieval-agent + server-agent)
- **retrieval-agent** : T09 (RRF fusion, 2 canaux P0)
- **server-agent** : T10 (MCP server tools — apres T09), T12 (CLI)
- **leader** : T13 (tests P0), T14 (CI)

**Taches** : T09, T10, T11, T12, T13, T14
**Sync** : Apres T14, MVP P0 complet et teste. CI verte obligatoire avant P1.
**Validation** :
```bash
uv run pytest -v
uv run ruff check .
uv run mypy src/fougasse/
```

#### Vague 3 — P1 (graph-agent + retrieval-agent + server-agent)
- **graph-agent** : T15 → T16, T17 → T22, T23
- **retrieval-agent** : T19, puis T18 (apres T16+T17), T20 (apres T18+T19), T21
- **server-agent** : T24 (apres T20), T25 (apres T15)
- **leader** : T26 (tests P1)

**Taches** : T15-T26
**Sync** : Apres T26, P1 complet et teste. Tous les tests doivent passer.
**Validation** :
```bash
uv run pytest tests/test_graph/ tests/test_retrieval/ -v
uv run pytest tests/test_integration_p1.py -v
```

#### Vague 4 — P2 (vitality-agent + server-agent)
- **vitality-agent** : T27, T28 → T29 → T30 → T34
- **server-agent** : T33 (Tarjan protection), T37 (stats avancees)
- **leader** : T31 (versioning), T32 (resurrection), T35 (tests P2)

**Taches** : T27-T35
**Sync** : Apres T35, P2 complet et teste.
**Validation** :
```bash
uv run pytest tests/test_vitality/ -v
uv run pytest tests/test_integration_p2.py -v
```

#### Vague 5 — P3 (parallele puis sequentiel)
- **server-agent** : T37 (si pas fait), T38 (export/import complet)
- **leader** : T36 (provenance scoring), T39 (RGPD), T40 (benchmarks)
- Puis sequentiel : T41 (docs) → T42 (packaging) → T43 (tests finaux)

**Taches** : T36-T43
**Validation finale** :
```bash
uv run pytest --cov=fougasse -v
uv run ruff check .
uv run mypy src/fougasse/ --strict
uv run hatch build
```

### Points de synchronisation

| Apres | Condition | Action |
|-------|-----------|--------|
| Vague 0 | `uv sync` OK, structure creee, tests config/models verts | Lancer Vague 1 |
| Vague 2 | MVP P0 complet, CI verte, `fougasse_remember` + `fougasse_recall` fonctionnels E2E | Lancer Vague 3 |
| T26 | Tous les tests P1 verts, retrieval 4 canaux fonctionnel | Lancer Vague 4 |
| T35 | Tous les tests P2 verts, vitality + consolidation fonctionnels | Lancer Vague 5 |
| T43 | Coverage >80%, CI verte 3 OS, zero warning mypy, package build OK | Shutdown team |

### Gestion des erreurs

- Si un agent signale une erreur → lis son message, diagnostique, envoie des instructions via SendMessage
- Si une tache echoue 2 fois → prends-la en charge toi-meme
- Si un conflit de fichiers est detecte → STOP, resous manuellement, puis relance
- **Fichiers a risque de conflit** : server.py (T10, T24, T25, T33, T37), hybrid_search.py (T09, T20, T28, T32)

### Shutdown

Quand toutes les taches sont terminees :
1. Verifie TaskList — tout doit etre "completed"
2. Envoie un shutdown_request a chaque agent
3. Attends les shutdown_response
4. Supprime la team avec TeamDelete

---

## Annexe : Detail des taches

### T01 · Init projet
**Phase** : P0
**But** : Scaffolding complet du projet avec uv, pyproject.toml, structure de dossiers.
**Fichiers** : `[NEW]` pyproject.toml, src/fougasse/__init__.py, src/fougasse/__main__.py, .gitignore, LICENSE, .github/workflows/ci.yml
**Dependances** : aucune
**Criteres d'acceptation** :
- [ ] `uv sync` installe les deps sans erreur
- [ ] `uv run python -m fougasse` retourne un message de version
- [ ] Structure de dossiers conforme a l'architecture technique
- [ ] .gitignore couvre .venv, __pycache__, *.db, .fougasse/

---

### T02 · Config
**Phase** : P0
**But** : Module de configuration avec fichier TOML et valeurs par defaut.
**Fichiers** : `[NEW]` src/fougasse/config.py, tests/test_config.py
**Dependances** : T01
**Criteres d'acceptation** :
- [ ] Config charge ~/.fougasse/config.toml s'il existe
- [ ] Valeurs par defaut pour : db_path, model_name, vault_default, vitality_threshold, max_results
- [ ] Override par variables d'environnement
- [ ] Creation automatique du dossier ~/.fougasse/ si absent

---

### T03 · SQLite + migrations
**Phase** : P0
**But** : Couche database avec connexion SQLite, WAL, FK, et systeme de migrations.
**Fichiers** : `[NEW]` src/fougasse/storage/__init__.py, storage/database.py, storage/migrations.py, migrations/001_init.sql, tests/test_storage/test_database.py
**Dependances** : T01
**Criteres d'acceptation** :
- [ ] Connexion SQLite avec WAL mode et foreign keys actives
- [ ] Migration runner applique les scripts SQL dans l'ordre
- [ ] Table schema_version tracke les migrations appliquees
- [ ] 001_init.sql cree : memories, vaults, tags, access_log, graph_nodes, graph_edges
- [ ] Tests avec DB in-memory

---

### T04 · Models Pydantic
**Phase** : P0
**But** : Modeles de donnees Pydantic pour la validation des inputs/outputs MCP.
**Fichiers** : `[NEW]` src/fougasse/models.py, tests/test_models.py
**Dependances** : T01
**Criteres d'acceptation** :
- [ ] MemoryCreate, Memory, SearchQuery, SearchResult, Vault, FougasseStatus
- [ ] Validation : content max 100KB, tags max 20, vault_id alphanum+tirets
- [ ] Serialisation JSON fonctionnelle

---

### T05 · Memory store CRUD
**Phase** : P0
**But** : Operations CRUD sur les memoires dans SQLite.
**Fichiers** : `[NEW]` src/fougasse/storage/memory_store.py, tests/test_storage/test_memory_store.py
**Dependances** : T03, T04
**Criteres d'acceptation** :
- [ ] insert_memory : genere UUID v7, stocke dans memories + tags
- [ ] get_memory, update_memory, delete_memory (soft-delete par defaut)
- [ ] list_memories : filtrage par vault_id, type, tags, is_archived, pagination
- [ ] Queries parametrees exclusivement

---

### T06 · Embeddings wrapper
**Phase** : P0
**But** : Wrapper sentence-transformers pour charger BGE-Base et encoder du texte.
**Fichiers** : `[NEW]` src/fougasse/embeddings.py, tests/test_embeddings.py
**Dependances** : T02
**Criteres d'acceptation** :
- [ ] Charge BAAI/bge-base-en-v1.5, cache dans ~/.fougasse/models/
- [ ] encode(text) -> list[float] avec normalisation L2
- [ ] encode_batch(texts) pour ingestion en masse
- [ ] Auto-detection device : MPS (Mac), CUDA, CPU
- [ ] serialize(vector) -> bytes via struct.pack

---

### T07 · Vector store
**Phase** : P0
**But** : Integration sqlite-vec pour stockage et recherche vectorielle.
**Fichiers** : `[NEW]` src/fougasse/storage/vector_store.py, tests/test_storage/test_vector_store.py, `[MODIFY]` migrations/001_init.sql
**Dependances** : T05, T06
**Criteres d'acceptation** :
- [ ] sqlite_vec.load(db) charge l'extension cross-platform
- [ ] Table vec0 vec_memories float[768]
- [ ] insert_vector, search_knn avec metadata filtering (vault_id, is_archived)
- [ ] Tests KNN avec vecteurs connus

---

### T08 · FTS store
**Phase** : P0
**But** : Index FTS5 pour la recherche plein texte BM25.
**Fichiers** : `[NEW]` src/fougasse/storage/fts_store.py, tests/test_storage/test_fts_store.py, `[MODIFY]` migrations/001_init.sql
**Dependances** : T05
**Criteres d'acceptation** :
- [ ] Table FTS5 fts_memories indexe content + tags
- [ ] Triggers SQLite pour sync auto INSERT/UPDATE/DELETE
- [ ] search_bm25(query, limit) -> [(memory_id, rank)]

---

### T09 · RRF fusion
**Phase** : P0
**But** : Fusion Reciprocal Rank Fusion entre resultats vec et FTS.
**Fichiers** : `[NEW]` src/fougasse/retrieval/__init__.py, retrieval/rrf_fusion.py, retrieval/hybrid_search.py (P0 : 2 canaux), tests/test_retrieval/
**Dependances** : T07, T08
**Criteres d'acceptation** :
- [ ] RRF en SQL (FULL OUTER JOIN vec + FTS avec 1/(k+rank))
- [ ] hybrid_search(query, vault_id, limit) -> SearchResult
- [ ] k configurable (defaut 60)

---

### T10 · MCP server tools
**Phase** : P0
**But** : Serveur MCP avec les 4 tools de base.
**Fichiers** : `[NEW]` src/fougasse/server.py, tests/test_server.py
**Dependances** : T09
**Securite** : validation Pydantic sur tous les inputs, jamais logger le contenu en INFO
**Criteres d'acceptation** :
- [ ] MCPServer avec lifespan (charge embeddings + ouvre DB)
- [ ] Tools : fougasse_remember, fougasse_recall, fougasse_forget, fougasse_status
- [ ] Transport stdio fonctionnel
- [ ] Test E2E : remember → recall retrouve la memoire

---

### T11 · Vaults
**Phase** : P0
**But** : Gestion des vaults (namespaces isoles).
**Fichiers** : `[MODIFY]` src/fougasse/storage/memory_store.py, src/fougasse/server.py, `[NEW]` tests/test_vaults.py
**Dependances** : T05
**Criteres d'acceptation** :
- [ ] Vault "default" cree auto, CRUD vaults
- [ ] Toutes les operations filtrent par vault_id
- [ ] Tool MCP fougasse_vaults

---

### T12 · CLI admin
**Phase** : P0
**But** : Interface CLI pour administration.
**Fichiers** : `[NEW]` src/fougasse/cli.py, tests/test_cli.py
**Dependances** : T10, T11
**Criteres d'acceptation** :
- [ ] Commandes : status, prune, export, import, vaults
- [ ] Flag --json sur toutes les commandes
- [ ] Entry point dans pyproject.toml

---

### T13 · Tests P0
**Phase** : P0
**But** : Couverture de tests complete P0.
**Fichiers** : `[NEW]` tests/conftest.py, tests/test_integration_p0.py
**Dependances** : T12
**Criteres d'acceptation** :
- [ ] Tests integration : remember → recall → forget cycle complet
- [ ] Tests multi-vault, coverage >70%

---

### T14 · CI GitHub Actions
**Phase** : P0
**But** : Pipeline CI cross-platform.
**Fichiers** : `[NEW]` .github/workflows/ci.yml
**Dependances** : T13
**Criteres d'acceptation** :
- [ ] Matrix : macOS, Windows, Ubuntu × Python 3.11 + 3.12
- [ ] Steps : uv sync, ruff, mypy, pytest

---

### T15 · Knowledge graph core
**Phase** : P1
**But** : Graphe NetworkX avec operations de base.
**Fichiers** : `[NEW]` src/fougasse/graph/__init__.py, graph/knowledge_graph.py, tests/test_graph/test_knowledge_graph.py
**Dependances** : T14
**Criteres d'acceptation** :
- [ ] DiGraph avec types memory/entity, relations relates_to/supersedes/conflicts_with/tagged_with
- [ ] add_node, add_edge, remove_node, get_neighbors, get_subgraph
- [ ] Charge depuis SQLite au demarrage, sync sur ecriture

---

### T16 · Entity linker
**Phase** : P1
**But** : Creation automatique d'aretes basee sur tags partages et proximite semantique.
**Fichiers** : `[NEW]` src/fougasse/graph/entity_linker.py, tests/test_graph/test_entity_linker.py
**Dependances** : T15
**Criteres d'acceptation** :
- [ ] Edges tagged_with vers entites-tags
- [ ] 2+ tags communs → edge relates_to
- [ ] Similarite cosinus >0.8 → edge relates_to

---

### T17 · Graph persistence
**Phase** : P1
**But** : Sync bidirectionnelle NetworkX ↔ SQLite.
**Fichiers** : `[NEW]` src/fougasse/graph/persistence.py, tests/test_graph/test_persistence.py
**Dependances** : T15
**Criteres d'acceptation** :
- [ ] save_graph, load_graph, sync incrementale

---

### T18 · Graph search channel
**Phase** : P1
**But** : Recherche par spreading activation sur le graphe.
**Fichiers** : `[NEW]` src/fougasse/retrieval/graph_search.py, tests/test_retrieval/test_graph_search.py
**Dependances** : T16, T17
**Criteres d'acceptation** :
- [ ] Spreading activation 3 hops, decroissance 0.5/hop
- [ ] Ignore les noeuds archives

---

### T19 · Temporal search channel
**Phase** : P1
**But** : Recherche par proximite temporelle.
**Fichiers** : `[NEW]` src/fougasse/retrieval/temporal_search.py, tests/test_retrieval/test_temporal_search.py
**Dependances** : T14
**Criteres d'acceptation** :
- [ ] Score temporel exp(-lambda * age_in_days)
- [ ] Filtrage par plage de dates

---

### T20 · Retrieval 4 canaux
**Phase** : P1
**But** : Orchestrateur 4 canaux en parallele.
**Fichiers** : `[MODIFY]` src/fougasse/retrieval/hybrid_search.py, tests/test_retrieval/test_hybrid_search.py
**Dependances** : T18, T19
**Criteres d'acceptation** :
- [ ] Execute vec + FTS + graph + temporal en parallele (asyncio)
- [ ] RRF etendu 4 listes, poids configurables, fallback gracieux

---

### T21 · Cross-encoder reranker
**Phase** : P1
**But** : Reranking via cross-encoder.
**Fichiers** : `[NEW]` src/fougasse/retrieval/reranker.py, tests/test_retrieval/test_reranker.py
**Dependances** : T20
**Criteres d'acceptation** :
- [ ] ms-marco-MiniLM-L-6-v2, reranke top-20, activable/desactivable

---

### T22 · Contradiction detector
**Phase** : P1
**But** : Detection heuristique de contradictions.
**Fichiers** : `[NEW]` src/fougasse/graph/contradiction_detector.py, tests/test_graph/test_contradiction_detector.py
**Dependances** : T16
**Criteres d'acceptation** :
- [ ] Similarite >0.85 + patterns de negation → supersedes ou conflicts_with
- [ ] Warning retourne dans la reponse fougasse_remember

---

### T23 · PageRank + Leiden
**Phase** : P1
**But** : PageRank et detection de communautes.
**Fichiers** : `[NEW]` src/fougasse/graph/community_detector.py, `[MODIFY]` graph/knowledge_graph.py, tests/test_graph/test_community_detector.py
**Dependances** : T17
**Criteres d'acceptation** :
- [ ] compute_pagerank, detect_communities (Leiden via leidenalg)
- [ ] Stocke community_id dans graph_nodes

---

### T24 · MCP tool explore
**Phase** : P1
**But** : Tool MCP pour naviguer dans le graphe.
**Fichiers** : `[MODIFY]` src/fougasse/server.py, tests/test_server.py
**Dependances** : T20
**Criteres d'acceptation** :
- [ ] fougasse_explore(entry_point, depth, max_nodes) → sous-graphe JSON

---

### T25 · MCP tool update
**Phase** : P1
**But** : Tool MCP pour mettre a jour une memoire avec versioning.
**Fichiers** : `[MODIFY]` src/fougasse/server.py, storage/memory_store.py, `[NEW]` migrations/003_versioning.sql
**Dependances** : T15
**Criteres d'acceptation** :
- [ ] fougasse_update avec versioning, re-embedding si content change

---

### T26 · Tests P1
**Phase** : P1
**But** : Couverture de tests P1.
**Fichiers** : `[NEW]` tests/test_integration_p1.py
**Dependances** : T24, T25, T21, T22, T23
**Criteres d'acceptation** :
- [ ] Tests graphe, contradictions, reranker, 4 canaux, coverage >75%

---

### T27 · ACT-R decay engine
**Phase** : P2
**But** : Calcul de vitalite ACT-R.
**Fichiers** : `[NEW]` src/fougasse/vitality/__init__.py, vitality/decay_engine.py, tests/test_vitality/test_decay_engine.py
**Dependances** : T26
**Criteres d'acceptation** :
- [ ] compute_vitality : sum(t_i^-0.5), update_all_vitalities, <1s pour 100K

---

### T28 · Access logging
**Phase** : P2
**But** : Enregistrement de chaque acces en lecture.
**Fichiers** : `[MODIFY]` src/fougasse/retrieval/hybrid_search.py, storage/memory_store.py, `[NEW]` tests/test_vitality/test_access_logging.py
**Dependances** : T26
**Criteres d'acceptation** :
- [ ] Chaque recall/explore → log dans access_log, batch insert

---

### T29 · Archivage automatique
**Phase** : P2
**But** : Archive les memoires sous le seuil de vitalite.
**Fichiers** : `[NEW]` src/fougasse/vitality/consolidation.py, tests/test_vitality/test_consolidation.py
**Dependances** : T27, T28
**Criteres d'acceptation** :
- [ ] archive_stale_memories(threshold), exclure memoires pinned

---

### T30 · Consolidation
**Phase** : P2
**But** : Fusion de memoires redondantes.
**Fichiers** : `[MODIFY]` src/fougasse/vitality/consolidation.py, `[NEW]` tests/test_vitality/test_merge.py
**Dependances** : T27
**Criteres d'acceptation** :
- [ ] Similarite >0.9 → fusion, mode auto ou suggestion, preserve historique

---

### T31 · Memory versioning
**Phase** : P2
**But** : Historique complet des modifications.
**Fichiers** : `[MODIFY]` src/fougasse/storage/memory_store.py, `[NEW]` tests/test_storage/test_versioning.py
**Dependances** : T26
**Criteres d'acceptation** :
- [ ] Chaque update → entree memory_versions, get_versions, get_version

---

### T32 · Resurrection
**Phase** : P2
**But** : Boost de vitalite quand une memoire archivee est retrouvee.
**Fichiers** : `[MODIFY]` retrieval/hybrid_search.py, vitality/decay_engine.py, `[NEW]` tests/test_vitality/test_resurrection.py
**Dependances** : T29
**Criteres d'acceptation** :
- [ ] Memoire archivee dans resultats recall → desarchiver + boost vitalite

---

### T33 · Protection Tarjan
**Phase** : P2
**But** : Warning avant suppression de noeuds critiques du graphe.
**Fichiers** : `[MODIFY]` graph/knowledge_graph.py, server.py
**Dependances** : T26
**Criteres d'acceptation** :
- [ ] is_articulation_point via nx, warning sur delete, force=true pour override

---

### T34 · Scheduler periodique
**Phase** : P2
**But** : Processus background pour decay et consolidation.
**Fichiers** : `[NEW]` src/fougasse/vitality/scheduler.py, `[MODIFY]` server.py
**Dependances** : T29, T30
**Criteres d'acceptation** :
- [ ] Asyncio task au demarrage, intervalle configurable (defaut 6h), arret propre

---

### T35 · Tests P2
**Phase** : P2
**But** : Couverture de tests P2.
**Fichiers** : `[NEW]` tests/test_integration_p2.py
**Dependances** : T34, T31, T32, T33
**Criteres d'acceptation** :
- [ ] Cycle complet remember → access → decay → archive → recall → resurrect, coverage >80%

---

### T36 · Provenance scoring
**Phase** : P3
**But** : Score de confiance par source_agent (Beta-Binomial bayesien).
**Fichiers** : `[NEW]` src/fougasse/security/__init__.py, security/trust_scoring.py, tests/test_security/
**Dependances** : T35
**Criteres d'acceptation** :
- [ ] Beta(alpha, beta), feedback positif/negatif asymetrique, agents <0.3 → warning

---

### T37 · Statistiques avancees
**Phase** : P3
**But** : Metriques detaillees sur l'etat de Fougasse.
**Fichiers** : `[MODIFY]` server.py, cli.py, `[NEW]` tests/test_stats.py
**Dependances** : T35
**Criteres d'acceptation** :
- [ ] Total memories, by type/vault/agent, top 10 entites/tags, latence P50/P95, graphe stats

---

### T38 · Export/import complet
**Phase** : P3
**But** : Export et import complet avec metadata, graphe, re-embedding.
**Fichiers** : `[MODIFY]` cli.py, `[NEW]` src/fougasse/io/exporter.py, io/importer.py, tests/test_io.py
**Dependances** : T35
**Criteres d'acceptation** :
- [ ] Export JSON complet, option --include-embeddings, import avec re-generation, gestion conflits ID

---

### T39 · RGPD compliance
**Phase** : P3
**But** : Separation donnees comportementales et droit a l'oubli.
**Fichiers** : `[NEW]` src/fougasse/storage/learning_store.py, migrations/004_learning.sql, tests/test_rgpd.py
**Dependances** : T38
**Securite** : separation physique des donnees comportementales
**Criteres d'acceptation** :
- [ ] learning.db separe, CLI gdpr-export et gdpr-delete, hard-delete complet verifie

---

### T40 · Benchmarks integres
**Phase** : P3
**But** : CLI de benchmark pour mesurer les performances de retrieval.
**Fichiers** : `[NEW]` src/fougasse/benchmarks/retrieval_bench.py, `[MODIFY]` cli.py, tests/test_benchmarks.py
**Dependances** : T37
**Criteres d'acceptation** :
- [ ] fougasse bench : N memoires synthetiques, P50/P95/P99, detection regression

---

### T41 · Documentation francaise
**Phase** : P3
**But** : README complet en francais.
**Fichiers** : `[NEW]` README.md, docs/installation.md, docs/usage.md, docs/contributing.md
**Dependances** : T40
**Criteres d'acceptation** :
- [ ] Tout en francais, installation, usage, contribution

---

### T42 · Packaging PyPI
**Phase** : P3
**But** : Build et publication sur PyPI.
**Fichiers** : `[MODIFY]` pyproject.toml, `[NEW]` .github/workflows/publish.yml
**Dependances** : T41
**Criteres d'acceptation** :
- [ ] hatch build OK, pip install fougasse sur env vierge, publish on tag

---

### T43 · Tests P3 + couverture
**Phase** : P3
**But** : Tests finaux et rapport de couverture.
**Fichiers** : `[NEW]` tests/test_integration_p3.py, `[MODIFY]` .github/workflows/ci.yml
**Dependances** : T42, T36, T39
**Criteres d'acceptation** :
- [ ] Coverage >80% global, 3 OS, zero warning mypy, zero erreur ruff
