# Configuration

[< Retour a l'index](index.md)

---

Fougasse se configure via un fichier TOML et/ou des variables d'environnement.

## Fichier de configuration

Emplacement : `~/.fougasse/config.toml`

Ce fichier est **optionnel**. Toutes les valeurs ont des defauts raisonnables.

### Exemple complet

```toml
[paths]
data_dir = "~/.fougasse"
db_path = "~/.fougasse/memory.db"
learning_db_path = "~/.fougasse/learning.db"
models_dir = "~/.fougasse/models"

[embeddings]
model_name = "BAAI/bge-base-en-v1.5"
embedding_dim = 768

[search]
max_results = 10
rrf_k = 60
similarity_threshold = 0.35

[vaults]
default_vault = "default"

[vitality]
vitality_decay_d = 0.5
vitality_archive_threshold = 0.1
vitality_schedule_hours = 6

[contradiction]
contradiction_similarity_threshold = 0.85

[reranker]
reranker_enabled = false
reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
reranker_top_k = 20

[server]
server_name = "Fougasse"
server_transport = "stdio"
server_host = "127.0.0.1"
server_port = 8765

[limits]
max_content_size = 102400
max_tags_per_memory = 20
max_tag_length = 64
```

## Reference des parametres

### Chemins

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `data_dir` | Path | `~/.fougasse` | Dossier racine des donnees |
| `db_path` | Path | `~/.fougasse/memory.db` | Chemin de la base de donnees principale |
| `learning_db_path` | Path | `~/.fougasse/learning.db` | Base comportementale (separee pour [RGPD](securite.md#conformite-rgpd)) |
| `models_dir` | Path | `~/.fougasse/models` | Cache local du modele d'[embedding](embeddings.md) |

### Embeddings

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `model_name` | str | `BAAI/bge-base-en-v1.5` | Modele sentence-transformers. Voir [Embeddings](embeddings.md) |
| `embedding_dim` | int | `768` | Dimension des vecteurs. Doit correspondre au modele |

### Recherche

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `max_results` | int | `10` | Nombre max de resultats par defaut |
| `rrf_k` | int | `60` | Parametre k du [RRF](recherche-hybride.md#fusion-rrf). Plus eleve = scores plus lisses |
| `similarity_threshold` | float | `0.35` | Seuil minimum de similarite vectorielle |

### Vaults

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `default_vault` | str | `default` | Vault utilise quand aucun n'est specifie. Voir [Vaults](vaults.md) |

### Vitalite

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `vitality_decay_d` | float | `0.5` | Exposant du [declin ACT-R](vitalite.md#modele-act-r). Plus eleve = oubli plus rapide |
| `vitality_archive_threshold` | float | `0.1` | Score sous lequel une memoire est [archivee](vitalite.md#archivage-automatique) |
| `vitality_schedule_hours` | int | `6` | Intervalle du [scheduler](vitalite.md#scheduler-periodique) de vitalite (en heures) |

### Detection de contradictions

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `contradiction_similarity_threshold` | float | `0.85` | Seuil de similarite pour declencher la [detection](contradictions.md) |

### Reranker

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `reranker_enabled` | bool | `false` | Activer le [cross-encoder reranking](recherche-hybride.md#reranking-optionnel) |
| `reranker_model` | str | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Modele cross-encoder |
| `reranker_top_k` | int | `20` | Nombre de candidats a reranker |

### Serveur

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `server_name` | str | `Fougasse` | Nom du serveur MCP |
| `server_transport` | str | `stdio` | Transport : `stdio` (recommande) ou `sse` |
| `server_host` | str | `127.0.0.1` | Hote pour SSE (localhost uniquement par [securite](securite.md)) |
| `server_port` | int | `8765` | Port pour SSE |

### Limites

| Parametre | Type | Defaut | Description |
|-----------|------|--------|-------------|
| `max_content_size` | int | `102400` | Taille max d'un contenu memoire (100 Ko) |
| `max_tags_per_memory` | int | `20` | Nombre max de tags par memoire |
| `max_tag_length` | int | `64` | Longueur max d'un tag |

## Variables d'environnement

Chaque parametre peut etre surcharge par une variable d'environnement prefixee `FOUGASSE_` :

```bash
export FOUGASSE_MAX_RESULTS=25
export FOUGASSE_DEFAULT_VAULT=work
export FOUGASSE_RERANKER_ENABLED=true
export FOUGASSE_DB_PATH=/tmp/test-fougasse.db
```

**Priorite** : variable d'environnement > fichier TOML > valeur par defaut.

Les types sont convertis automatiquement :
- `Path` : interprete comme chemin
- `bool` : `true`, `1`, `yes` → True
- `int` / `float` : conversion numerique
- `str` : tel quel

---

**Voir aussi** : [Installation](installation.md) | [Outils MCP](mcp-tools.md) | [Vaults](vaults.md)
