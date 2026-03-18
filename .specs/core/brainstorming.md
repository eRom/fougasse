# Brainstorming : core

**Date** : 2026-03-17
**Statut** : Decide
**Mode** : Nouveau projet

## Idee initiale
Fougasse est un serveur MCP local + moteur de memoire persistante qui centralise le contexte entre tous les clients LLM (Claude Desktop, Cruchot, Claude Code, Cursor, Windsurf...). Les LLM poussent des memoires structurees via des tools MCP, Fougasse les stocke localement, construit un graphe de connaissances dynamique, et restitue le contexte pertinent a la demande. Full local, open-source, francais.

## Hypotheses validees
- Le probleme est reel et quotidien : copier-coller entre clients LLM plusieurs fois par jour
- Fougasse est **passif a l'ecriture** : les LLM font la classification et la structuration au moment du push (zero pipeline d'ingestion cote Fougasse)
- La classification est gratuite car faite par le LLM appelant (pas de classificateur local necessaire)
- ~50K memoires/an est un volume realiste
- "Full local" = les donnees ne quittent jamais la machine. Un appel API ephemere optionnel (embedding) est acceptable
- Le dual MCP + CLI n'est plus necessaire : MCP est l'interface principale. Une CLI legere pour admin/debug suffit
- Fougasse est independant de Cruchot (pas de couplage)
- L'identite francaise = docs/README en francais, code en anglais
- Cross-platform obligatoire : Mac (M1 Pro dev), Windows, Linux

## Hypotheses rejetees
- Fougasse comme pipeline d'ingestion actif (extraction entites, detection emotions a l'ecriture) → rejete, les LLM font le travail
- CLI comme interface d'usage principale → rejete, MCP suffit, CLI pour admin seulement
- Prise en compte de Cruchot dans le design → rejete, projet independant
- Images et videos → explicitement exclus
- Classification par LLM local (Ministral) → inutile car le LLM appelant classifie au push

## Risques identifies
- **Over-engineering** : graphe de connaissances + moteur de vitalite + Sheaf Cohomology = complexe pour un dev solo. Risque de passer 8 mois sur le moteur cognitif sans l'utiliser
- **Cold-start embeddings** : re-indexation de 100K memoires sur M1 Pro = ~37 minutes. A prevoir dans le design (indexation incrementale obligatoire)
- **Cross-platform** : SQLite + embeddings ONNX doivent fonctionner identiquement sur Mac ARM, Windows x64, Linux x64
- **Modele d'embedding** : le choix du modele impacte toute la base. Changer de modele = re-indexer 100% des vecteurs
- **Qualite du retrieval** : sans LLM actif cote Fougasse, le retrieval depend de la qualite des embeddings + BM25 + graphe. Si ca ne suffit pas, il faudra ajouter un reranker

## Alternatives considerees
| Approche | Priorise | Sacrifie |
|----------|----------|----------|
| A — Coffre-fort intelligent | Simplicite, fiabilite, usage quotidien | Graphe, cognition, auto-reflexion |
| B — Cerveau local | Intelligence, connexions emergentes, challenge technique | Simplicite, temps de livraison |
| C — Evolutif par paliers | Usage reel guide le dev | Plan predefini |

## Decision retenue
**Approche B — Le cerveau local.** Fougasse est un moteur de memoire passif a l'ecriture mais actif a l'interieur : graphe de connaissances dynamique, Zettelkasten, declin cognitif, detection de contradictions. Motivation : challenge technique pour portfolio post-AVC, Romain a deja prouve avec Cruchot (28 services, 97/100 securite) qu'il livre du lourd.

## Prerequis avant implementation
1. Choix de stack definitif (Python vs TypeScript vs Rust)
2. Modele d'embedding local valide sur M1 Pro (latence + accuracy)
3. Schema de donnees capable de supporter graphe + vaults + temporalite
4. Validation que sqlite-vec ou equivalent fonctionne sur les 3 plateformes cibles
5. Prototype de serveur MCP minimal pour valider le flux LLM → Fougasse → LLM

## Hors scope (explicitement exclu)
- Images et videos
- Multi-utilisateurs (solo user seulement)
- Cloud storage / sync cloud
- Interface graphique web (sauf dashboard admin futur)
- Integration specifique a Cruchot
- Federation de memoire entre machines
- Appli mobile

## Contraintes de securite identifiees
- **Donnees sensibles** : conversations privees, idees de projets, code source, RDV, taches personnelles
- **Modele de menace** : empoisonnement de memoire par un agent malveillant (MemoryGraft, Sleeper Agents), acces non autorise aux fichiers locaux
- **Surface d'attaque** : serveur MCP local (stdio/SSE), fichiers SQLite sur disque
- **Conformite** : RGPD (droit a l'oubli, Article 17) — separation donnees comportementales
- **Chiffrement** : donnees au repos sur disque local (chiffrement optionnel), zero transit reseau
- **Provenance** : chaque memoire tracee (agent source, timestamp, protocole)
