# Detection de contradictions

[< Retour a l'index](index.md)

---

Fougasse detecte automatiquement quand une nouvelle memoire contredit une memoire existante, et maintient la coherence du [graphe de connaissances](graphe-connaissances.md).

## Fonctionnement

A chaque appel a [`fougasse_remember`](mcp-tools.md#fougasse_remember), Fougasse :

1. Cherche les memoires existantes avec une **similarite semantique elevee** (> 0.85) dans le meme [vault](vaults.md)
2. Verifie la presence de **patterns de negation** dans les textes
3. Cree un lien dans le graphe si contradiction detectee
4. Retourne un warning au LLM appelant

## Types de contradictions

### Supersedes (remplacement)

**Condition** : haute similarite (> 0.85) + pattern de negation detecte.

La nouvelle memoire **remplace** l'ancienne. Un lien `supersedes` est cree dans le [graphe](graphe-connaissances.md#types-de-relations-aretes).

```
Ancienne : "Le meeting est a 14h"
Nouvelle : "Le meeting n'est plus a 14h, il est a 16h"
→ Lien supersedes : nouvelle → ancienne
```

### Conflicts_with (conflit ambigu)

**Condition** : tres haute similarite (> 0.95) sans negation claire.

Les deux memoires coexistent avec un lien `conflicts_with` — c'est peut-etre un doublon, peut-etre un vrai conflit.

```
Ancienne : "Deploy to production on Friday"
Nouvelle : "Deploy to production on Friday afternoon"
→ Lien conflicts_with (possible doublon)
```

## Patterns de negation

Fougasse reconnait les patterns de negation en **francais et en anglais** :

### Francais
- `ne...pas` / `n'est pas`
- `plus` (ne...plus)
- `annule`, `remplace`
- `contrairement`
- `en fait`

### Anglais
- `not`, `no longer`
- `cancel`, `replace`
- `actually`, `instead`
- `wrong`, `incorrect`
- `changed...to`
- `no`, `never`

## Configuration

| Parametre | Defaut | Description |
|-----------|--------|-------------|
| `contradiction_similarity_threshold` | 0.85 | Seuil de similarite pour declencher la detection. [Configurable](configuration.md#detection-de-contradictions) |

Augmenter le seuil (ex: 0.90) reduit les faux positifs mais peut manquer des contradictions subtiles.

## Warning dans la reponse

Quand une contradiction est detectee, `fougasse_remember` retourne un champ supplementaire :

```json
{
  "status": "stored",
  "id": "...",
  "warning": {
    "type": "contradiction_detected",
    "conflicting_memory_id": "abc-123",
    "relation": "supersedes",
    "similarity": 0.92,
    "reason": "High similarity (0.92) with negation pattern detected."
  }
}
```

Le LLM peut alors decider d'informer l'utilisateur ou de prendre une action.

## Limites

- La detection est **heuristique** (patterns regex), pas un raisonnement logique complet
- Ne detecte pas les contradictions implicites (ex: "le budget est 10K" vs "le budget est 20K" sans negation)
- Fonctionne mieux pour les faits explicitement opposes
- Evolution prevue : Sheaf Cohomology pour la detection algebrique (P3+)

---

**Voir aussi** : [Graphe de connaissances](graphe-connaissances.md) | [Outils MCP — remember](mcp-tools.md#fougasse_remember) | [Configuration](configuration.md#detection-de-contradictions)
