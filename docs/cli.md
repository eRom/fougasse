# Interface CLI

[< Retour a l'index](index.md)

---

Fougasse fournit une interface en ligne de commande pour l'administration et le monitoring. La CLI n'est **pas** destinee a l'usage quotidien (les LLM utilisent les [outils MCP](mcp-tools.md)) mais a la maintenance, l'export, et le diagnostic.

## Commandes disponibles

```bash
fougasse --version       # Afficher la version
fougasse --help          # Aide generale
fougasse <command> --help  # Aide sur une commande
```

---

## `fougasse status`

Afficher l'etat general de Fougasse.

```bash
fougasse status          # Tableau Rich
fougasse status --json   # Sortie JSON
```

### Sortie

| Metrique | Description |
|----------|-------------|
| `version` | Version installee |
| `db_path` | Chemin de la base de donnees |
| `memory_count` | Nombre total de memoires |
| `active_memories` | Memoires non archivees |
| `archived_memories` | Memoires [archivees](vitalite.md#archivage-automatique) |
| `vault_count` | Nombre de [vaults](vaults.md) |
| `db_size_bytes` | Taille du fichier DB |
| `db_size_mb` | Taille en Mo |

---

## `fougasse stats`

Statistiques detaillees.

```bash
fougasse stats           # Tableau Rich
fougasse stats --json    # Sortie JSON
```

### Sortie

| Metrique | Description |
|----------|-------------|
| `total_memories` | Total (actives + archivees) |
| `by_type` | Repartition par type (`text`, `code`, `task`, etc.) |
| `by_vault` | Repartition par [vault](vaults.md) |
| `graph_nodes` | Noeuds dans le [graphe de connaissances](graphe-connaissances.md) |
| `graph_edges` | Aretes dans le graphe |
| `top_tags` | Top 10 des tags les plus frequents |

---

## `fougasse vaults`

Lister les [vaults](vaults.md) existants.

```bash
fougasse vaults          # Tableau Rich
fougasse vaults --json   # Sortie JSON
```

Affiche pour chaque vault : ID, nom, nombre de memoires, description.

---

## `fougasse prune`

Nettoyer les memoires archivees.

```bash
fougasse prune           # Soft-delete definitif (confirmation requise)
fougasse prune --hard    # Hard-delete irreversible (confirmation requise)
fougasse prune --json    # Sortie JSON
```

### Options

| Option | Description |
|--------|-------------|
| `--hard` | Suppression permanente (au lieu de garder les archives) |
| `--json` | Sortie machine-readable |

> Cette commande demande une confirmation interactive. Utile pour le menage periodique apres que le [moteur de vitalite](vitalite.md) ait archive les memoires obsoletes.

---

## `fougasse export`

Exporter les memoires en JSON. Voir [Export / Import](export-import.md).

```bash
fougasse export                          # Vers stdout
fougasse export -o backup.json           # Vers fichier
fougasse export --vault work -o work.json  # Un seul vault
```

### Options

| Option | Description |
|--------|-------------|
| `--vault VAULT` | Exporter uniquement ce vault |
| `-o, --output PATH` | Chemin du fichier de sortie |
| `--json` | Format JSON (defaut) |

---

## `fougasse import`

Importer des memoires depuis un fichier JSON. Voir [Export / Import](export-import.md).

```bash
fougasse import backup.json
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FILE` | Chemin du fichier JSON a importer (requis) |

---

## `fougasse bench`

Lancer un [benchmark](benchmarks.md) de performance.

```bash
fougasse bench                        # 1000 memoires, 100 queries
fougasse bench --count 5000           # 5000 memoires synthetiques
fougasse bench --queries 500          # 500 requetes de test
fougasse bench --json                 # Sortie JSON
```

### Options

| Option | Description |
|--------|-------------|
| `--count N` | Nombre de memoires synthetiques (defaut: 1000) |
| `--queries N` | Nombre de requetes de test (defaut: 100) |
| `--json` | Sortie machine-readable |

---

## Flag global `--json`

Toutes les commandes supportent le flag `--json` (ou `--json-output`) pour produire une sortie JSON parseable par des scripts ou des agents.

```bash
fougasse status --json | jq '.memory_count'
```

---

**Voir aussi** : [Outils MCP](mcp-tools.md) | [Configuration](configuration.md) | [Export / Import](export-import.md) | [Benchmarks](benchmarks.md)
