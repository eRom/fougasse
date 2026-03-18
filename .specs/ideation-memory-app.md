# Compilation - Mémoire Locale & LLM
## Extraction du NotebookLM "Ideation Memory" (30 sources)

---

## 1. FONCTIONNALITES PRINCIPALES

### F1 - Stockage local, persistant et privé
- Toutes les données restent sur la machine, zero cloud
- Fichiers Markdown (Ori-Mnemos) ou bases locales SQLite/ChromaDB
- Elimine les coûts d'API et les risques de fuite

### F2 - Récupération multi-signaux (Hybrid Retrieval)
- Dépasse la simple similarité cosinus du RAG classique
- **4 canaux parallèles** :
  1. **Sémantique** : embeddings + métrique Fisher-Rao (pondération par variance/confiance)
  2. **BM25** : correspondance lexicale exacte (code, noms propres)
  3. **Graphe d'entités** : PageRank / Spreading Activation (3 sauts, décroissance)
  4. **Temporel** : fenêtres `valid_from`/`valid_to`, proximité temporelle
- Fusion via **WRRF** (Weighted Reciprocal Rank Fusion) + **Cross-Encoder** neural pour reranking

### F3 - Structuration cognitive (secteurs de mémoire)
- **Episodique** : flux d'événements, historique narratif
- **Sémantique** : faits, connaissances stables
- **Procédurale** : compétences, workflows appris
- **Emotionnelle** : contexte affectif des interactions
- **Réflexive** : meta-cognition, auto-évaluation

### F4 - Déclin naturel et consolidation
- Inspiré des sciences cognitives (ACT-R, MINERVA 2)
- Les mémoires fréquemment consultées sont renforcées (consolidation)
- Les mémoires inactives déclinent progressivement (pas de TTL arbitraire)
- "Pics de résurrection" quand une note reçoit de nouvelles connexions
- Dynamique de Langevin Riemannienne pour le cycle rétention/oubli

### F5 - Isolation des agents (Vaults)
- Partitionnement structurel en "voûtes" isolées (pas de simples filtres metadata)
- Chaque agent n'accède qu'aux vaults assignés
- Scores de confiance bayésiens contre l'empoisonnement de mémoire
- Séparation données comportementales / mémoire principale (conformité RGPD)

### F6 - Efficacité des tokens et compression
- **Gist Compression** : compression de l'essentiel (5x plus dense)
- **Index Markdown compressé** (MEMORY.md) : table des matières sémantique toujours dans le contexte
- L'agent sait ce qui existe sans charger les détails bruts
- Economies de contexte jusqu'à 99,6%

### F7 - Détection de contradictions
- **Sheaf Cohomology** (théorie des faisceaux) : détecte algébriquement les contradictions inter-contextes
- Création automatique de liens `supersedes` quand un fait contredit un autre
- Contrôle de cohérence à chaque écriture

### F8 - Injection proactive (Hook de pré-injection)
- Hook HTTP **avant** que l'agent reçoive le message
- Injection déterministe du contexte en ~70ms
- L'agent n'a pas besoin de "penser" à appeler ses outils de mémoire

### F9 - Intégration MCP native
- Serveur MCP standard (add_memories, search_memory, list_memories, delete_all)
- Connectable à Claude Desktop, Cursor, Windsurf, VS Code Copilot, etc.
- Portabilité totale entre clients

---

## 2. STACK TECHNIQUE RECOMMANDEE

