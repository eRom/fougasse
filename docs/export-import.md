# Export / Import

[< Retour a l'index](index.md)

---

Fougasse permet d'exporter et importer ses memoires en format JSON pour la sauvegarde, la migration, ou le partage.

## Export

### Via CLI

```bash
# Export complet vers stdout
fougasse export

# Export vers fichier
fougasse export -o backup.json

# Export d'un seul vault
fougasse export --vault work -o work-backup.json
```

### Format de sortie

```json
{
  "fougasse_version": "0.1.0",
  "export_format": "1.0",
  "count": 42,
  "vault_filter": null,
  "memories": [
    {
      "id": "e8ee0fe1-...",
      "content": "Le contenu de la memoire",
      "type": "text",
      "tags": ["python", "ml"],
      "vault_id": "default",
      "source_agent": "claude-code",
      "metadata": {"importance": "high"},
      "vitality_score": 0.85,
      "access_count": 12,
      "is_archived": false,
      "created_at": "2026-03-18T08:23:28",
      "updated_at": "2026-03-18T10:45:00"
    }
  ],
  "vaults": [
    {
      "id": "default",
      "name": "default",
      "description": "Default vault",
      "created_at": "2026-03-18T07:59:47"
    }
  ],
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

### Contenu exporte

| Element | Inclus | Notes |
|---------|--------|-------|
| Memoires (actives + archivees) | Oui | Tous les champs |
| Tags | Oui | Dans chaque memoire |
| Vaults | Oui | Liste complete |
| [Graphe de connaissances](graphe-connaissances.md) | Oui | Noeuds + aretes |
| Vecteurs (embeddings) | Non | Re-generes a l'import |
| Index FTS5 | Non | Re-construit a l'import |
| [Access log](vitalite.md#journalisation-des-acces) | Non | Non exporte |

## Import

### Via CLI

```bash
fougasse import backup.json
```

### Comportement

1. Les [vaults](vaults.md) du fichier sont crees s'ils n'existent pas (`INSERT OR IGNORE`)
2. Chaque memoire est re-inseree avec un **nouvel ID** (pas de conflit d'UUID)
3. Les [embeddings](embeddings.md) sont re-generes a l'insertion
4. L'[index FTS5](recherche-hybride.md#canal-2--bm25-fts5) est reconstruit automatiquement
5. Les memoires invalides sont ignorees avec un message d'erreur

### Sortie

```
Imported 42 memories from backup.json
```

Si des erreurs surviennent :

```
Skipped: content too short
Skipped: invalid type 'unknown'
Imported 40 memories from backup.json
```

### Resultats

| Champ | Description |
|-------|-------------|
| `imported` | Nombre de memoires importees |
| `skipped` | Nombre de memoires ignorees |
| `errors` | Liste des 10 premieres erreurs |
| `source_version` | Version de Fougasse qui a genere l'export |

## Cas d'usage

### Sauvegarde periodique

```bash
# Cron quotidien
fougasse export -o ~/.fougasse/backups/$(date +%Y-%m-%d).json
```

### Migration entre machines

```bash
# Machine source
fougasse export -o transfer.json

# Machine destination
fougasse import transfer.json
```

### Partage de contexte

```bash
# Exporter le contexte d'un projet
fougasse export --vault cruchot -o cruchot-context.json

# Un collegue peut importer ce contexte
fougasse import cruchot-context.json
```

> **Note** : les embeddings sont re-generes a l'import, ce qui necessite que le modele d'[embedding](embeddings.md) soit le meme sur les deux machines.

---

**Voir aussi** : [CLI](cli.md) | [Configuration](configuration.md#chemins) | [Securite — RGPD](securite.md#conformite-rgpd)
