# Graphe de connaissances

[< Retour a l'index](index.md)

---

Fougasse construit et maintient un graphe de connaissances oriente (DiGraph) qui relie les memoires entre elles. Ce graphe permet de decouvrir des connexions non evidentes et alimente le [canal de recherche graphe](recherche-hybride.md#canal-3--graphe).

## Structure du graphe

Le graphe utilise **NetworkX** en memoire, persiste dans [SQLite](modele-donnees.md#graphe-de-connaissances).

### Types de noeuds

| Type | ID | Description |
|------|----|-------------|
| `memory` | UUID de la memoire | Chaque memoire stockee est un noeud |
| `entity` | `tag:<nom>` | Chaque tag unique est un noeud entite |

### Types de relations (aretes)

| Relation | Direction | Signification |
|----------|-----------|---------------|
| `tagged_with` | memoire → entite | La memoire a ce tag |
| `relates_to` | memoire ↔ memoire | Les deux memoires sont liees (tags partages ou similarite) |
| `supersedes` | nouvelle → ancienne | La nouvelle memoire remplace l'ancienne ([contradiction](contradictions.md)) |
| `conflicts_with` | memoire ↔ memoire | Les deux memoires se contredisent |

Chaque arete porte un **poids** (0.0 a 1.0) representant la force de la relation.

## Entity linking

Quand une memoire est inseree, le systeme cree automatiquement des aretes :

### 1. Liens tag → entite

Pour chaque tag de la memoire, une arete `tagged_with` est creee vers le noeud entite correspondant. Si l'entite n'existe pas, elle est creee.

```
[Memoire "Python ML tutorial"] --tagged_with--> [tag:python]
                                --tagged_with--> [tag:ml]
```

### 2. Liens par tags partages

Si deux memoires partagent **2 tags ou plus**, une arete bidirectionnelle `relates_to` est creee. Le poids est proportionnel au ratio de tags partages.

```
[Memoire A: tags python, ml, data] <--relates_to--> [Memoire B: tags python, data, web]
                                       poids = 2/3
```

### 3. Liens par similarite semantique

Apres insertion, les memoires les plus proches semantiquement (via [recherche KNN](recherche-hybride.md#canal-1--semantique-knn)) avec une similarite >= 0.8 recoivent un lien `relates_to`.

## Spreading activation

L'algorithme de spreading activation est utilise pour le [canal de recherche graphe](recherche-hybride.md#canal-3--graphe) :

1. **Initialisation** : les noeuds "graines" (top resultats du canal semantique) recoivent un score = 1.0
2. **Propagation** : a chaque hop, le score est multiplie par `decay * poids_arete`
3. **Hops** : maximum 3 sauts (configurable)
4. **Filtrage** : seuls les noeuds `memory` (pas `entity`) sont retournes
5. **Tri** : par score d'activation decroissant

### Parametres

| Parametre | Defaut | Description |
|-----------|--------|-------------|
| `max_hops` | 3 | Profondeur de propagation |
| `decay` | 0.5 | Facteur de decroissance par hop |
| `max_results` | 30 | Nombre max de resultats |

## PageRank

Fougasse calcule le [PageRank](https://fr.wikipedia.org/wiki/PageRank) de chaque noeud pour identifier les memoires les plus "centrales" du graphe.

- Algorithme : `nx.pagerank(G, alpha=0.85)`
- Les scores sont stockes dans l'attribut `pagerank` de chaque noeud
- Declenchable periodiquement via le [scheduler](vitalite.md#scheduler-periodique) ou manuellement

Les memoires a fort PageRank sont les "hubs" de votre base de connaissances — elles relient de nombreuses autres memoires.

## Detection de communautes

Fougasse detecte les groupes de memoires fortement interconnectees (communautes) :

- Algorithme : Greedy Modularity de NetworkX (fallback : composantes connexes)
- Chaque noeud recoit un `community_id`
- Utile pour identifier des clusters thematiques (ex: "tout ce qui touche au projet X")

Voir `fougasse_explore` dans les [outils MCP](mcp-tools.md#fougasse_vaults) pour naviguer les communautes.

## Protection Tarjan

Avant de supprimer une memoire via [`fougasse_forget`](mcp-tools.md#fougasse_forget), Fougasse verifie si le noeud est un **point d'articulation** du graphe (algorithme de Tarjan).

Un point d'articulation est un noeud dont la suppression **deconnecterait** le graphe en deux ou plusieurs composantes. Si c'est le cas, un warning est emis dans la reponse.

```
// Warning retourne par fougasse_forget
{
  "warning": "This memory is an articulation point. Deleting it will disconnect part of the graph.",
  "force": "Set force=true to delete anyway."
}
```

## Persistence

Le graphe est maintenu en memoire (NetworkX) pour la performance et persiste dans SQLite :

- **Au demarrage** : le graphe est charge depuis les tables [`graph_nodes` et `graph_edges`](modele-donnees.md#graphe-de-connaissances)
- **A l'ecriture** : chaque nouvelle memoire declenche une sauvegarde incrementale (noeud + aretes)
- **Periodiquement** : sauvegarde complete via le [scheduler](vitalite.md#scheduler-periodique)

### Performance du chargement

| Taille graphe | Temps de chargement |
|---------------|-------------------|
| 10K noeuds, 50K aretes | ~50ms |
| 100K noeuds, 500K aretes | ~200ms |
| 500K+ noeuds | Considerer `igraph` |

---

**Voir aussi** : [Recherche hybride](recherche-hybride.md) | [Detection de contradictions](contradictions.md) | [Modele de donnees](modele-donnees.md) | [Vitalite](vitalite.md)
