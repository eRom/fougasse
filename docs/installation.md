# Installation

[< Retour a l'index](index.md)

---

## Pre-requis

- Python 3.11 ou superieur
- macOS (ARM/Intel), Windows ou Linux
- ~500 Mo d'espace disque (modele d'embedding)

## Installation rapide (PyPI)

```bash
pip install fougasse
```

## Installation depuis les sources (developpement)

```bash
git clone https://github.com/eRom/fougasse.git
cd fougasse
uv sync --all-extras
```

## Premier lancement

```bash
# Verifier l'installation
fougasse --version

# Voir le statut (cree automatiquement ~/.fougasse/)
fougasse status
```

Au premier lancement, Fougasse :
1. Cree le dossier `~/.fougasse/`
2. Initialise la base de donnees `~/.fougasse/memory.db`
3. Applique les migrations SQL
4. Cree le vault par defaut (`default`)

## Telecharger le modele d'embedding

Le modele `BAAI/bge-base-en-v1.5` (~450 Mo) est telecharge automatiquement au premier appel. Pour le pre-telecharger :

```bash
uv run python -c "from fougasse.embeddings import load_model; load_model()"
```

Le modele est cache dans `~/.fougasse/models/` pour eviter les re-telechargements.

## Configurer comme serveur MCP

### Claude Code (global)

Creer ou editer `~/.claude/mcp.json` :

```json
{
  "mcpServers": {
    "fougasse": {
      "command": "uv",
      "args": ["run", "--directory", "/chemin/vers/fougasse", "python", "-m", "fougasse.server"],
      "env": {
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_OFFLINE": "1"
      }
    }
  }
}
```

> Les variables `TRANSFORMERS_OFFLINE` et `HF_HUB_OFFLINE` evitent les requetes reseau au demarrage si le modele est deja en cache.

### Claude Code (projet uniquement)

Creer `.mcp.json` a la racine du projet :

```json
{
  "mcpServers": {
    "fougasse": {
      "command": "uv",
      "args": ["run", "--directory", "/chemin/vers/fougasse", "python", "-m", "fougasse.server"]
    }
  }
}
```

### Claude Desktop

Editer `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) :

```json
{
  "mcpServers": {
    "fougasse": {
      "command": "uv",
      "args": ["run", "--directory", "/chemin/vers/fougasse", "python", "-m", "fougasse.server"]
    }
  }
}
```

### Cursor / Windsurf

Consulter la documentation de chaque editeur pour l'ajout de serveurs MCP. Le format est similaire.

## Verification

Apres configuration, relancez votre client LLM puis :

```
fougasse_status
```

Si Fougasse repond avec la version et les statistiques, l'installation est reussie.

---

**Voir aussi** : [Configuration](configuration.md) | [Outils MCP](mcp-tools.md) | [CLI](cli.md)