| Couche | Technologie | Justification |
|--------|------------|---------------|
| **Langage principal** | **Python** | Ecosystème IA/ML riche, FastAPI, scikit-learn, sentence-transformers |
| **Langage perf.** | **Rust** (optionnel) | Noyau haute performance (743K mémoires/s, 2.7ms latence) |
| **DB relationnelle** | **SQLite + FTS5 + WAL** | Local, portable, zero config, concurrent, recherche plein texte |
| **DB vectorielle** | **ChromaDB** | Embeddings locaux, RAG, léger, pas de serveur externe |
| **Graphe** | **NetworkX** + algorithmes Leiden/PageRank | Graphe de connaissances local, détection communautés |
| **Embeddings** | **Sentence-Transformers** (`all-MiniLM-L6-v2`) | In-process, local, rapide |
| **LLM local** | **Ollama** | Exécution locale, zero cloud, conformité privacy |
| **API** | **FastAPI** | REST HTTP + WebSockets + SSE |
| **Protocole** | **MCP (Model Context Protocol)** | Standard universel pour connecter aux clients LLM |
| **Orchestration** | **LangChain / LangGraph** | Chaînage RAG, workflow agents |
| **Stockage fichiers** | **Markdown + Git** | Lisible humain, versionné, éditable manuellement |
| **Recherche lexicale** | **BM25 (Okapi)** | Correspondances exactes, complémente le sémantique |
| **Fusion scores** | **WRRF + Cross-Encoder** | Reranking neural, +104% NDCG@5 |

---

## 3. ARCHITECTURE TECHNIQUE

```
+------------------------------------------------------------------+
|                     CLIENTS LLM (MCP)                             |
|  Claude Desktop | Cursor | Windsurf | VS Code | CLI              |
+----------------------------------+-------------------------------+
                                   |
                          MCP Protocol (stdio/SSE)
                                   |
+----------------------------------v-------------------------------+
|                    SERVEUR MCP LOCAL                              |
|  Tools: add_memories, search_memory, list, delete, recall...     |
|  Resources: memory://index, memory://stats                       |
+----------------------------------+-------------------------------+
                                   |
              +--------------------+--------------------+
              |                                         |
+-------------v--------------+           +--------------v-----------+
|   HOOK PRE-INJECTION       |           |    API REST (FastAPI)    |
|   HTTP hook avant prompt   |           |    + WebSockets/SSE     |
|   Injection contexte 70ms  |           |    + CLI (mem)           |
+--------------+-------------+           +--------------+-----------+
               |                                        |
+--------------v----------------------------------------v-----------+
|                     MOTEUR COGNITIF                                |
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  | Secteur          |  | Secteur          |  | Secteur          | |
|  | EPISODIQUE       |  | SEMANTIQUE       |  | PROCEDURAL       | |
|  | (événements)     |  | (faits)          |  | (skills)         | |
|  +------------------+  +------------------+  +------------------+ |
|  +------------------+  +------------------+                       |
|  | Secteur          |  | Secteur          |                       |
|  | EMOTIONNEL       |  | REFLEXIF         |                       |
|  +------------------+  +------------------+                       |
+----------------------------+--------------------------------------+
                             |
+----------------------------v--------------------------------------+
|                  PIPELINE D'INGESTION (Write)                     |
|  1. Embedding du contenu                                          |
|  2. Extraction entités nommées + métadonnées                      |
|  3. Détection émotions/croyances                                  |
|  4. Construction arêtes graphe d'entités                          |
|  5. Contrôle cohérence (Sheaf Cohomology)                         |
|  6. Filtrage entropie + score confiance bayésien                  |
+----------------------------+--------------------------------------+
                             |
+----------------------------v--------------------------------------+
|              MOTEUR DE RETRIEVAL (4 canaux parallèles)            |
|                                                                   |
|  [Sémantique]    [BM25]    [Graphe]      [Temporel]              |
|  Fisher-Rao      Okapi     PageRank/     valid_from/to           |
|  + variance      lexical   Spreading     fenêtres                |
|                            Activation    temporelles              |
|                                                                   |
|  ---------> WRRF Fusion ---------> Cross-Encoder Rerank -------> |
+----------------------------+--------------------------------------+
                             |
+----------------------------v--------------------------------------+
|                    COUCHE STOCKAGE                                 |
|                                                                   |
|  +----------------+  +-----------------+  +--------------------+  |
|  | SQLite + FTS5  |  | ChromaDB        |  | Fichiers Markdown  |  |
|  | + WAL          |  | (embeddings)    |  | + Git versioning   |  |
|  | memory.db      |  |                 |  | MEMORY.md (index)  |  |
|  | learning.db    |  |                 |  |                    |  |
|  +----------------+  +-----------------+  +--------------------+  |
|                                                                   |
|  +-------------------------------------------------------------+ |
|  | VAULTS (Isolation)                                           | |
|  | vault-project-A/  |  vault-project-B/  |  vault-personal/   | |
|  | (index + data)    |  (index + data)    |  (index + data)    | |
|  +-------------------------------------------------------------+ |
+-------------------------------------------------------------------+
                             |
+----------------------------v--------------------------------------+
|              MOTEUR DE VITALITE (Decay/Consolidation)             |
|                                                                   |
|  - Dynamique de Langevin (Boule de Poincaré)                     |
|  - Activation MINERVA 2 (cubique) pour résurrection              |
|  - Modèle ACT-R pour le déclin naturel                            |
|  - Event Bus: memory.created, memory.accessed, agent.connected   |
+-------------------------------------------------------------------+
```

