# Fougasse — Documentation

**Moteur de memoire persistante locale pour LLM multi-clients via MCP**

Fougasse centralise le contexte entre tous vos clients LLM. Plus jamais de copier-coller entre vos conversations IA.

---

## Guide de demarrage

- [Installation](installation.md) — Installer et configurer Fougasse
- [Configuration](configuration.md) — Fichier TOML, variables d'environnement, valeurs par defaut

## Fonctionnalites principales

- [Outils MCP](mcp-tools.md) — Les 5 tools MCP : remember, recall, forget, status, vaults
- [Interface CLI](cli.md) — Commandes d'administration en ligne de commande
- [Recherche hybride](recherche-hybride.md) — 4 canaux de recherche avec fusion RRF
- [Graphe de connaissances](graphe-connaissances.md) — NetworkX, entity linking, PageRank, communautes
- [Vaults](vaults.md) — Isolation par namespaces
- [Embeddings](embeddings.md) — Modele BGE-Base, serialisation vectorielle

## Fonctionnalites avancees

- [Vitalite et declin](vitalite.md) — Moteur ACT-R, consolidation, archivage, resurrection
- [Detection de contradictions](contradictions.md) — Heuristique semantique FR/EN
- [Securite et confiance](securite.md) — Scoring bayesien, provenance, conformite RGPD
- [Export / Import](export-import.md) — Sauvegarde et restauration JSON
- [Benchmarks](benchmarks.md) — Tests de performance integres

## Reference technique

- [Modele de donnees](modele-donnees.md) — Schema SQLite complet, tables, index, migrations

---

## Liens utiles

- [Depot GitHub](https://github.com/eRom/fougasse)
- [CLAUDE.md](../CLAUDE.md) — Best practices de la stack technique
- [Specifications](../.specs/) — Dossier de specs complet
