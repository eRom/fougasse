# Vaults

[< Retour a l'index](index.md)

---

Les vaults sont des **namespaces d'isolation** pour vos memoires. Chaque vault est un espace logique independant avec ses propres memoires, tags et sous-graphe.

## Concept

Imaginez les vaults comme des dossiers de projet pour votre memoire :

```
default/        ← Tout ce qui n'a pas de vault specifie
work/           ← Contexte professionnel
cruchot/        ← Tout sur le projet Cruchot
fougasse/       ← Tout sur le projet Fougasse
perso/          ← Notes personnelles
```

## Vault par defaut

Au premier demarrage, Fougasse cree automatiquement un vault `default`. Toute memoire sans `vault_id` explicite est stockee dans ce vault.

Le vault par defaut est [configurable](configuration.md#vaults) via `default_vault` dans le fichier TOML.

## Gestion via MCP

Voir [`fougasse_vaults`](mcp-tools.md#fougasse_vaults) pour la reference complete.

```
// Creer un vault
fougasse_vaults(action="create", name="work", description="Projets pro")

// Lister les vaults
fougasse_vaults(action="list")

// Supprimer un vault (doit etre vide)
fougasse_vaults(action="delete", name="old-project")
```

## Gestion via CLI

```bash
fougasse vaults          # Lister
fougasse vaults --json   # Lister en JSON
```

> La creation et suppression de vaults via CLI n'est pas encore implementee — utilisez les [outils MCP](mcp-tools.md#fougasse_vaults).

## Recherche et isolation

### Recherche dans un vault

Specifiez `vault_id` dans [`fougasse_recall`](mcp-tools.md#fougasse_recall) pour limiter la recherche :

```
fougasse_recall(query="architecture microservices", vault_id="work")
```

### Recherche cross-vault

Si `vault_id` n'est pas specifie, la recherche s'effectue sur **tous les vaults**. C'est le comportement par defaut.

### Isolation vectorielle

Les vecteurs dans [sqlite-vec](modele-donnees.md#recherche-vectorielle) portent un champ `vault_id` qui permet le filtrage au niveau de la requete KNN. L'isolation est donc **logique** (pas physique — tout est dans un seul fichier DB).

## Regles de nommage

- Alphanumerique + tirets + underscores : `[a-zA-Z0-9_-]+`
- Maximum 64 caracteres
- Convertis en minuscules automatiquement
- Le vault `default` ne peut pas etre supprime

## Export par vault

L'[export](export-import.md) peut etre filtre par vault :

```bash
fougasse export --vault work -o work-backup.json
```

---

**Voir aussi** : [Outils MCP — vaults](mcp-tools.md#fougasse_vaults) | [Recherche hybride](recherche-hybride.md) | [Configuration](configuration.md#vaults) | [Modele de donnees](modele-donnees.md)