---

## 4. PLAN DE PROJET PROPOSE

### Phase 1 - Fondations (MVP)
1. **Serveur MCP** : squelette Python/FastAPI avec outils `add`, `search`, `list`, `delete`
2. **SQLite + FTS5** : stockage mémoires avec metadata, tags, timestamps
3. **ChromaDB** : embeddings locaux via Sentence-Transformers
4. **Recherche hybride** : sémantique + BM25, fusion RRF basique
5. **Vaults** : isolation par dossier/namespace
6. **Index MEMORY.md** : table des matières compressée auto-générée

### Phase 2 - Intelligence cognitive
7. **Secteurs cognitifs** : classification auto des mémoires (épisodique/sémantique/procédural)
8. **Graphe de connaissances** : NetworkX + PageRank + Leiden
9. **Retrieval 4 canaux** : ajout canal graphe + canal temporel
10. **WRRF + Cross-Encoder** : reranking neural
11. **Hook pré-injection** : injection contexte avant prompt agent

### Phase 3 - Vitalité et sécurité
12. **Moteur de déclin** : ACT-R / MINERVA 2, consolidation adaptative
13. **Détection contradictions** : Sheaf Cohomology ou heuristique simplifiée
14. **Score confiance bayésien** : par agent, défense anti-empoisonnement
15. **Séparation RGPD** : `memory.db` vs `learning.db`

### Phase 4 - Polish et intégrations
16. **CLI complète** : `mem add`, `mem recall`, `mem status`, `mem prune`
17. **Dashboard web** : visualisation graphe, stats, santé mémoire
18. **Multi-clients** : connexion Claude Desktop, Cursor, Windsurf
19. **Ollama** : mode full-local sans aucun appel cloud
20. **Git sync** : versioning automatique des Markdown

---

## 5. PROJETS DE REFERENCE

| Projet | Force clé |
|--------|-----------|
| **OpenMemory** | Modèle cognitif 5 secteurs + graphe temporel |
| **Ori-Mnemos** | Vitalité ACT-R + Markdown natif + PageRank |
| **SuperLocalMemory V3** | Fisher-Rao + Sheaf Theory + sécurité bayésienne |
| **CtxVault** | Isolation topologique stricte (Vaults) |
| **Lucid-Memory** | Rust + MINERVA 2 + Gist compression |
| **zer0dex** | Double couche index compressé + Hook pré-injection |
| **Mem0** | Production-ready, 26% improvement LLM-as-Judge, 90% token reduction |
| **A-MEM** | Zettelkasten dynamique, mises à jour rétroactives (NeurIPS 2025) |
| **Graphiti (Zep)** | Knowledge graph temporel Neo4j, P95 300ms, zero LLM au retrieval |
| **MemOS v2** | Multi-modal (texte/image/tool traces), +43.7% accuracy vs OpenAI Memory |
| **Mnemosyne** | Graph-structured, 65.8% win rate vs baseline RAG |
| **LightMem** | Atkinson-Shiffrin 3 stages, sleep-time consolidation (ICLR 2026) |
| **DiffMem** | Git-based memory storage, branching/merging natif |

