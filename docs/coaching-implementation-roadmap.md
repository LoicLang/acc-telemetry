---
summary: execution entry point for a verified one-corner coaching dossier with visual reference, reliability prerequisites, and separate replay research
read_when:
  - implementing the first usable ChatGPT coaching dossier
  - resuming the September 5 implementation plans
  - deciding what the user and agent must provide before reference comparison
---

# Du repo actuel au premier débrief utilisable

## Priorité approuvée le 9 septembre 2026

Le premier résultat produit est un **exercice utile sur un virage**, étayé par une
référence expliquée, les commandes et une vraie comparaison visuelle de placement.
La boucle est : passages personnels → dossier B revu → un exercice → nouveaux
passages comparables → vérification de son effet. Un export de courbes seul ne suffit
pas. Tant que le suivi n'a pas eu lieu, l'utilité reste `utility_not_yet_tested`.

Ordre retenu : terminer A en **1920×1080, exactement 60 fps CFR**, puis livrer B sur
un cas de Spa avec la même voiture. Cas proposé : Bruxelles, à confirmer dans les
images. Un deuxième circuit vient après ce premier cas pour éprouver la généralisation.
Les critères A restent obligatoires ; cette priorité ne les abaisse pas.

La mesure latérale métrique `d` n'est **ni un livrable ni un prérequis de B**.
B exige des images appariées aux repères physiques et une revue explicite des
constats de placement, avec abstention si caméra/FOV ou visibilité empêchent de
conclure. Après les premiers débriefs, consigner leurs limites récurrentes : si elles
justifient une mesure latérale, décider explicitement d'un petit test de faisabilité
du plan C. Un go n'autorise pas encore un modèle : géométrie, labels synchronisés,
erreur/couverture et validation PS5 indépendante doivent être établis.

Pendant A, préparer le choix du virage, le contexte et les sources de B est permis.
L'implémentation et le débrief comparatif chiffré B attendent le passage de Gate A.
Les échanges de brainstorming n'autorisent pas à lancer du code ou une extraction ;
terminer uniquement le travail explicitement demandé avant de reprendre la discussion.

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
| Après retour sur B, si besoin démontré | [Plan C — recherche replays](plans/2026-09-05-replay-spatial-feasibility.md) | Décision go/no-go sur `.rpy -> vidéo + labels` pour envisager `d/heading` | Décision explicite, puis labels et synchronisation démontrés avant tout modèle |

La [spécification commune](specs/2026-09-05-reference-corner-coach-design.md)
fixe les contrats et limites. Le plan A est le premier travail d'implémentation ; B
ne commence pas tant que son gate échoue. C est de la recherche séparée, non un
prérequis au débrief visuel. `current-status.md` et le plan actif portent l'avancement
vérifié ; ne pas recommencer les étapes A déjà livrées.

Le **plan C de recherche** est distinct du « gate C » de revue du coaching nommé
dans la spécification. Le suivi de l'exercice fait déjà partie de B9/B10.

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

Toutes les nouvelles vidéos, pilote comme référence, doivent respecter le format
1080p60 natif. Les anciennes preuves 720p restent historiques et ne sont plus traitées.

Trois rôles de source restent distincts :

- **Pilote pour B** : les captures 1080p existantes peuvent suffire ; trois passages
  complets minimum, cinq si disponibles, avec voiture et conditions documentées.
- **Référence pédagogique pour B** : même circuit/virage et voiture compatible,
  vidéo autorisée, auteur/lien conservés, HUD et pédales lisibles pour les deltas,
  explication technique sourcée ou revue compétente. Elle peut être préparée dès maintenant.
- **Validation indépendante pour A** : nouvel enregistrement distinct, gardé en
  réserve ; identité et code/config figés avant inspection. Il ne sert ni de terrain
  de réglage ni de référence pédagogique pendant les corrections.

L'agent prend en charge la revue des images existantes lorsqu'elle est fiable et
consigne son auteur séparément des approbations utilisateur. Les ambiguïtés donnent
lieu à une demande ciblée ; l'utilisateur n'a pas à annoter toutes les images d'emblée.

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
spécification commune et le plan actif indiqué par le handoff. Reprendre exactement
la prochaine action vérifiée, actuellement la revue de visibilité continue 1080p.
Conserver les gates en échec tant que leurs preuves manquent. Les cases ne sont
cochées qu'après vérification et commit de leur tâche.
