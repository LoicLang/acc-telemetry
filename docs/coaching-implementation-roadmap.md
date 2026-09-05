---
summary: execution entry point for a verified one-corner coaching dossier with visual reference, reliability prerequisites, and separate replay research
read_when:
  - implementing the first usable ChatGPT coaching dossier
  - resuming the September 5 implementation plans
  - deciding what the user and agent must provide before reference comparison
---

# Du repo actuel au premier débrief utilisable

## Résultat concret à livrer

Un dossier local pour **un virage de Spa**, avec tes passages et un passage de
référence : tableaux vitesse/frein/gaz, comparaison des événements, images cockpit
aux mêmes repères, explication sourcée de la référence et consigne prête à envoyer
à ChatGPT. Un diagnostic de placement exige ces images et leur revue ; les courbes
de pédales seules ne l'autorisent pas.

Commande cible, à implémenter (elle n'existe pas aujourd'hui) :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.coaching \
  build --case data/lab/coaching-spa-bruxelles/case.yaml \
  --output data/lab/coaching-spa-bruxelles/reports/run-001
```

Sortie attendue :

```text
run-001/
  START_HERE.md             quoi joindre à ChatGPT et dans quel ordre
  coach_prompt.md           demande exacte et limites du diagnostic
  dossier.md                contexte, mesures, référence, preuves et limites
  evidence.json             mêmes faits avec types, unités, statuts et identifiants
  metrics.csv               une ligne par passage et métrique
  comparison.html           revue locale des courbes et images côte à côte
  images/                   paires pilote/référence, lisibles sans outil spécifique
  clips/                    extraits individuels à vitesse réelle
  provenance.json           hashes des entrées, code, config et transformations
```

ChatGPT ne peut pas ouvrir les chemins locaux de ce dossier. L'utilisateur joint
`dossier.md`, `evidence.json` et les PNG explicitement listés dans `START_HERE.md`,
puis colle `coach_prompt.md`. Les clips servent à la revue humaine et peuvent être
joints si l'interface utilisée les accepte ; aucune capacité vidéo n'est supposée.

## Découpage et dépendances

| Ordre | Plan | Livrable | Condition pour continuer |
| --- | --- | --- | --- |
| 1 | [A — fiabilité](plans/2026-09-05-coaching-reliability.md) | Observations fiables, exports sans perte et benchmark indépendant | Rapport de gate A validé, défauts audit couverts par tests |
| 2 | [B — virage + référence](plans/2026-09-05-reference-corner-dossier.md) | Dossier réel vérifié et premier exercice | Référence et images présentes, nombres traçables, revue humaine |
| Séparé | [C — faisabilité replays](plans/2026-09-05-replay-spatial-feasibility.md) | Décision go/no-go sur `.rpy -> vidéo + labels` | Labels et synchronisation démontrés avant tout dataset ML |

La [spécification commune](specs/2026-09-05-reference-corner-coach-design.md)
fixe les contrats et limites. Le plan A est le premier travail d'implémentation ; B
ne commence pas tant que son gate échoue. C est de la recherche séparée, non un
prérequis au débrief visuel. L’exécution A0/A1 est maintenant autorisée ; `current-status.md` et les cases
du plan A portent l’avancement vérifié.

## Qui fait quoi

| Sujet | Agent | Utilisateur / personne compétente |
| --- | --- | --- |
| Vidéo pilote | Vérifie capture, hash et profil, extrait les mesures | Confirme voiture et contexte inconnus |
| Référence | Inspecte les fichiers fournis et leur comparabilité ; dresse une liste des éléments manquants | Fournit une vidéo autorisée et une explication de conduite, ou choisit une source à acquérir |
| Repères | Prépare les images et un fichier d'annotations | Valide les mêmes repères physiques sur pilote et référence |
| Qualité | Calcule les scores sur annotations indépendantes | Vérifie les annotations et les images dégradées |
| Trajectoire | Présente des images appariées, consigne les observations | Valide les constats de placement ; un avis technique compétent reste nécessaire pour valider une causalité |
| Débrief | Produit dossier, prompt, formulaire d'évaluation et liens de preuves | Joint les fichiers à ChatGPT, vérifie le retour et réalise l'exercice |

Le plan n'autorise pas un achat, une publication, un message à un fournisseur ou un
entraînement ML massif. Une référence manquante bloque le **débrief comparatif réel**,
pas les tests synthétiques du logiciel après le gate A. Ne jamais la remplacer par
un tour inventé ou présenter le meilleur passage personnel comme une trajectoire idéale.

## Choix de départ explicites

- Cas proposé : Spa / Bruxelles, voiture identique à la capture pilote. Confirmer
  visuellement le virage et le modèle avant de figer le cas. Le logiciel reste générique.
- Capture pilote candidate : `/Users/loiclang/Movies/2026-09-03 22-42-08.mov`,
  `ps5_full_map_1080p`, déjà utilisée pour la validation BMW. Le fichier existe.
- Sélectionner trois passages complets au minimum, cinq si la capture le permet.
  Les premières images d'un tour partiel ne deviennent pas une référence de tour.
- Une référence peut être une vidéo seule avec HUD lisible : on applique la même
  extraction après calibration du profil. Une télémétrie native est optionnelle et
  nécessite un import explicite avec unités et synchronisation ; aucun parseur MoTeC
  ou `.rpy` n'est nécessaire au plan B.
- Sans HUD de référence exploitable, fournir seulement une comparaison visuelle et
  les mesures personnelles ; marquer le dossier `visual_only`, sans deltas de commandes.
- Les positions de repères sont annotées dans les images. Le `s` générique sert à
  vérifier/retrouver une zone, pas à inventer des mètres ni à recaler des circuits
  provenant de sources différentes sans preuve.

## Les sept métriques et leur unité

| Métrique | Définition v1 |
| --- | --- |
| Temps du segment | `exit_time - entry_time`, secondes, deux repères physiques identiques |
| Début de freinage | Instant du premier épisode de frein validé, relatif à l'entrée du segment |
| Relâchement principal | Durée entre le dernier passage descendant à 80% du pic et celui à 20%, dans le même épisode ; non disponible si épisode ambigu |
| Temps sans pédales | Durée observée avec frein et gaz sous les seuils d'inactivité |
| Vitesse minimale | Minimum des observations admises dans le segment ; indisponible si la couverture ne permet pas de comparer les minima |
| Remise des gaz | Premier épisode soutenu après le freinage, plus nombre de relâchements observés jusqu'à la sortie |
| Vitesse de sortie | Valeur au repère de sortie, interpolée seulement entre observations proches et qualifiées |

Trajectoire v1 : observations visuelles entrée / milieu / sortie, avec statut
`unreviewed`, `human_observed` ou `indeterminate`. Aucun `d` en mètres, pourcentage de
largeur physique, angle de dérive ou « turn-in 7 m trop tôt » n'est produit.

## Première action pour le futur agent

Lire `AGENTS.md`, lancer `./scripts/docs-list`, lire `docs/current-status.md`, la
spécification commune puis le plan A. Exécuter **A0**, puis **A1** (OCR brut).
Conserver les gates en échec tant que leurs preuves manquent. Les cases ne sont
cochées qu'après vérification et commit de leur tâche.
