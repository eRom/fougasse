# Analyse Team — core

**Date** : 2026-03-17
**Nombre de taches analysees** : 43

## Niveaux de parallelisme

```
Niveau 1 (parallel) : T01
Niveau 2 (parallel) : T02, T03, T04
Niveau 3 (parallel) : T05, T06
Niveau 4 (parallel) : T07, T08, T11
Niveau 5 (parallel) : T09
Niveau 6 (parallel) : T10
Niveau 7 (parallel) : T12
Niveau 8 (parallel) : T13
Niveau 9 (parallel) : T14
Niveau 10 (parallel) : T15, T19
Niveau 11 (parallel) : T16, T17, T25
Niveau 12 (parallel) : T18, T22, T23
Niveau 13 (parallel) : T20
Niveau 14 (parallel) : T21, T24
Niveau 15 (parallel) : T26
Niveau 16 (parallel) : T27, T28, T31, T33
Niveau 17 (parallel) : T29, T30, T32
Niveau 18 (parallel) : T34
Niveau 19 (parallel) : T35
Niveau 20 (parallel) : T36, T37, T38
Niveau 21 (parallel) : T39, T40
Niveau 22 (parallel) : T41
Niveau 23 (parallel) : T42
Niveau 24 (parallel) : T43
```

## Chemin critique
T01 → T03 → T05 → T07 → T09 → T10 → T12 → T13 → T14 → T15 → T16 → T18 → T20 → T24 → T26 → T27 → T29 → T34 → T35 → T37 → T40 → T41 → T42 → T43

**Longueur** : 24 niveaux (24 etapes sequentielles minimum)

## Goulots d'etranglement
| Tache | Dependantes directes | Impact |
|-------|---------------------|--------|
| T05 (Memory store) | T07, T08, T11 | 3 taches bloquees |
| T14 (CI) | T15, T19 | Porte d'entree P1 |
| T26 (Tests P1) | T27, T28, T31, T33 | Porte d'entree P2 (4 taches) |
| T35 (Tests P2) | T36, T37, T38 | Porte d'entree P3 (3 taches) |
| T20 (Retrieval 4 canaux) | T21, T24 | Cle de voute du retrieval |

## Conflits de fichiers
| Fichier | Taches | Risque |
|---------|--------|--------|
| server.py | T10, T24, T25, T33, T37 | Moyen — chaque tache ajoute des tools, mais sections independantes |
| hybrid_search.py | T09, T20, T28, T32 | Moyen — reecrit en P1, modifie en P2 |
| memory_store.py | T05, T11, T25, T31 | Faible — ajouts additifs |
| cli.py | T12, T37, T38, T39, T40 | Faible — ajouts de commandes |
| migrations/001_init.sql | T03, T07, T08 | Faible — co-editable lors de la creation initiale |

## Verdict
**OUI PARTIEL** — Le parallelisme est significatif a l'interieur de chaque phase, mais les phases elles-memes sont sequentielles (P0 → P1 → P2 → P3). Le gain principal est au sein de P0 (T02/T03/T04 en parallele, puis T07/T08/T11 en parallele) et P1 (T16/T17/T25 en parallele, puis T18/T22/T23 en parallele).

Le risque de conflits de fichiers est modere sur `server.py` et `hybrid_search.py`, mais gerable avec des sections bien definies.

## Composition de team

### Agents
| Agent | Type | Taches | Mode |
|-------|------|--------|------|
| storage-agent | backend | T03, T05, T07, T08, T11 | worktree |
| retrieval-agent | backend | T09, T18, T19, T20, T21 | worktree |
| graph-agent | backend | T15, T16, T17, T22, T23 | worktree |
| vitality-agent | backend | T27, T28, T29, T30, T31, T32, T34 | worktree |
| server-agent | backend | T10, T24, T25, T33, T37 | standard |

### Sequencage par vagues

**Vague 0 (bootstrap)** — Sequentiel, pas de team
- T01 (init projet) → T02, T03, T04 (config, DB, models)

**Vague 1 (P0 core)** — 2 agents paralleles
- storage-agent : T05 → T07 → T08 → T11
- Attente : T06 (embeddings) doit etre fait avant T07

**Vague 2 (P0 integration)** — Sequentiel
- T09 (RRF) → T10 (MCP server) → T12 (CLI) → T13 (tests) → T14 (CI)

**Vague 3 (P1)** — 2 agents paralleles
- graph-agent : T15 → T16, T17 → T18, T22, T23
- retrieval-agent : T19 → T20 (apres T18) → T21
- server-agent : T24, T25 (apres T15/T20)

**Vague 4 (P2)** — 2 agents paralleles
- vitality-agent : T27, T28 → T29 → T30 → T34
- server-agent : T31, T33, T32

**Vague 5 (P3)** — 2-3 agents paralleles
- T36, T37, T38 en parallele → T39, T40 → T41 → T42 → T43

### Points de synchronisation
- Apres Vague 0 : structure projet validee, DB operationnelle
- Apres Vague 2 : MVP P0 complet et teste, CI verte
- Apres T26 : P1 complet et teste, porte d'entree P2
- Apres T35 : P2 complet et teste, porte d'entree P3
- Apres T43 : Projet complet

## Estimation du gain
| Metrique | Valeur |
|----------|--------|
| Unites sequentielles | 43 taches, ~24 niveaux |
| Unites avec team | ~18 niveaux (parallelisme intra-phase) |
| Gain estime | ~25% reduction du chemin critique |

Le gain est modeste car les phases sont intrinsèquement sequentielles (P1 depend de P0, etc.). Le parallelisme est surtout utile au sein de chaque phase.

## Risques & Mitigations
| Risque | Impact | Mitigation |
|--------|--------|------------|
| Conflit sur server.py entre agents | Moyen | Chaque agent ajoute des tools dans des fonctions distinctes, merge sequentiel |
| Conflit sur hybrid_search.py | Moyen | Rewrite complet en P1 (T20), modifications P2 additives |
| Agent graph depend de storage | Faible | Graph persistence utilise les memes tables — interface DB bien definie |
| Tests d'integration cross-modules | Moyen | Tests d'integration apres chaque vague, pas seulement en fin de phase |
