# Architecture Fonctionnelle — Fougasse

**Date de creation** : 2026-03-17
**Derniere mise a jour** : 2026-03-17
**Chantiers integres** : core

## Vision produit
Fougasse est un moteur de memoire persistante locale qui centralise le contexte entre tous les clients LLM compatibles MCP. Les LLM poussent des souvenirs structures, Fougasse les stocke, les relie dans un graphe de connaissances dynamique, et restitue le contexte pertinent a la demande. Open-source, gratuit, francais, full local.

## Personas

### Romain — Developpeur / Architecte multi-LLM
- **Qui** : Developpeur senior utilisant 5+ LLM quotidiennement (Claude Desktop, Claude Code, Cursor, Cruchot, Gemini, Ollama)
- **Objectif** : Ne plus jamais re-expliquer un contexte quand il change de client LLM
- **Frustration actuelle** : Copier-coller le contexte entre clients LLM plusieurs fois par jour. Perdre des idees, des decisions techniques, des fils de discussion
- **Frequence d'usage** : Continu, plusieurs dizaines d'interactions/jour, ~50K memoires/an

### Contributeur open-source
- **Qui** : Developpeur francophone ou anglophone decouvrant le projet sur GitHub
- **Objectif** : Utiliser Fougasse pour sa propre memoire multi-LLM, contribuer
- **Frustration actuelle** : Les solutions existantes (Mem0, OpenMemory) sont anglophones, parfois cloud-dependent
- **Frequence d'usage** : Variable

## Parcours utilisateurs

### Parcours 1 — Memoriser un contexte
```
[LLM Client] → tool_call(fougasse_remember) → [Fougasse MCP Server]
                                                       |
                                                 Stocke memoire
                                                 Genere embedding
                                                 Met a jour graphe
                                                       |
                                                 [Confirmation]
```

### Parcours 2 — Retrouver du contexte
```
[LLM Client] → tool_call(fougasse_recall) → [Fougasse MCP Server]
                                                    |
                                              Recherche hybride
                                              (semantique + BM25 + graphe + temporel)
                                                    |
                                              Fusion + ranking
                                                    |
                                              [Memoires pertinentes]
```

### Parcours 3 — Naviguer dans la memoire
```
[LLM Client] → tool_call(fougasse_explore) → [Fougasse MCP Server]
                                                     |
                                               Parcours du graphe
                                               Liens, voisins, timeline
                                                     |
                                               [Carte du contexte]
```

### Parcours 4 — Administrer la memoire
```
[Utilisateur] → CLI (fougasse status/prune/export) → [Fougasse Engine]
                                                            |
                                                      Stats, nettoyage
                                                      Export/import
                                                            |
                                                      [Resultat]
```

## Cas d'usage

### [CU-01] Memoriser une information
- **Acteur** : LLM client via MCP
- **Precondition** : Fougasse tourne en local, LLM connecte via MCP
- **Scenario nominal** :
  1. Le LLM appelle `fougasse_remember` avec contenu, type, tags, metadata optionnelle
  2. Fougasse genere l'embedding du contenu
  3. Fougasse stocke la memoire dans le vault actif (ou default)
  4. Fougasse met a jour le graphe de connaissances (entites, liens)
  5. Fougasse met a jour l'index compresse
  6. Fougasse retourne un ID + confirmation
- **Scenarios alternatifs** :
  - [SA-01] Memoire contradictoire detectee → Fougasse cree un lien `supersedes` et retourne un warning
  - [SA-02] Vault specifie n'existe pas → creation automatique du vault
  - [SA-03] Contenu duplique detecte → merge ou rejet avec notification
- **Postcondition** : Memoire persistee, indexee, liee dans le graphe
- **Regles metier** : RM-01, RM-02, RM-03, RM-04

