# Benchmarks

[< Retour a l'index](index.md)

---

Fougasse integre un outil de benchmark pour mesurer les performances de [recherche hybride](recherche-hybride.md) sur votre machine.

## Lancement

```bash
# Benchmark par defaut (1000 memoires, 100 queries)
fougasse bench

# Benchmark avec plus de donnees
fougasse bench --count 10000 --queries 500

# Sortie JSON
fougasse bench --json
```

## Fonctionnement

Le benchmark :

1. **Cree une DB temporaire** (en memoire, pas votre DB de production)
2. **Genere N memoires synthetiques** avec du vocabulaire technique aleatoire
3. **Insere** chaque memoire avec un vecteur et un index FTS5
4. **Execute Q requetes** de [recherche hybride](recherche-hybride.md) avec des embeddings mockes
5. **Mesure** les latences d'insertion et de retrieval

## Metriques

| Metrique | Description |
|----------|-------------|
| `memories` | Nombre de memoires synthetiques generees |
| `queries` | Nombre de requetes executees |
| `embedding_dim` | Dimension des vecteurs (4 en bench, 768 en production) |
| `insert_total_ms` | Temps total d'insertion |
| `insert_per_memory_ms` | Temps moyen par memoire |
| `retrieval_p50_ms` | Latence mediane du retrieval |
| `retrieval_p95_ms` | 95e percentile |
| `retrieval_p99_ms` | 99e percentile |
| `queries_per_sec` | Debit de requetes |

## Exemple de sortie

```
+----------------------+---------+
| Metric               | Value   |
+----------------------+---------+
| memories             | 1000    |
| queries              | 100     |
| embedding_dim        | 4       |
| insert_total_ms      | 1250.3  |
| insert_per_memory_ms | 1.25    |
| retrieval_p50_ms     | 2.45    |
| retrieval_p95_ms     | 5.12    |
| retrieval_p99_ms     | 8.93    |
| queries_per_sec      | 312.5   |
+----------------------+---------+
```

## Limites du benchmark

- Les vecteurs sont de **dimension 4** (pas 768) pour la vitesse — les latences reelles seront plus elevees
- Les memoires synthetiques n'ont pas la distribution d'un usage reel
- Le [canal graphe](recherche-hybride.md#canal-3--graphe) n'est pas actif dans le benchmark
- Le [reranking](recherche-hybride.md#reranking-optionnel) n'est pas teste

Pour des mesures plus realistes, utilisez votre propre base de donnees et mesurez les latences de `fougasse_recall` en production.

## Objectifs de performance

| Metrique | Cible | Notes |
|----------|-------|-------|
| Retrieval P50 | < 50ms | Avec vecteurs 768-dim |
| Retrieval P95 | < 200ms | Sur 100K memoires |
| Insertion | < 100ms | Hors temps d'[embedding](embeddings.md) (~22ms) |
| Premier appel | < 5s | Chargement du modele |

---

**Voir aussi** : [Recherche hybride](recherche-hybride.md) | [CLI](cli.md#fougasse-bench) | [Configuration](configuration.md#recherche)