---

# PARTIE 2 - RECHERCHE COMPLEMENTAIRE
## Au-delà du NotebookLM : techniques avancées, fonctionnalités innovantes, écosystème 2025-2026

---

## 6. TECHNIQUES DE COMPRESSION MEMOIRE AVANCEES

### Au-delà du Gist Compression

| Technique | Principe | Performance |
|-----------|----------|-------------|
| **AdmTree** (NeurIPS 2025) | Arbre sémantique adaptatif avec gist tokens, segmentation par densité d'information | 3.3-3.4x inference plus rapide, +10% vs SOTA |
| **MemWalker** | Arbre de noeuds résumés, navigation hiérarchique à la requête | Localisation sans fine-tuning |
| **ReadAgent** | 3 étapes : pagination + gisting + look-up interactif | Compression progressive |
| **KVzip** | Compression KV cache intelligente, élimination redondances | 3-4x compression mémoire |
| **DMC** (Dynamic Memory Compression) | Ratios de compression appris par tête d'attention | Jusqu'à 7x throughput sur H100 |
| **PISCO** | Distillation de connaissances, zero pretraining | 16x compression, 0-3% perte accuracy |
| **SARA** | Représentation 2 niveaux : snippets fins + vecteurs compressés | +13-18 points answer relevance |
| **500xCompressor** | Soft prompts continus entraînables | Jusqu'à 480x ratio compression |
| **LLMLingua** | Compression de prompts dynamique | 20x compression, 70-94% savings |

### Compression de contexte - Patterns clés
- **Selective Expansion** : ne décompresser que les segments à haute nouveauté (SARA)
- **Mean-Pooling Architecture** : surpasse les approches par compression-token (CCF)
- **KV-Distillation** : student-teacher avec divergence KL pour sélection de tokens

---

## 7. MEMOIRE BASEE GRAPHE - GENERATION 2025

### GraphRAG et au-delà

| Système | Innovation | Impact |
|---------|-----------|--------|
| **A-MEM** (NeurIPS 2025) | Zettelkasten agentic : notes avec keywords/tags/descriptions, liens dynamiques par embedding + LLM reasoning | Mises à jour rétroactives des contextes existants |
| **Graphiti (Zep AI)** | Knowledge graph temporel dans Neo4j, hybrid search (semantic + BM25 + graph traversal), zero LLM au retrieval | P95 latence 300ms (compatible voix) |
| **MemoTime** | Tree of Time hiérarchique + opérateurs temporels monotones + mémoire d'expérience auto-évolutive | +24% vs baselines, Qwen3-4B = GPT-4-Turbo |
| **LightRAG** | Retrieval dual-level efficace | 10x réduction tokens vs GraphRAG standard |
| **AriGraph** | Graphe sémantique + sommets épisodiques | Raisonnement en jeux textuels |
| **MAGMA** | Multi-graphes agentic | Raisonnement long-horizon structuré |
| **Trainable Graph Memory** | Trajectoires agent → chemins décisionnels + meta-cognition RL | Stratégie interprétable |

### Dégradation temporelle documentée
- Le GraphRAG standard perd **16.6% d'accuracy** sur les requêtes time-sensitive
- Les temporal knowledge graphs avec quadruples (fait + timestamp) corrigent ce problème
- `valid_from`/`valid_to` + reconstruction d'état à un instant T

---

## 8. RETRIEVAL AVANCE - PATTERNS 2025-2026

### RAG de nouvelle génération

| Pattern | Mécanisme | Cas d'usage |
|---------|-----------|-------------|
| **CRAG** (Corrective RAG) | Évaluateur de confiance → Correct/Incorrect/Ambigu → web search fallback | Robustesse anti-hallucination |
| **Self-RAG** | Boucle introspective, auto-évaluation de pertinence pendant la génération | Raffinement itératif |
| **Agentic RAG** | Agent multi-steps avec sélection d'outils, réflexion, adaptation | Tâches complexes |
| **Adaptive RAG** | Analyse query → skip retrieval si simple, multi-canal si complexe | Efficacité dynamique |
| **RAPTOR** | Clustering hiérarchique + résumés récursifs | Raisonnement cross-chunk |
| **Modular RAG** | Composants interchangeables : retrievers, rerankers, generators | Architecture pluggable |

