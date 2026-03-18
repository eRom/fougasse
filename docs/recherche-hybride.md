# Recherche hybride

[< Retour a l'index](index.md)

---

La recherche hybride est le coeur du [retrieval](mcp-tools.md#fougasse_recall) de Fougasse. Elle combine 4 canaux de recherche independants, fusionne leurs resultats via RRF, et applique optionnellement un reranking neural.

## Architecture

```
          Query (langage naturel)
                    |
    +---------------+---------------+
    |               |               |
    v               v               v
[Canal 1]      [Canal 2]      [Canal 3]      [Canal 4]
Semantique     BM25 FTS5      Graphe         Temporel
(sqlite-vec)   (SQLite)       (NetworkX)     (decay exp)
    |               |               |               |
    v               v               v               v
    +-------+-------+-------+-------+
                    |
              Fusion RRF
                    |
            [Reranking] (optionnel)
                    |
              Top-K resultats
```

## Canal 1 — Semantique (KNN)

Recherche par similarite vectorielle dans [sqlite-vec](modele-donnees.md#recherche-vectorielle).

1. Le texte de la requete est encode en vecteur via [BGE-Base](embeddings.md)
2. Recherche KNN (K-Nearest Neighbors) sur les vecteurs stockes
3. Distance L2 sur vecteurs normalises (equivalent cosinus)
4. Filtrage par `vault_id` et `is_archived` au niveau SQL

**Forces** : comprend le sens semantique, fonctionne meme si les mots exacts ne sont pas presents.
**Faiblesses** : peut manquer des correspondances lexicales exactes (noms propres, code).

## Canal 2 — BM25 (FTS5)

Recherche plein texte via l'index [FTS5](modele-donnees.md#recherche-plein-texte) de SQLite.

1. La requete est nettoyee (caracteres speciaux supprimes, seuls les mots alphanumeriques sont gardes)
2. Recherche BM25 sur le contenu + tags
3. Score BM25 natif (Okapi BM25 integre a FTS5)

**Forces** : excellent pour les termes exacts, noms propres, identifiants de code, acronymes.
**Faiblesses** : ne comprend pas les synonymes ni la semantique.

## Canal 3 — Graphe

[Spreading activation](graphe-connaissances.md#spreading-activation) dans le [graphe de connaissances](graphe-connaissances.md).

1. Les 3 meilleurs resultats du canal semantique servent de "graines" (seeds)
2. L'activation se propage dans le graphe sur 3 sauts (hops)
3. A chaque saut, le score est multiplie par un facteur de decroissance (defaut: 0.5)
4. Seuls les noeuds de type `memory` sont retournes (pas les entites)

**Forces** : decouvre des connexions non evidentes entre memoires liees par tags, entites ou relations.
**Faiblesses** : necessite un graphe suffisamment connecte. Sans [entity linking](graphe-connaissances.md#entity-linking), ce canal est inactif.

## Canal 4 — Temporel

Boost de recence base sur l'age des memoires.

1. Calcul du score temporel : `score = exp(-lambda * age_en_jours)`
2. `lambda` par defaut = 0.05 (configurable via [`vitality_decay_d`](configuration.md))
3. Une memoire creee aujourd'hui a un score ~1.0, a 30 jours ~0.22, a 90 jours ~0.01

**Forces** : favorise les informations recentes, pertinent pour les contextes evolutifs.
**Faiblesses** : peut noyer des memoires anciennes mais toujours pertinentes.

## Fusion RRF

Les resultats des 4 canaux sont fusionnes via **Reciprocal Rank Fusion** :

```
score(item) = sum( weight_i / (k + rank_i + 1) )
```

| Parametre | Defaut | Role |
|-----------|--------|------|
| `k` | 60 | Parametre de lissage. Plus eleve = scores plus uniformes. [Configurable](configuration.md) |
| `weights` | `[1.0, 1.0, 1.0, 0.5]` | Poids par canal (semantique, BM25, graphe, temporel) |

**Pourquoi RRF ?** Pas d'hyperparametres a tuner (contrairement a la normalisation de scores), performant meme avec des listes de longueurs differentes, prouve en production.

## Reranking optionnel

Quand [`reranker_enabled = true`](configuration.md#reranker), les top-K resultats de la fusion RRF sont re-scores par un cross-encoder neural :

- **Modele** : `cross-encoder/ms-marco-MiniLM-L-6-v2` (configurable)
- **Top-K** : 20 candidats (configurable via `reranker_top_k`)
- **Principe** : le cross-encoder score chaque paire (requete, contenu) conjointement, plus precis qu'un bi-encoder

Le reranking ajoute ~50-100ms de latence mais peut ameliorer significativement la precision sur les requetes ambigues.

## Filtrage post-fusion

Apres la fusion (et reranking optionnel), les resultats sont filtres :

1. **Vault** : si `vault_id` specifie, seules les memoires de ce vault
2. **Type** : si `type_filter` specifie (ex: `code`, `task`)
3. **Tags** : si `tags_filter` specifie, au moins un tag doit correspondre
4. **Archives** : exclues par defaut (sauf `include_archived=true`)
5. **Score minimum** : si `min_score` specifie

## Performance

| Metrique | Cible | Mesure typique |
|----------|-------|----------------|
| Latence P50 | < 50ms | ~30ms (sans reranker, 10K memoires) |
| Latence P95 | < 200ms | ~150ms |
| Premier appel | < 5s | ~3-5s (chargement modele) |

> Utilisez `fougasse bench` pour mesurer les performances sur votre machine. Voir [Benchmarks](benchmarks.md).

---

**Voir aussi** : [Outils MCP — recall](mcp-tools.md#fougasse_recall) | [Embeddings](embeddings.md) | [Graphe de connaissances](graphe-connaissances.md) | [Configuration](configuration.md#recherche)