### [CU-02] Retrouver des memoires pertinentes
- **Acteur** : LLM client via MCP
- **Precondition** : Au moins une memoire stockee
- **Scenario nominal** :
  1. Le LLM appelle `fougasse_recall` avec une query en langage naturel
  2. Fougasse execute la recherche hybride (4 canaux paralleles)
  3. Fougasse fusionne les scores (WRRF)
  4. Fougasse applique le reranking
  5. Fougasse retourne les top-K memoires avec scores et metadata
- **Scenarios alternatifs** :
  - [SA-01] Aucun resultat pertinent (score < seuil) → retourne vide avec suggestion d'elargir
  - [SA-02] Query ambigue → retourne des clusters thematiques
  - [SA-03] Filtrage par vault, type, date demande → applique les filtres avant la recherche
- **Postcondition** : Memoires retournees, compteur d'acces incremente (vitalite)
- **Regles metier** : RM-05, RM-06, RM-07

### [CU-03] Explorer le graphe de connaissances
- **Acteur** : LLM client via MCP
- **Precondition** : Graphe non vide
- **Scenario nominal** :
  1. Le LLM appelle `fougasse_explore` avec un point d'entree (memoire ID, tag, entite)
  2. Fougasse retourne les noeuds voisins, les liens, les clusters
  3. Le LLM peut naviguer iterativement (drill-down)
- **Scenarios alternatifs** :
  - [SA-01] Point d'entree inconnu → suggestion de points proches
- **Postcondition** : Contexte de navigation retourne
- **Regles metier** : RM-08

### [CU-04] Mettre a jour une memoire
- **Acteur** : LLM client via MCP
- **Precondition** : Memoire existante
- **Scenario nominal** :
  1. Le LLM appelle `fougasse_update` avec l'ID et les champs a modifier
  2. Fougasse cree une version (historique)
  3. Fougasse re-genere l'embedding si le contenu change
  4. Fougasse met a jour le graphe
  5. Fougasse retourne confirmation
- **Scenarios alternatifs** :
  - [SA-01] ID inexistant → erreur
  - [SA-02] Mise a jour contradictoire → lien `supersedes` + warning
- **Postcondition** : Memoire mise a jour, historique preserve
- **Regles metier** : RM-09, RM-04

### [CU-05] Supprimer une memoire
- **Acteur** : LLM client via MCP ou utilisateur via CLI
- **Precondition** : Memoire existante
- **Scenario nominal** :
  1. Appel `fougasse_forget` avec ID ou filtre
  2. Fougasse verifie les dependances dans le graphe
  3. Fougasse supprime (soft-delete ou hard-delete selon config)
  4. Fougasse met a jour le graphe et l'index