### Recherche hybride avancée

| Modèle | Type | Force |
|--------|------|-------|
| **ColBERTv2** | Late interaction token-level | 6-10x réduction espace vs ColBERT original |
| **SPLADE** | Sparse neuronal appris | Expansion de termes + index inversé (vitesse BM25) |
| **SPLATE** | Sparse late interaction | CPU-deployable, <10ms filtrage candidats |
| **Dynamic Alpha Tuning** (2025) | Pondération hybride per-query | +2-7.5% Precision@1, MRR@20 |
| **Learned Sparse Retrieval** | Pénalisation termes fréquents | 10x réduction latence, production-ready Solr/OpenSearch |

### Query Understanding

| Technique | Principe |
|-----------|----------|
| **HyDE** | LLM génère document hypothétique → embedding → retrieval par voisinage |
| **Tree of Thoughts** | Arbre de séquences cohérentes avec BFS/DFS, lookahead/backtracking |
| **Step-Back Prompting** | Génération d'abstractions avant résolution détaillée |
| **RT-RAG** | Décomposition en arbres de raisonnement, traversée bottom-up |

### Reranking - Comparatif

| Stratégie | Latence | Coût/query | Force |
|-----------|---------|-----------|-------|
| **Cross-Encoder** | 1-2ms | $0.001-0.01 | Baseline production, bat les LLMs |
| **Cohere Rerank** | ~5ms | variable | 100+ langues, standard industrie |
| **Listwise** | 4-6s | $0.10-1.00 | +5-8% accuracy vs pointwise |
| **LLM-as-Judge** (JudgeRank) | 4-6s | $0.10-1.00 | Meilleur sur tâches de raisonnement |
| **Mixture of Prompts** (MoPs) | variable | variable | Modules spécialisés par type d'input |

### Optimisation fenêtre de contexte

- **Lost-in-the-Middle** : performance en U → placer les docs importants en début/fin
- **MS-PoE** (Multi-Scale Positional Encoding) : +20-40% accuracy positions centrales
- **Dual-Stage Retrieval** : broad recall (20-100 candidats) → cross-encoder → 3-5 docs finaux
- **SARA** : expansion sélective via score de nouveauté d'embedding

---

## 9. FONCTIONNALITES INNOVANTES (AU-DELA DU NOTEBOOK)

### F10 - Mémoire multi-modale
- **MemOS v2.0** : texte + images + tool traces + personas, retrieval unifié
  - +43.7% accuracy vs OpenAI Memory, 72% tokens en moins
  - Opérations asynchrones, latence milliseconde
- **EBind** : binding d'espaces d'embedding multi-modaux (image/video/audio/3D) surpasse des modèles 4-17x plus gros

### F11 - Mémoire collaborative avec contrôle d'accès
- **Collaborative Memory Framework** (ICML 2025) :
  - Dual-memory : fragments privés + fragments partagés sélectivement
  - Graphe bipartite pour contraintes d'accès (users ↔ agents ↔ resources)
  - Politiques read/write avec vues filtrées par permissions
  - Droits asymétriques évoluant dans le temps
  - Provenance immuable (timestamps, agents contributeurs)

### F12 - Auto-réflexion et auto-amélioration de la mémoire
- **MemRL** (Jan 2026) : RL runtime, Q-values appris pour différencier stratégies haute-valeur du bruit sémantique
- **SAGE** : courbe d'oubli d'Ebbinghaus pour prioriser dynamiquement (+2.26x improvement)
- **ACE** (Agentic Context Engineering) : Generator-Reflector-Curator, playbooks évolutifs (+10.6% AppWorld)
- **Nemori** : auto-organisation inspirée Event Segmentation Theory + Free-Energy Principle

