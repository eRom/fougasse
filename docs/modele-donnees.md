# Modele de donnees

[< Retour a l'index](index.md)

---

Fougasse stocke tout dans un seul fichier SQLite (`~/.fougasse/memory.db`) avec WAL mode, foreign keys, et trois extensions : FTS5, sqlite-vec, et des migrations versionnees.

## Schema conceptuel

```
memories ──1:N── tags
    |
    1:N── memory_versions
    |
    1:1── vec_memories (embedding)
    |
    1:1── fts_memories (index plein texte)
    |
    N:1── vaults
    |
    1:N── access_log
    |
    1:1── graph_nodes (type='memory')
              |
              N:N── graph_edges ──N:N── graph_nodes (type='entity')
```

## Tables principales

### `memories`

Table centrale de toutes les memoires stockees.

| Colonne | Type | Defaut | Description |
|---------|------|--------|-------------|
| `id` | TEXT PK | — | UUID unique |
| `content` | TEXT NOT NULL | — | Contenu textuel (max 100 Ko) |
| `type` | TEXT NOT NULL | `'text'` | Type : text, code, task, appointment, idea, conversation, topic |
| `vault_id` | TEXT NOT NULL FK | `'default'` | Reference vers [vaults](vaults.md) |
| `source_agent` | TEXT | NULL | Identifiant de l'agent source (provenance) |
| `metadata` | TEXT (JSON) | NULL | Metadonnees cle-valeur libres |
| `vitality_score` | REAL NOT NULL | 1.0 | Score de [vitalite ACT-R](vitalite.md#modele-act-r) |
| `access_count` | INTEGER NOT NULL | 0 | Nombre total d'acces |
| `is_archived` | INTEGER NOT NULL | 0 | 1 = soft-deleted / decline |
| `created_at` | TEXT NOT NULL | now() | ISO 8601 UTC |
| `updated_at` | TEXT NOT NULL | now() | ISO 8601 UTC |

**Index** : vault_id, type, is_archived, vitality_score, created_at

### `vaults`

Namespaces d'isolation. Voir [Vaults](vaults.md).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | TEXT PK | Identifiant (slug) |
| `name` | TEXT UNIQUE | Nom affichable |
| `description` | TEXT | Description optionnelle |
| `created_at` | TEXT | ISO 8601 UTC |

### `tags`

Relation many-to-many entre memoires et tags.

| Colonne | Type | Description |
|---------|------|-------------|
| `memory_id` | TEXT PK FK | Reference vers memories |
| `tag` | TEXT PK | Nom du tag (minuscules) |

**Index** : tag (pour les recherches par tag)

### `access_log`

Journal des acces pour le calcul de [vitalite](vitalite.md).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | — |
| `memory_id` | TEXT FK | Memoire accedee |
| `accessed_at` | TEXT | Timestamp de l'acces |

**Index** : memory_id

## Recherche vectorielle

### `vec_memories` (sqlite-vec)

Table virtuelle `vec0` pour la recherche KNN. Voir [Embeddings](embeddings.md).

| Colonne | Type | Description |
|---------|------|-------------|
| `memory_id` | TEXT | Reference vers memories |
| `vault_id` | TEXT | Pour le filtrage par [vault](vaults.md) |
| `is_archived` | INTEGER | Pour exclure les archives |
| `embedding` | float[768] | Vecteur normalise L2 |

**Recherche** : `WHERE embedding MATCH ? AND k = ? AND vault_id = ?`

## Recherche plein texte

### `fts_memories` (FTS5)

Table virtuelle FTS5 pour la recherche BM25. Voir [Recherche hybride](recherche-hybride.md#canal-2--bm25-fts5).

| Colonne | Type | Description |
|---------|------|-------------|
| `memory_id` | TEXT (UNINDEXED) | Reference vers memories |
| `content` | TEXT | Contenu indexe |
| `tags` | TEXT | Tags concatenes (espace-separes) |

**Recherche** : `WHERE fts_memories MATCH ?`

> La table FTS5 est **standalone** (pas content-sync) — elle est geree manuellement dans le code Python a chaque INSERT/UPDATE/DELETE.

## Graphe de connaissances

### `graph_nodes`

Noeuds du [graphe](graphe-connaissances.md). Voir aussi [PageRank](graphe-connaissances.md#pagerank) et [communautes](graphe-connaissances.md#detection-de-communautes).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | TEXT PK | UUID memoire ou `tag:<nom>` |
| `node_type` | TEXT NOT NULL | `'memory'` ou `'entity'` |
| `label` | TEXT NOT NULL | Texte affichable (content tronque ou nom du tag) |
| `pagerank` | REAL NOT NULL | Score PageRank (0.0 par defaut) |
| `community_id` | INTEGER | ID de la communaute detectee |
| `created_at` | TEXT | ISO 8601 UTC |

**Index** : node_type

### `graph_edges`

Aretes du graphe. Voir les [types de relations](graphe-connaissances.md#types-de-relations-aretes).

| Colonne | Type | Description |
|---------|------|-------------|
| `source_id` | TEXT PK FK | Noeud source |
| `target_id` | TEXT PK FK | Noeud cible |
| `relation` | TEXT PK | `relates_to`, `supersedes`, `conflicts_with`, `tagged_with` |
| `weight` | REAL NOT NULL | Force de la relation (0.0 a 1.0) |
| `created_at` | TEXT | ISO 8601 UTC |

**Index** : source_id, target_id, relation

## Historique des versions

### `memory_versions` (migration 003)

Historique des modifications de chaque memoire. Voir [Vitalite — consolidation](vitalite.md#consolidation).

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | TEXT PK | UUID de la version |
| `memory_id` | TEXT FK | Memoire parente |
| `content` | TEXT NOT NULL | Contenu a cette version |
| `metadata` | TEXT (JSON) | Metadonnees a cette version |
| `version_number` | INTEGER NOT NULL | Numero sequentiel |
| `created_at` | TEXT | ISO 8601 UTC |

**Index** : (memory_id, version_number)

## Scoring de confiance

### `agent_trust` (creation dynamique)

Scores de confiance par agent. Voir [Securite](securite.md#scoring-de-confiance-par-agent).

| Colonne | Type | Description |
|---------|------|-------------|
| `agent_id` | TEXT PK | Identifiant de l'agent |
| `alpha` | REAL NOT NULL | Evidence positive (defaut 1.0) |
| `beta` | REAL NOT NULL | Evidence negative (defaut 1.0) |

## Suivi des versions

### `schema_version`

Tracking des migrations appliquees.

| Colonne | Type | Description |
|---------|------|-------------|
| `version` | INTEGER PK | Numero de migration |
| `applied_at` | TEXT | Timestamp d'application |

## Migrations

Les migrations sont des fichiers SQL dans `migrations/` :

| Fichier | Version | Contenu |
|---------|---------|---------|
| `001_init.sql` | 1 | Tables principales, FTS5, index |
| `002_vitality.sql` | 2 | Index conditionnel sur vitality_score |
| `003_versioning.sql` | 3 | Table memory_versions |

Les migrations sont appliquees **automatiquement** au demarrage. Le systeme verifie `schema_version` et n'applique que les migrations manquantes.

## Pragmas SQLite

```sql
PRAGMA journal_mode=WAL;      -- Lectures concurrentes
PRAGMA foreign_keys=ON;        -- Integrite referentielle
PRAGMA busy_timeout=5000;      -- 5s de retry sur lock
```

## Donnees comportementales (RGPD)

La base `learning.db` ([configurable](configuration.md#chemins)) est separee de `memory.db` pour la conformite [RGPD](securite.md#conformite-rgpd) :

| Table | Contenu |
|-------|---------|
| `search_patterns` | Requetes de recherche + timestamps |
| `feedback` | Feedback utilisateur sur les memoires |

---

**Voir aussi** : [Configuration](configuration.md) | [Embeddings](embeddings.md) | [Recherche hybride](recherche-hybride.md) | [Graphe de connaissances](graphe-connaissances.md) | [Securite](securite.md)
