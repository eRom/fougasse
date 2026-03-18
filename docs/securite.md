# Securite et confiance

[< Retour a l'index](index.md)

---

Fougasse est concu **security by design** : donnees locales uniquement, validation stricte des entrees, et scoring de confiance par agent.

## Principes

1. **Zero cloud** : les donnees ne quittent jamais la machine
2. **Zero reseau** : transport stdio par defaut, pas de port ouvert
3. **Provenance** : chaque memoire tracke son agent source
4. **Defense en profondeur** : validation Pydantic + SQL parametre + isolation vaults

## Scoring de confiance par agent

Fougasse utilise un modele **Beta-Binomial bayesien** pour evaluer la fiabilite de chaque agent source.

### Modele

Chaque agent a deux compteurs :
- `alpha` (evidence positive) — initialise a 1.0
- `beta` (evidence negative) — initialise a 1.0

**Score de confiance** = `alpha / (alpha + beta)`

| Score initial | 0.5 (neutre) |
| Score apres 50 feedbacks positifs | ~0.67 |
| Seuil de confiance | >= 0.3 |
| Agent non fiable | < 0.3 → warnings sur ses memoires |

### Asymetrie

Le scoring est **intentionnellement asymetrique** :

| Feedback | Magnitude | Interpretation |
|----------|-----------|---------------|
| Positif (memoire utile) | +0.02 | Dur a gagner |
| Negatif (memoire incorrecte) | +0.03 | Facile a perdre |

Un agent qui injecte 1 fausse memoire pour 10 correctes verra son score baisser progressivement.

### Menaces contrees

| Menace | Description | Defense |
|--------|------------|---------|
| **MemoryGraft** | Injection indirecte via experiences empoisonnees | Score bayesien + provenance |
| **Sleeper Agents** | Comportement normal puis injection lente | Asymetrie du scoring detecte la derive |
| **Propagation multi-agents** | 1 agent empoisonne contamine les autres | Score < 0.3 → blocage des ecritures |

## Provenance

Chaque memoire stocke son **agent source** (`source_agent`), permettant :

- L'audit de qui a ecrit quoi
- Le calcul du score de confiance par agent
- Le filtrage des memoires par source
- La tracabilite en cas d'incident

## Validation des entrees

Toutes les entrees MCP sont validees par Pydantic **avant** tout traitement :

| Champ | Validation |
|-------|-----------|
| `content` | 1 a 102400 caracteres |
| `type` | Enum strict (text, code, task, appointment, idea, conversation, topic) |
| `tags` | Max 20, chacun max 64 chars, alphanumerique + tirets |
| `vault_id` | Alphanumerique + tirets, max 64 chars |
| `memory_id` | Format UUID |
| `limit` | 1 a 100 |

## Protection SQL

- **Queries parametrees uniquement** : aucune interpolation de string dans les requetes SQL
- `sqlite3` stdlib avec `?` placeholders
- Aucun ORM (controle total des requetes)

## Surface d'attaque

| Point d'entree | Exposition | Mitigation |
|----------------|-----------|------------|
| MCP stdio | Process local uniquement | Pas de port reseau |
| MCP SSE (optionnel) | `127.0.0.1` uniquement | Jamais `0.0.0.0`, [configurable](configuration.md#serveur) |
| Fichiers DB sur disque | Systeme de fichiers local | Permissions 700 (`~/.fougasse/`) |
| Modele d'embedding | Telecharge depuis HuggingFace | Pin de version, cache local, mode offline |
| Dependencies Python | Supply chain | `uv.lock` pinne, CI avec matrix |

## Conformite RGPD

Fougasse est concu pour etre compatible RGPD :

### Separation des donnees

| Base | Contenu | Objectif |
|------|---------|----------|
| `memory.db` | Memoires, graphe, vecteurs | Fonctionnel |
| `learning.db` | Patterns de recherche, feedback | Comportemental ([configurable](configuration.md#chemins)) |

Cette separation permet de supprimer les donnees comportementales independamment des memoires.

### Droit a l'oubli (Article 17)

- **Soft-delete** par defaut : [`fougasse_forget`](mcp-tools.md#fougasse_forget) archive sans detruire
- **Hard-delete** : `fougasse_forget(memory_id, hard=true)` ou CLI `fougasse prune --hard`
- **Export** : `fougasse export` pour obtenir toutes ses donnees ([Export / Import](export-import.md))
- **Suppression totale** : CLI `fougasse gdpr-delete` (a venir)

### Chiffrement (optionnel)

Le chiffrement au repos via SQLCipher est prevu pour une version ulterieure. En attendant, les fichiers DB sont proteges par les permissions du systeme de fichiers.

---

**Voir aussi** : [Configuration](configuration.md) | [Outils MCP](mcp-tools.md) | [Modele de donnees](modele-donnees.md)