### F13 - Mémoire émotionnelle et sociale
- Tracking émotionnel multi-granularité (dialogue-level, turn-level, first-spike)
- Mémoire associative inter-agents : "amitiés" = clusters de mémoires épisodiques positives
- Risque identifié : "sycophanie émotionnelle" (validation de narratifs maladaptés)

### F14 - Versioning Git-like de la mémoire
- **Git-Context-Controller (GCC)** : COMMIT, BRANCH, MERGE, CONTEXT pour la mémoire d'agent
  - 48% bug resolution SWE-Bench (vs 26 systèmes compétitifs)
  - Transforme le contexte en workspace navigable et persistant
- **AgentGit** : state commit, revert, branching sur LangGraph
- **DiffMem** : stockage Git natif avec branching (ex: timelines mensuelles)

### F15 - Mémoire proactive (anticipation)
- **Predict-Calibrate Loop** (Nemori) : les écarts de prédiction déclenchent l'intégration de nouvelles connaissances
- Hook de pré-injection HTTP automatique (zer0dex) : contexte injecté avant que l'agent ne réfléchisse
- Réduction 30-60% des appels API LLM par minimisation du contexte redondant

### F16 - Consolidation par "sommeil" (Sleep Mechanisms)
- **LightMem** (ICLR 2026) : Atkinson-Shiffrin 3 stages (sensoriel → court-terme → long-terme)
  - Sleep-time update : consolidation offline
- **Mnemosyne** : filtres substance/redondance, pruning temporel, résumé concentré
  - 65.8% win rate vs 31.1% baseline RAG
- Distillation transférant les connaissances in-context vers les paramètres du modèle

### F17 - Privacy-preserving memory
- **DP-FedLoRA** : adaptation LoRA locale + injection de bruit calibré + norm clipping
- **Hensel's Compression** : Lemme de Hensel + differential privacy (réduction significative ressources)
- **Chiffrement local** : SQLite + WAL isolé, zero exposition réseau
- Arsenal : Differential Privacy, Federated Learning, Homomorphic Encryption, SMPC

---

## 10. ECOSYSTEME MCP & ALTERNATIVES VECTORIELLES

### Serveurs MCP mémoire additionnels

| Serveur | Approche |
|---------|----------|
| **Knowledge Graph Memory (Anthropic officiel)** | Entity-relation-observation, SQLite + RRF |
| **Qdrant MCP Server** | Intégration vectorielle HNSW officielle |
| **Chroma MCP** | 4 modes déploiement, 6 providers d'embedding, HNSW + BM25 |
| **Memory MCP (Puliczek)** | BGE-M3 via Cloudflare Workers AI, dual-store (Vectorize + D1) |
| **Memory Bank MCP** | Remote memory, isolation + coordination centralisée |

### Modèles d'embedding - Comparatif local

| Modèle | Params | Dims | Latence (ms/1K) | Accuracy Top-5 | Sweet spot |
|--------|--------|------|-----------------|----------------|------------|
| **MiniLM-L6-v2** | 22M | 384 | **14.7** | 78.1% | Edge, haut volume, chatbots |
| **E5-Base-v2** | 110M | 768 | 20.2 | 83.5% | Balanced production |
| **BGE-Base-v1.5** | 110M | 768 | 22.5 | 84.7% | Meilleur accuracy mid-tier |
| **BGE-M3** | 335M | 1024 | 28-35 | 72% retrieval BEIR | Multilingue, meilleur retrieval |
| **Nomic Embed v1** | ~500M | 768 | 41.9 | **86.2%** | Précision max (légal, médical) |

### Bases vectorielles locales - Comparatif 2025

