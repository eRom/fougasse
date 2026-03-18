# Vitalite et declin

[< Retour a l'index](index.md)

---

Fougasse simule l'oubli et le renforcement des souvenirs inspire des sciences cognitives. Les memoires frequemment consultees sont renforcees, les memoires inactives declinent progressivement.

## Modele ACT-R

Le moteur de vitalite est base sur le modele [ACT-R](https://en.wikipedia.org/wiki/ACT-R) (Adaptive Control of Thought-Rational) :

```
vitality = somme( age_heures_i ^ (-d) )
```

Ou :
- `age_heures_i` = temps en heures depuis le i-eme acces (minimum 1h)
- `d` = exposant de declin (defaut : 0.5, [configurable](configuration.md#vitalite))
- La somme porte sur **tous les acces** enregistres dans `access_log`

### Comportement

| Scenario | Vitalite |
|----------|----------|
| Memoire accedee il y a 1h | 1.0 |
| Memoire accedee il y a 24h | 0.20 |
| Memoire accedee il y a 7 jours | 0.077 |
| Memoire accedee 10 fois en 1 semaine | ~1.5 (renforcee) |
| Memoire jamais accedee depuis 30 jours | ~0.04 (proche archivage) |

**Point cle** : une memoire accedee 10 fois il y a 1 an declinera, tandis qu'une memoire accedee 2 fois cette semaine restera active. C'est exactement le comportement desire — pas de TTL arbitraire.

## Journalisation des acces

Chaque appel a [`fougasse_recall`](mcp-tools.md#fougasse_recall) ou [`fougasse_explore`](mcp-tools.md#fougasse_vaults) qui retourne une memoire dans ses resultats enregistre un acces dans la table `access_log`.

Ces acces alimentent le calcul de vitalite. Plus une memoire est consultee, plus elle reste active.

## Archivage automatique

Les memoires dont la vitalite tombe sous le seuil sont automatiquement archivees :

- **Seuil** : `vitality_archive_threshold = 0.1` ([configurable](configuration.md#vitalite))
- **Mode** : soft-delete (`is_archived = 1`) — pas de suppression
- **Exception** : les memoires avec `metadata.pinned = true` sont protegees

L'archivage est execute periodiquement par le [scheduler](#scheduler-periodique).

### Memoires pinnees

Pour proteger une memoire de l'archivage, ajoutez `"pinned": true` dans ses metadonnees :

```
fougasse_remember(
  content="Information critique a ne jamais oublier",
  metadata={"pinned": true}
)
```

## Resurrection

Quand une memoire archivee est retrouvee par [`fougasse_recall`](mcp-tools.md#fougasse_recall), elle est automatiquement **ressuscitee** :

1. `is_archived` repasse a `0`
2. `vitality_score` est booste a 1.0
3. Un acces est enregistre dans `access_log`

Cela simule le phenomene cognitif du "souvenir retrouve" — une information oubliee qui redevient pertinente apres avoir ete retrouvee.

## Consolidation

La consolidation fusionne les memoires quasi-identiques (similarite > 0.9) dans le meme [vault](vaults.md) :

1. Detection des paires de memoires tres similaires
2. La memoire la plus recente est conservee
3. L'ancienne est archivee avec un lien `supersedes` dans le [graphe](graphe-connaissances.md)
4. L'historique est preserve via le [versioning](modele-donnees.md#historique-des-versions)

## Scheduler periodique

Un processus asyncio tourne en arriere-plan pendant que le serveur MCP est actif :

| Parametre | Defaut | Description |
|-----------|--------|-------------|
| `vitality_schedule_hours` | 6 | Intervalle entre les cycles ([configurable](configuration.md#vitalite)) |

### Cycle d'execution

A chaque cycle, le scheduler :

1. **Recalcule** la vitalite de toutes les memoires actives
2. **Archive** les memoires sous le seuil (sauf pinnees)
3. **Detecte** les candidats a la consolidation
4. **Met a jour** le [PageRank](graphe-connaissances.md#pagerank) et les [communautes](graphe-connaissances.md#detection-de-communautes)
5. **Log** un resume du cycle

### Monitoring

Le resultat du dernier cycle est visible dans les logs du serveur :

```
INFO Vitality cycle: {'vitalities_updated': 1250, 'archived': 3, 'skipped_pinned': 1}
```

---

**Voir aussi** : [Outils MCP](mcp-tools.md) | [Graphe de connaissances](graphe-connaissances.md) | [Configuration](configuration.md#vitalite) | [Modele de donnees](modele-donnees.md)
