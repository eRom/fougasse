# Outils MCP

[< Retour a l'index](index.md)

---

Fougasse expose 5 outils via le protocole MCP (Model Context Protocol). Ces outils sont appeles par les LLM clients (Claude Code, Cursor, Windsurf, etc.) pour interagir avec la memoire.

## fougasse_remember

**Stocker un nouveau souvenir.**

Le LLM appelle cet outil pour memoriser une information. Fougasse genere un [embedding](embeddings.md), stocke dans SQLite + [sqlite-vec](modele-donnees.md), indexe dans [FTS5](recherche-hybride.md#canal-2--bm25-fts5), et retourne l'ID.

### Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| `content` | string | oui | — | Contenu textuel a memoriser (max 100 Ko) |
| `type` | string | non | `"text"` | Type : `text`, `code`, `task`, `appointment`, `idea`, `conversation`, `topic` |
| `tags` | list[string] | non | `[]` | Tags de categorisation (max 20, alphanumeriques) |
| `vault_id` | string | non | `"default"` | [Vault](vaults.md) de destination |
| `source_agent` | string | non | `null` | Identifiant du client appelant (ex: `"claude-code"`) |
| `metadata` | object | non | `null` | Metadonnees cle-valeur libres |

### Retour

```json
{
  "status": "stored",
  "id": "e8ee0fe1-f242-4633-b5bb-c4d3b1656107",
  "type": "topic",
  "vault_id": "default",
  "tags": ["python", "architecture"],
  "created_at": "2026-03-18T08:23:28.427452+00:00"
}
```

### Comportement

1. Validation des inputs via Pydantic (taille content, format tags, vault_id)
2. Generation d'un UUID pour la memoire
3. Insertion dans la table `memories` + `tags` + `fts_memories`
4. Generation de l'[embedding](embeddings.md) via BGE-Base
5. Insertion du vecteur dans `vec_memories` ([sqlite-vec](modele-donnees.md#recherche-vectorielle))
6. Retour de l'ID et du statut

### Erreurs possibles

| Erreur | Cause |
|--------|-------|
| `Invalid type` | Type non reconnu |
| Validation Pydantic | Content vide, tags trop longs, vault_id invalide |

---

## fougasse_recall

**Retrouver des souvenirs pertinents.**

C'est le coeur de Fougasse. Le LLM envoie une requete en langage naturel, et Fougasse execute une [recherche hybride](recherche-hybride.md) multi-canaux pour retrouver les memoires les plus pertinentes.

### Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| `query` | string | oui | — | Requete en langage naturel |
| `vault_id` | string | non | `null` | Filtrer par [vault](vaults.md) (null = tous les vaults) |
| `type_filter` | string | non | `null` | Filtrer par type (`text`, `code`, `task`, etc.) |
| `tags_filter` | list[string] | non | `null` | Filtrer par tags |
| `limit` | int | non | `10` | Nombre max de resultats (1-100) |

### Retour

```json
{
  "results": [
    {
      "id": "e8ee0fe1-...",
      "content": "Romain a cree Fougasse...",
      "type": "topic",
      "tags": ["fougasse", "python"],
      "vault_id": "default",
      "source_agent": "claude-code",
      "score": 0.041,
      "match_sources": ["semantic", "bm25", "temporal"],
      "created_at": "2026-03-18T08:23:28"
    }
  ],
  "total_count": 1,
  "search_time_ms": 479.48
}
```

### Canaux de recherche

La recherche combine jusqu'a 4 canaux (voir [Recherche hybride](recherche-hybride.md)) :

1. **Semantique** — KNN vectoriel via [sqlite-vec](recherche-hybride.md#canal-1--semantique-knn)
2. **BM25** — Recherche plein texte via [FTS5](recherche-hybride.md#canal-2--bm25-fts5)
3. **Graphe** — [Spreading activation](recherche-hybride.md#canal-3--graphe) dans le [graphe de connaissances](graphe-connaissances.md)
4. **Temporel** — Boost de [recence](recherche-hybride.md#canal-4--temporel)

Les scores sont fusionnes via [RRF](recherche-hybride.md#fusion-rrf), puis optionnellement [rerankes](recherche-hybride.md#reranking-optionnel).

### Champ `match_sources`

Indique quels canaux ont contribue au resultat :
- `"semantic"` — trouve par similarite vectorielle
- `"bm25"` — trouve par correspondance de mots-cles
- `"graph"` — trouve via le graphe de connaissances
- `"temporal"` — booste par recence
- `"reranked"` — reordonne par cross-encoder

---

## fougasse_forget

**Supprimer un souvenir.**

### Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| `memory_id` | string | oui | — | UUID de la memoire a supprimer |
| `hard` | bool | non | `false` | `true` = suppression definitive, `false` = archivage (soft-delete) |

### Retour

```json
{
  "status": "archived",
  "memory_id": "e8ee0fe1-..."
}
```

### Comportement

- **Soft-delete** (defaut) : met `is_archived = 1`. La memoire n'apparait plus dans les recherches mais reste en base. Elle peut etre [ressuscitee](vitalite.md#resurrection).
- **Hard-delete** (`hard=true`) : suppression definitive de la memoire, de ses tags, de son vecteur, et de son index FTS. Irreversible.

> **Securite** : si la memoire est un [point d'articulation](graphe-connaissances.md#protection-tarjan) du graphe, un warning est emis.

### Erreurs possibles

| Erreur | Cause |
|--------|-------|
| `Memory not found` | ID inexistant |

---

## fougasse_status

**Consulter l'etat du serveur.**

### Parametres

Aucun.

### Retour

```json
{
  "version": "0.1.0",
  "memory_count": 42,
  "vault_count": 3,
  "active_memories": 38,
  "archived_memories": 4,
  "db_size_bytes": 2097152,
  "uptime_seconds": 3600.5
}
```

| Champ | Description |
|-------|-------------|
| `version` | Version de Fougasse |
| `memory_count` | Nombre total de memoires (actives + archivees) |
| `vault_count` | Nombre de [vaults](vaults.md) |
| `active_memories` | Memoires non archivees |
| `archived_memories` | Memoires archivees (soft-deleted ou declinantes) |
| `db_size_bytes` | Taille du fichier `memory.db` |
| `uptime_seconds` | Temps depuis le demarrage du serveur |

---

## fougasse_vaults

**Gerer les vaults (namespaces d'isolation).**

Voir la documentation detaillee des [Vaults](vaults.md).

### Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| `action` | string | non | `"list"` | Action : `list`, `create`, `delete` |
| `name` | string | non | `null` | Nom du vault (requis pour `create` et `delete`) |
| `description` | string | non | `null` | Description (pour `create`) |

### Actions

#### `list` — Lister les vaults

```json
{
  "vaults": [
    {
      "id": "default",
      "name": "default",
      "description": "Default vault",
      "memory_count": 42,
      "created_at": "2026-03-18T07:59:47"
    }
  ]
}
```

#### `create` — Creer un vault

```json
// Appel : action="create", name="work", description="Projets professionnels"
{
  "status": "created",
  "vault_id": "work",
  "name": "work"
}
```

#### `delete` — Supprimer un vault

```json
// Appel : action="delete", name="old-project"
{
  "status": "deleted",
  "name": "old-project"
}
```

### Erreurs possibles

| Erreur | Cause |
|--------|-------|
| `name is required` | Action create/delete sans nom |
| `Vault already exists` | Tentative de creation d'un vault existant |
| `Cannot delete the default vault` | Tentative de suppression du vault par defaut |
| `Vault has N memories` | Tentative de suppression d'un vault non vide |

---

**Voir aussi** : [Recherche hybride](recherche-hybride.md) | [Vaults](vaults.md) | [CLI](cli.md) | [Embeddings](embeddings.md)