| DB | Architecture | Performance | Forces | Limites |
|----|-------------|-------------|--------|---------|
| **sqlite-vec** | Pure C, zero deps | **1ms build, 17ms query** (1M/128-dim) | Ultra-portable (WASM, RPi), brute-force SQL | Pas d'index approché |
| **LanceDB** | Apache Arrow, serverless | Petabyte-scale, zero-copy | Multi-modal, hybrid search, auto-scale to zero | Jeune écosystème |
| **ChromaDB** | HNSW + BM25 | Production-ready | 4 modes, 6 embedding providers, MCP intégré | Scaling limité |
| **Milvus Lite** | Python embedded | Same API que Milvus distribué | Dense + sparse + hybrid | <1M vecteurs, pas de RBAC |
| **DuckDB VSS** | HNSW extension | 741ms index, 46ms query | Forces OLAP | Médiocre sur gros dims (3072+) |
| **Turbopuffer** | S3 natif, Rust | 8ms cached, 343ms uncached | 2.5T+ docs, 10x moins cher | Cloud-first (pas full local) |

---

## 11. SECURITE & MENACES DOCUMENTEES (2025)

### Attaques identifiées

| Attaque | Mécanisme | Impact |
|---------|-----------|--------|
| **MemoryGraft** | Injection indirecte via expériences empoisonnées (imitation sémantique) | Corruption de la base d'expérience |
| **Sleeper Agents** | Comportement normal → injection lente de fausses croyances | 73% succès exploit calendrier (Lakera) |
| **Propagation multi-agents** | 1 agent empoisonné contamine 87% des décisions downstream en 4h | Effondrement systémique |

### Défenses (SuperLocalMemory Trust Framework)

- **Score Beta-Binomial bayésien** : +0.01/0.02 par action positive, -0.02/0.03 par négative
- **Trust separation gap** : 0.90 entre agents bénins/malveillants
- **Seuil d'écriture** : trust < 0.3 → blocage writes/deletes
- **Provenance tracking** : créateur, protocole source, timestamp, historique modifications
- **Isolation architecturale** : SQLite local, zero cloud, WAL concurrence
- **Conformité RGPD** : données comportementales isolées dans `learning.db`, Article 17

---

## 12. EVALUATION & BENCHMARKS

### Frameworks d'évaluation

| Framework | Type | Métriques clés |
|-----------|------|---------------|
| **RAGAS** | Reference-free | Context Precision, Context Recall, Faithfulness, Answer Relevancy |
| **DeepEval** | Pytest-compatible | 14+ métriques, self-explaining, debug verbose |
| **MTEB/MMTEB** | Benchmark embeddings | 500+ tâches, 250+ langues |
| **MemoryAgentBench** (ICLR 2026) | Cognitif | Retrieval accuracy, Test-Time Learning, Long-Range, Selective Forgetting |
| **Reflection-Bench** (ICML 2025) | Psychologie cognitive | 7 tâches : oddball, n-back, Wisconsin card sorting, Iowa gambling... |

### Métriques recommandées pour notre projet

1. **Precision@k** : fraction de mémoires pertinentes dans le top-k récupéré
2. **Recall@k** : proportion d'information ground-truth capturée
3. **Faithfulness** : cohérence entre contexte récupéré et réponse générée
4. **Token Efficiency** : ratio information utile / tokens consommés
5. **Latence P50/P95** : temps de retrieval (cible : <50ms P50, <200ms P95)
6. **Memory Decay Accuracy** : les bonnes mémoires survivent-elles au déclin ?
7. **Contradiction Detection Rate** : taux de détection de faits contradictoires

---

## 13. PLAN DE PROJET ENRICHI (v2)

### Phase 1 - Fondations (MVP)
1. Serveur MCP Python avec outils `add`, `search`, `list`, `delete`
2. **sqlite-vec** pour les embeddings (ultra-rapide, zero deps) + SQLite FTS5 pour BM25
3. Modèle d'embedding : **BGE-Base-v1.5** (meilleur ratio accuracy/latence)
4. Recherche hybride : sémantique + BM25, fusion RRF
5. Vaults : isolation par namespace
6. Index MEMORY.md compressé auto-généré
7. CLI basique : `mem add`, `mem search`, `mem list`