- **Scenarios alternatifs** :
  - [SA-01] Memoire est un noeud critique du graphe (point d'articulation) → warning avant suppression
  - [SA-02] Suppression en masse par filtre → confirmation requise
- **Postcondition** : Memoire supprimee, graphe coherent
- **Regles metier** : RM-10, RM-11

### [CU-06] Gerer les vaults
- **Acteur** : LLM client via MCP ou utilisateur via CLI
- **Precondition** : Fougasse operationnel
- **Scenario nominal** :
  1. Creer/lister/switcher/supprimer un vault
  2. Chaque vault est un namespace isole avec son propre index et graphe
- **Scenarios alternatifs** :
  - [SA-01] Suppression d'un vault non vide → confirmation requise
  - [SA-02] Recherche cross-vault → option explicite
- **Postcondition** : Vault gere, isolation maintenue
- **Regles metier** : RM-12

### [CU-07] Consulter les statistiques
- **Acteur** : LLM client via MCP ou utilisateur via CLI
- **Precondition** : Fougasse operationnel
- **Scenario nominal** :
  1. Appel `fougasse_status` ou CLI `fougasse status`
  2. Retourne : nombre de memoires, taille DB, sante graphe, memoires actives/declinantes, latence moyenne
- **Postcondition** : Information retournee
- **Regles metier** : RM-13

### [CU-08] Declin et consolidation automatique
- **Acteur** : Systeme (processus periodique)
- **Precondition** : Memoires existantes avec historique d'acces
- **Scenario nominal** :
  1. Processus periodique (configurable) evalue la vitalite de chaque memoire
  2. Memoires non accedees declinent progressivement (ACT-R / Ebbinghaus)
  3. Memoires frequemment accedees sont consolidees (score renforce)
  4. Memoires sous le seuil de vitalite sont archivees (pas supprimees)
  5. Consolidation : fusion de memoires redondantes, mise a jour du graphe
- **Scenarios alternatifs** :
  - [SA-01] Memoire archivee retrouvee par une recherche → "resurrection" (boost de vitalite)
- **Postcondition** : Vitalite mise a jour, memoires archivees si necessaire
- **Regles metier** : RM-14, RM-15

### [CU-09] Detecter et gerer les contradictions
- **Acteur** : Systeme (a l'ecriture)
- **Precondition** : Nouvelle memoire poussee
- **Scenario nominal** :
  1. A l'ingestion, Fougasse compare semantiquement avec les memoires existantes du meme domaine
  2. Si contradiction detectee, cree un lien `supersedes` de la nouvelle vers l'ancienne
  3. Retourne un warning au LLM appelant
- **Scenarios alternatifs** :
  - [SA-01] Contradiction ambigue → les deux memoires coexistent avec un lien `conflicts_with`
- **Postcondition** : Coherence du graphe maintenue, contradictions tracees
- **Regles metier** : RM-16

### [CU-10] Exporter / Importer des memoires
- **Acteur** : Utilisateur via CLI
- **Precondition** : Fougasse operationnel
- **Scenario nominal** :
  1. Export : `fougasse export` → fichier JSON/Markdown
  2. Import : `fougasse import <file>` → ingestion avec re-embedding
- **Scenarios alternatifs** :
  - [SA-01] Import de format inconnu → erreur descriptive
  - [SA-02] Conflit d'ID a l'import → re-generation d'ID
- **Postcondition** : Donnees exportees/importees
- **Regles metier** : RM-17

## Regles metier
| ID | Regle | Justification |
|----|-------|---------------|
| RM-01 | Chaque memoire a un ID unique (UUID v7, ordonne temporellement) | Tri chronologique natif, pas de collision |
| RM-02 | Chaque memoire porte : content, type, tags[], vault, source_agent, created_at, updated_at, vitality_score | Tracabilite et retrieval multi-critere |
| RM-03 | Le type est fourni par le LLM appelant (texte, code, tache, rdv, idee, conversation, sujet) | Zero classification cote Fougasse |
| RM-04 | Chaque ecriture/mise a jour genere un embedding vectoriel | Recherche semantique toujours a jour |
| RM-05 | La recherche hybride combine 4 canaux : semantique, BM25, graphe, temporel | Precision maximale multi-signal |
| RM-06 | Les resultats sont fusionnes via Reciprocal Rank Fusion (RRF) | Methode prouvee, sans hyperparametres |
| RM-07 | Un acces en lecture incremente le compteur d'acces de la memoire (vitalite) | Le declin est base sur la frequence d'acces |
| RM-08 | Le graphe relie les memoires par : tags partages, entites communes, liens explicites, proximite semantique | Navigation et decouverte de connexions |
| RM-09 | Les mises a jour preservent l'historique (versioning) | Tracabilite, rollback possible |
| RM-10 | La suppression soft-delete par defaut (flag `archived`) | RGPD Article 17, securite |
| RM-11 | Les noeuds critiques du graphe (points d'articulation Tarjan) generent un warning avant suppression | Protection de la coherence du graphe |
| RM-12 | Les vaults sont des namespaces isoles : index, graphe et stockage separes | Isolation sans filtres faillibles |
| RM-13 | Les stats incluent : count, size_db, active_count, declining_count, avg_latency | Monitoring de sante |
| RM-14 | Le declin suit le modele ACT-R : vitality = sum(t_i^-d) avec d = 0.5 | Science cognitive prouvee, pas de TTL arbitraire |
| RM-15 | Seuil d'archivage configurable (defaut : vitality < 0.1) | Adaptable au volume et a l'usage |
| RM-16 | La detection de contradictions utilise la similarite semantique (seuil configurable) + inversion de sens | Heuristique simple avant Sheaf Cohomology |
| RM-17 | L'export produit du JSON structure avec metadata complete | Portabilite, backup, migration |

## Modele de donnees metier

```
[Memory] 1──N [Tag]
    |
    1──N [MemoryVersion]
    |
    N──N [Memory]  (liens graphe : relates_to, supersedes, conflicts_with)
    |
    N──1 [Vault]
    |
    N──1 [Agent]   (source_agent)
    |
    1──1 [Embedding]
    |
    1──N [Entity]  (entites extraites, noeuds du graphe)
         |
         N──N [Entity] (relations inter-entites)
```

## Exigences non-fonctionnelles
| Categorie | Exigence | Priorite |
|-----------|----------|----------|
| Performance | Latence retrieval < 50ms P50, < 200ms P95 | P0 |
| Performance | Ingestion d'une memoire < 100ms (hors embedding) | P0 |
| Performance | Embedding local < 30ms par chunk sur M1 Pro | P0 |
| Performance | Support 100K+ memoires sans degradation | P0 |
| Stockage | Taille DB < 4Go pour 100K memoires | P0 |
| Securite | Zero donnees en transit reseau (sauf API embedding optionnelle) | P0 |
| Securite | Provenance tracee pour chaque memoire | P0 |
| Securite | Soft-delete par defaut, hard-delete explicite | P0 |
| Portabilite | Cross-platform : macOS ARM, Windows x64, Linux x64 | P0 |
| Portabilite | Installation en 1-2 commandes (pip install ou binaire) | P1 |
| Maintenabilite | Codebase lisible par un dev solo | P0 |
| Maintenabilite | Tests automatises sur les 3 plateformes | P1 |
| Fiabilite | Pas de perte de donnees en cas de crash (WAL, transactions) | P0 |
| Fiabilite | Indexation incrementale (pas de re-indexation complete) | P0 |
| Internationalisation | Docs/README en francais, code/CLI en anglais | P1 |

## Contraintes de securite (Security by Design)
- **Donnees sensibles** : conversations privees, idees de projets, code source, RDV, taches — tout est potentiellement sensible
- **Authentification** : non applicable (single-user, local only). Le serveur MCP ecoute uniquement en local (stdio ou localhost)
- **Autorisation** : isolation par vaults. Pas de RBAC (single-user)
- **Surface d'attaque** : serveur MCP stdio (pas de port reseau sauf SSE optionnel sur localhost), fichiers SQLite sur disque
- **Conformite** : RGPD-friendly (droit a l'oubli via soft/hard delete, export des donnees, separation donnees comportementales)
- **Chiffrement** : optionnel au repos (SQLite Encryption Extension ou sqlcipher). Zero transit reseau par defaut
- **Provenance** : chaque memoire porte source_agent, created_at, protocol, modification_history

## Priorites
| Priorite | Fonctionnalites |
|----------|----------------|
| P0 (MVP) | Serveur MCP (remember/recall/forget/status), stockage SQLite + embeddings, recherche hybride (semantique + BM25), vaults, CLI admin, provenance |
| P1 (intelligence) | Graphe de connaissances, retrieval 4 canaux (+ graphe + temporel), detection contradictions, Zettelkasten (liens auto), reranking |
| P2 (vitalite) | Moteur de declin ACT-R, consolidation, archivage auto, versioning memoires, export/import, sleep consolidation |
| P3 (avance) | Exploration du graphe, statistiques avancees, dashboard admin, benchmarks integres, scoring de confiance par agent |