### Phase 2 - Retrieval intelligent
8. **HyDE** : génération document hypothétique pour enrichir les requêtes
9. **Adaptive RAG** : skip retrieval si simple, multi-canal si complexe
10. **Cross-Encoder reranking** (production baseline)
11. Hook pré-injection HTTP (injection ~70ms avant prompt)
12. **Query decomposition** : Tree of Thoughts pour requêtes multi-hop

### Phase 3 - Graphe & cognition
13. Graphe de connaissances temporel (style Graphiti/A-MEM)
14. Secteurs cognitifs : épisodique/sémantique/procédural
15. Retrieval 4 canaux parallèles + WRRF fusion
16. **Zettelkasten dynamique** : notes avec keywords/tags, liens auto-générés
17. Détection contradictions (heuristique puis Sheaf Cohomology)

### Phase 4 - Vitalité & apprentissage
18. Moteur de déclin ACT-R / Ebbinghaus
19. **Sleep consolidation** : consolidation offline périodique (style LightMem)
20. **Auto-réflexion** : l'agent review et réorganise ses propres mémoires (style MemRL)
21. Score confiance bayésien par agent
22. Séparation RGPD : `memory.db` vs `learning.db`

### Phase 5 - Fonctionnalités avancées
23. **Versioning Git-like** : commit/branch/merge de la mémoire (style GCC)
24. **Mémoire collaborative** : fragments privés + partagés, graphe bipartite accès
25. **Mémoire multi-modale** : images, code snippets, tool traces
26. **Mémoire proactive** : predict-calibrate loop, anticipation contexte
27. Dashboard web : visualisation graphe, timeline, stats santé

### Phase 6 - Production & sécurité
28. Défenses anti-empoisonnement (provenance tracking, seuils trust)
29. Chiffrement local + zero network exposure
30. Benchmarks intégrés : RAGAS metrics + latence P50/P95
31. Multi-clients : Claude Desktop, Cursor, Windsurf, VS Code
32. Mode full-local : Ollama + embeddings locaux, zero cloud

---

## 14. SOURCES & REFERENCES

### Papers clés
- AdmTree (NeurIPS 2025) - arxiv.org/abs/2512.04550
- A-MEM (NeurIPS 2025) - arxiv.org/abs/2502.12110
- MemRL (Jan 2026) - arxiv.org/abs/2601.03192
- LightMem (ICLR 2026) - arxiv.org/abs/2510.18866
- MemoryAgentBench (ICLR 2026) - arxiv.org/abs/2507.05257
- Collaborative Memory (ICML 2025) - arxiv.org/abs/2505.18279
- Nemori (Aug 2025) - arxiv.org/abs/2508.03341
- Git-Context-Controller - arxiv.org/abs/2508.00031
- Graphiti (Zep) - arxiv.org/abs/2501.13956
- MemoTime - arxiv.org/abs/2510.13614
- SARA Context Compression - emergentmind.com/topics/context-compression
- PISCO (ACL 2025) - aclanthology.org/2025.findings-acl.800.pdf
- ColBERTv2 - arxiv.org/abs/2112.01488
- HyDE - arxiv.org/abs/2212.10496
- Mem0 - arxiv.org/abs/2504.19413
- SuperLocalMemory Trust - arxiv.org/html/2603.02240
- MemoryGraft Attack - arxiv.org/html/2512.16962v1

### Projets GitHub
- sqlite-vec - github.com/asg017/sqlite-vec
- Chroma MCP - github.com/chroma-core/chroma-mcp
- MemOS - github.com/MemTensor/MemOS
- DiffMem - github.com/Growth-Kinetics/DiffMem
- LLMLingua - github.com/microsoft/LLMLingua
- Ori-Mnemos - github.com/aayoawoyemi/Ori-Mnemos

### Benchmarks & évaluation
- RAGAS - docs.ragas.io
- DeepEval - deepeval.com
- MTEB Leaderboard - huggingface.co/spaces/mteb/leaderboard
- MMTEB (500+ tâches, 250+ langues) - arxiv.org/abs/2502.13595
