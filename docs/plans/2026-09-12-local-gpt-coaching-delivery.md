---
summary: detailed local-only delivery plan from verified extraction to a portable evidence-backed GPT coaching dossier and one tested exercise
read_when:
  - resuming the owner's request for a genuinely usable GPT coaching report
  - choosing the next implementation lot after run-024
  - deciding whether measurement work is necessary for the first coaching dossier
---

# Plan de livraison local : un dossier réellement exploitable par GPT

**12 septembre 2026 — plan demandé, exécution non commencée.**
Dernière consigne du propriétaire : préparer uniquement le plan, ne pas implémenter.
L’essai manuel de lecture/coaching demandé a servi à préciser ce plan ; il ne vaut
ni développement B, ni dossier validé. Voir `../gpt-coaching-report-trial.md`.
Base auditée : `f4c43ed`, run-024. Audit : `../gpt-coaching-readiness-audit.md`.
Spécification produit : `../specs/2026-09-05-reference-corner-coach-design.md`.
Contrat de mesure : `../signal-treatment.md` et `../capture-validation.md`.
Le plan B du 5 septembre reste la référence technique des calculs ; ce document
fixe l'ordre opérationnel, les livrables, les limites et les décisions de sortie.

**Périmètre impératif : tout se construit localement.** Le pilote joint lui-même les
fichiers à GPT. Aucun travail sur FastAPI, upload, hébergement, connexion API GPT ou
interface web. Un HTML local peut aider notre revue ; le dossier envoyé est autonome.
Aucune fusion vers main. Aucun sous-agent ni campagne exhaustive sur BMW/incidents.
La consultation de sources pédagogiques publiques sert à qualifier une référence ;
elle ne réintroduit pas un service web dans le produit local.

## 1. Définition précise de terminé

Un premier résultat exploitable est un dossier sur **un seul virage**, contenant :

- trois passages personnels complets minimum, même voiture/contexte documenté ;
- une référence réelle et expliquée, ou un statut explicitement limité sans cible normative ;
- les mêmes repères physiques d'entrée, milieu et sortie, illustrés ;
- des métriques calculées par le code, leurs incertitudes et les données absentes ;
- des courbes statiques lisibles et des images de trajectoire pilote/référence ;
- un prompt qui demande à GPT un diagnostic argumenté et **un seul exercice** ;
- une réponse GPT relue, dont chaque chiffre et constat peut être rattaché aux preuves.

Le dossier complet n'est pas obtenu en exportant un CSV ou en générant un prompt.
Après livraison, le pilote réalise l'exercice ; son effet est mesuré lors de passages
comparables. Avant cela, statut `utility_not_yet_tested`, aucune efficacité revendiquée.

Candidat issu de l'essai réel : **famille McLaren 720S GT3, fin des Combes/Malmedy à Spa**.
Le cockpit et les huit images d'approche l'étayent ; la variante d'origine/EVO, le
matériel et les limites physiques exactes restent à confirmer. Le rapport initial
ne donnait pas ce contexte. L'ancien choix BMW/Bruxelles reste une option historique,
pas une sélection à imposer à une autre vidéo. Proposition de périmètre à fixer au
lot 0 : entrée des Combes jusqu'à la sortie de Malmedy, avec une priorité unique sur
la préparation du dernier droit. Distinguer la zone de mesure de son contexte vidéo ;
confirmer l'applicabilité des métriques avant tout code, sans inventer un freinage
obligatoire dans un passage qui n'en aurait pas. Les trois passages admissibles et la
référence ne sont pas encore sélectionnés. Un incident peut servir au diagnostic,
mais ne devient pas un passage propre dans les statistiques de régularité.

### Test central de qualité du rapport

Le premier essai a échoué pour un coaching spécifique complet : l'extrait d'incident
commence déjà dans les graviers, les passages ne sont pas alignés, la voiture/contexte
sont incomplets et les « références » noires ne sont que des contrôles d'extraction.
Huit images source supplémentaires montrent pourquoi l'approche complète change
l'analyse ; aucune causalité exacte ni faiblesse répétitive n'est encore prouvée.

À chaque itération utile, le modèle devra lire le rapport et répondre à ces questions :
**quelle faiblesse, quelles preuves, quelle comparaison, quelles causes alternatives,
quelle correction praticable et quel test de réussite ?** Une réponse vague ou obligée
d'inventer une pièce manque ce test. Ajouter la pièce manquante nommée, puis recommencer ;
le nombre de fichiers, de tests ou de tours analysés ne remplace pas cette acceptation.
Le modèle peut proposer une hypothèse de travail honnête ; il ne doit pas présenter
une cause indéterminée comme un diagnostic établi.

## 2. Ce que l'on conserve, ce que l'on arrête

Conserver l'extraction automatique complète, les artefacts telemetry-v2, les valeurs
fraîches, les nulls, les revues de compteur, les annotations existantes et les seuils
d'acceptation. Les annotations servent à vérifier les sorties, pas à limiter toute
l'extraction à quelques secondes. Une source hors 1920×1080 exactement 60 fps CFR est refusée.

Ne plus refaire les revues du compteur, réextraire pour modifier un graphique, choisir
les réglages sur une capture indépendante, masquer un trou par lissage ou laisser GPT
inventer les mesures. Ni `d` en mètres, ni TC/ABS, ni précision spatiale générale ne
sont un objectif v1. Le `s` estimé peut aider la navigation ; l'alignement du dossier
se fait sur des repères physiques et les horodatages, sans attendre un `s` parfait.

## 3. Livrable final, dossier portable

Arborescence cible, **pas encore produite** :

```text
case-spa-001/
  envoi_gpt/
    A_LIRE.md                 ordre des pièces, objectif, limites et liste des images
    DOSSIER.md                rapport autonome en français
    PREUVES.json              faits structurés avec unités, statuts et identifiants
    METRIQUES.csv             3 passages + référence, valeurs/erreurs/couverture
    PROMPT_GPT.txt             question précise, citations de preuves et exercice unique
    images/
      courbes_*.png            vitesse/frein/gaz, repère commun, trous visibles
      trajectoire_*.png        entrée/milieu/sortie, sources et temps identifiés
  revue_locale/
    comparison.html           navigation facultative, jamais nécessaire pour lire le dossier
    clips/                    extraits à vitesse réelle pour notre vérification
    segments.csv              données à 60 Hz des seuls passages retenus, sans décimation
    provenance.json           hashes, configuration, versions, sources et transformations
    coach-review.json         vérification de la réponse obtenue
```

`DOSSIER.md` contient dans cet ordre : objectif et contexte ; sources/conditions ;
qualité et capacités permises ; définition des passages/repères ; tableau des mesures ;
comparaison descriptive ; observations visuelles revues ; incertitudes et questions.
Objectif de lisibilité : environ 3–5 pages de texte/tableaux, un cas, au plus 12 PNG.
Ce sont des budgets de conception, pas des limites annoncées de GPT.

`PREUVES.json` sépare `measurements`, `comparisons`, `visual_observations`,
`limitations`, `unsupported_claims` et `evidence`. Chaque métrique garde son unité,
source/passage, champ requis, temps/frame, couverture, erreur et raison si null.
Les images utilisent des identifiants stables (`IMG-entry-01`, etc.). Les fichiers
à envoyer ne nécessitent aucun chemin absolu de notre ordinateur, dépôt ou ancien chat.
Les exports bruts complets restent locaux ; une archive est facultative pour transporter
le dossier, sans supposer que GPT pourra exploiter ses éléments sans pièces accessibles.

## 4. Chemin critique et travaux préparables

```text
Lot 0 : contexte, passages, référence candidate et essai manuel du rapport
  -> Lot 1 : clore les défauts de mesure nécessaires
  -> Lot 2 : gel + validation indépendante + décision Gate A
  -> Lot 3 : passages, événements et métriques d'un virage
  -> Lot 4 : preuves visuelles + export portable
  -> Lot 5 : essai réel avec GPT + revue de sa réponse
  -> Lot 6 : exercice du pilote + contrôle à la séance suivante
```

Le lot 0 commence par la préparation du cas et peut continuer pendant les lots 1–2.
La lecture critique manuelle du rapport est autorisée pendant A ; elle ne produit
pas une implémentation B ou une certification du coaching.
**Les lots3–5 implémentant B restent bloqués tant que Gate A échoue.** Le plan ne
supprime pas ce préalable et n'invente pas un nouveau gate plus faible. Pas de code B
« provisoire » pour contourner la règle. Les maquettes/documentations ne portent pas
le statut d'un dossier validé.

### Lot 0 — Préparer le cas et la référence, tester le rapport avant de coder B

- [ ] Confirmer Spa/virage/voiture et relever trois passages propres avec entrée et
  sortie visibles. Écarter les tours partiels/erreurs majeures pour le cas principal,
  tout en conservant l'incident comme exemple de limitation, pas comme tour idéal.
- [ ] Relever session, météo, setup si connu, pneus/carburant et caméra ; inconnu reste
  inconnu. Obtenir une référence autorisée du même virage avec une voiture comparable
  et une explication technique fournie ou revue. Une vidéo rapide ne suffit pas à
  justifier une recommandation normative.
- [ ] Séparer trois rôles : vidéo pilote pour le dossier, référence pédagogique,
  capture indépendante de validation. Ne pas inspecter le holdout pour choisir le cas.
- [ ] Si une preuve réelle de HUD absent manque au développement, demander uniquement
  un court extrait de calibration séparé (menu/HUD visible), avant gel. Ne pas utiliser
  les négatifs du futur holdout pour régler le lecteur.

**Livrable :** fiche de contexte, sources candidates, repères proposés, pièces manquantes.
Le contexte McLaren/Les Combes de l'essai réel est prioritaire pour ce candidat ; la
capture BMW reste distincte. Une référence pédagogique publique a été repérée, ainsi
qu'une publication McLaren/Spa de Nils Naujoks datant d'ACC 1.9.0 en 2023. Ce sont des
pistes, pas des données de référence acquises/compatibles : voir le compte rendu du
test. Privilégier un passage de course/relais comparable et expliqué, en vérifiant
voiture/variante, version/BoP, pneus, carburant, météo, setup et lisibilité du HUD.
Ne pas transposer un chrono de qualification ou de version ancienne en objectif.
La référence n'est jamais admise sur la seule présence d'une URL.

### Lot 1 — Fermer la fiabilisation utile, sans rouvrir toute la vidéo

**Responsable : agent, avec question utilisateur seulement sur un fait réellement ambigu.**

- [ ] Écrire une matrice courte des six contrôles A : preuves actuelles, preuves encore
  incompatibles/manquantes, défaut reproduit et action unique pour chacun. Réutiliser
  run-024 pour les résultats et les annotations run-021/022 pour le compteur.
- [ ] Vérifier la géométrie des barres sur les points déjà annotés : plein gaz 94,12%,
  zéro résiduel et niveaux intermédiaires. L'hypothèse « largeur de ROI/largeur utile »
  doit être démontrée avant correction. Corriger au niveau du lecteur/configuration,
  jamais par min/max de session ou multiplication choisie pour obtenir 100%.
- [ ] Ajouter les régressions ciblées avant toute correction ; vérifier 0/100,
  intermédiaires, attaques, relâchements et blips, sans lissage. Si aucune correction
  fiable n'est établie dans le lot borné, conserver le biais et interdire les conseils
  sur le plein gaz/les faibles résidus ; l'exactitude parfaite des extrêmes n'est pas
  un nouveau seuil de Gate A. Les cibles de mesure existantes restent obligatoires.
- [ ] Qualifier l'admission du HUD en mode automatique sur développement : ROI vide,
  noire, uniforme, interface/menu et HUD réel. Le test gris de l'audit montre une limite.
  Introduire uniquement une vérification de présence démontrée ; pas de grand modèle
  ou de campagne de recherche. Un panneau coloré quelconque ne vaut pas visibilité.
- [ ] Préserver explicitement les échecs sur impact et V-CRASH-15. Examiner uniquement
  leurs lectures/crops conservés ; aucune recherche de seuil pour verdir 95% et aucune
  suppression opportuniste du segment. Si le défaut empêche les critères applicables,
  le gate reste en échec avec une cause nommée ; un taux global ne le masque pas.
- [ ] Figer les choix techniques après les tests ciblés et le full suite. Faire au plus
  un replay final par source de développement réellement affectée par les changements
  de mesure. Ne pas relancer de source pour les seuls rapports/docs/calculs aval.

**Fichiers :** `extraction/controls.py`, `extraction/laps.py`, `application/pipeline.py`,
`application/speed_admission.py` uniquement si un défaut y est démontré ; réglages dans
`config/roi_config.yaml` / `config/telemetry.yaml`. Réutiliser les tests des mesures
fraîches et du mode automatique. Aucun changement de cible dans `config/validation.yaml`.

**Livrable :** `measurement-closeout.md` + comparatif avant/après sur les mêmes références,
régressions, exclusions autorisées et empreinte gelée. Statut « prêt à tester ailleurs »
ou blocage exact. Deux tentatives fondées sur une cause au maximum par défaut ; en cas
d'échec, décision documentée, sans troisième campagne improvisée. Ce plafond limite
l'expérimentation ; il n'autorise pas à déclarer un critère satisfait.

### Lot 2 — Une validation indépendante bornée, avec une vraie décision

**Responsabilités :** pilote fournit la nouvelle capture ; agent prépare le protocole,
les fichiers et le calcul ; revue source séparée des sorties numériques.

- [ ] Réserver une nouvelle capture distincte **après gel** : hash, `recording_id`,
  profil/mode/code/config et critères avant inspection. Le holdout run-008 reste
  historique ; une découpe d'une capture connue n'est pas une nouvelle indépendance.
- [ ] Rester au premier périmètre Spa, même voiture/HUD si possible, au moins trois
  tours/passage utiles, format natif 1080p60 CFR. Pas besoin d'un second circuit pour
  cette première admission de cas ; aucune généralisation inter-circuits revendiquée.
- [ ] Fixer la sélection des tests avant lecture des prédictions. Réutiliser les labels
  natifs existants : cible du corpus au moins100 lectures chiffrées par champ, 20 images
  dégradées, 20 fenêtres d'événement, rôles développement/holdout distincts et au moins
  deux passages physiques par source selon le contrat courant. Avec 40 points natifs
  réutilisables, prévoir au moins 60 nouveaux triplets vitesse/frein/gaz ; vérifier les
  vrais dénominateurs, sans recompter un label partagé. Des points ajoutés ne prouvent
  pas une précision numérique entre eux.
- [ ] Inclure les situations qui changent les conseils : freinage plein/dégressif,
  reprise gaz soutenue, coupure/blip, vitesse basse/zéro, sortie de piste et HUD absent.
  Les cas absents du corpus restent non évalués ; ne pas les appeler réussis.
- [ ] Annoter les valeurs et bornes temporelles depuis la vidéo avant consultation des
  sorties, puis figer les labels. Pour les tours, établir les transitions dans l'ordre
  source indépendamment des prédictions ; réutiliser la vérité complète des anciennes
  captures sans nouvelle revue. Pas de qualification de réviseur ni de revue de chaque
  image de la session pour les autres champs.
- [ ] Traiter la capture entière une fois en automatique, puis lancer la validation
  sur annotations. Comparer sans changer le code ni les seuils pendant ce test.
- [ ] Assembler les six contrôles compatibles de Gate A, avec les statuts manquants
  explicites. En cas d'échec, écrire un diagnostic unique ; la capture devient donnée
  de développement pour la correction, jamais à nouveau un holdout vierge.

**Cibles inchangées :** vitesse MAE≤2km/h/P95≤5km/h ; pédales MAE≤5 points ; événements
P95≤0,10s ; disponibilité≥95% dans le périmètre défini ; pas de mesure fraîche sur HUD
annoté absent ; temps et fraîcheur cohérents. Les 20 fenêtres doivent conserver les
bonnes sémantiques : une remise à100% n'est pas une reprise à5%, et un début de
relâchement n'est pas le franchissement descendant de5%.

**Livrable :** capture réservée + labels figés + `gate-a.json` compatible + une page de
décision. Sortie : les six contrôles passent avant B. On n'essaie pas cinq nouveaux
algorithmes sur la capture de validation. Une absence de capture bloque ce lot, pas
la préparation documentaire du cas et de la référence.

### Lot 3 — Transformer les passages en faits calculés (après Gate A)

- [ ] Créer le manifeste du cas : sources/hashes, rôle, conditions, artefacts, passages,
  repères physiques, visibilité/validité du cas et empreinte de gate compatible.
  `observed` seul n'autorise pas une métrique : vérifier les raisons, le gate et la
  couverture des champs du passage. Les annotations de cas contrôlent la validité
  des mesures ; elles ne réintroduisent pas une extraction sparse de toute la vidéo.
- [ ] Fixer entrée/milieu/sortie au même repère physique pour tous les passages. Garder
  les bornes de frames possibles ; ne pas aligner les pics de frein ou les minima de
  vitesse, ce qui effacerait les différences à expliquer.
- [ ] Implémenter les épisodes frein/gaz avec persistance et hystérésis validées selon
  B4 : préserver les samples, couper aux trous, dater début candidat et confirmation
  séparément, marquer les épisodes tronqués/ambigus. Les blips restent dans la courbe,
  sans devenir automatiquement une remise volontaire des gaz.
- [ ] Calculer les sept métriques et leurs preuves, selon le tableau ci-dessous. Réutiliser
  les artefacts ; aucun nouvel OCR si le lecteur/code de mesure n'a pas changé.
- [ ] Comparer les trois passages personnels et la référence avec médiane/dispersion,
  incertitude et statuts `available`, `unavailable`, `not_comparable`. Un meilleur
  passage personnel sert à étudier la régularité, pas à inventer une ligne idéale.

| Métrique | Calcul/unité | Refus obligatoire |
| --- | --- | --- |
| Temps du segment | Sortie−entrée, secondes, bornes des deux repères | Repères différents/incomplets |
| Début de freinage | Premier épisode confirmé depuis l'entrée, secondes | Déjà actif à l'entrée, trou ou borne inconnue |
| Relâchement principal | Durée 80→20% du pic après dernier pic principal | Remontée ambiguë, signal interrompu, épisode tronqué |
| Temps sans pédales | Somme des durées réellement observées sous les seuils | Ne pas extrapoler la portion manquante |
| Vitesse minimale | Minimum observé du passage | Trou pouvant cacher un minimum ; pas de valeur estimée déguisée |
| Remise des gaz | Premier épisode soutenu après freinage + interruptions | Blip isolé, absence ou ambiguïté de l'épisode |
| Vitesse de sortie | Lecture au repère ou interpolation bornée qualifiée | Extrapolation/gap trop long |

Pour un premier dossier complet, exiger au minimum temps du segment, début de freinage,
remise des gaz et vitesse de sortie sur les trois passages et la référence. Les autres
métriques peuvent être nulles avec raison ; toutes absentes n'est jamais « complet ».
Les deltas temporels restent des secondes depuis un repère, jamais des mètres. Les
causes techniques nécessitent la référence expliquée et la revue visuelle.

**Fichiers :** `domain/coaching.py`, `application/coaching_config.py`,
`application/coaching_case.py`, `analysis/corner_events.py`, `corner_metrics.py`,
`corner_comparison.py`, `config/coaching.yaml`. Implémenter le minimum des tâches
B1/B3–B6, avec tests de valeurs connues, trous aux événements, incertitudes et contextes
incompatibles ; pas d'architecture SaaS ni de généralisation anticipée.

**Livrable :** tableau concret des trois passages/référence et `PREUVES.json` relisant
les données sources. Chaque valeur doit être reproductible par le code sans GPT.

### Lot 4 — Produire les pièces que GPT pourra réellement examiner

- [ ] Générer les PNG de courbes depuis les mêmes données que les métriques, à temps
  relatif au repère ; vitesse/frein/gaz séparés, passage/référence nommés, trous visibles.
- [ ] Générer les images appariées entrée/milieu/sortie en conservant la scène cockpit,
  complétées si utile par le HUD et un contexte d'événement. Garder la frame source,
  le temps, le rôle et les limites FOV/caméra ; aucune distance latérale inventée.
- [ ] Rédiger les observations visuelles comme `reviewed` ou `indeterminate` ; un score
  d'OCR ou une courbe de pédale ne valide pas une trajectoire. Ne pas attribuer un blip
  automatique à une décision volontaire du pilote.
- [ ] Assembler l'arborescence de la section3 via une commande locale versionnée, avec
  sorties atomiques et refus d'écraser source/ancien dossier. Le générateur devient
  du code réutilisable ; les fichiers personnels restent ignorés par Git.
- [ ] Faire un contrôle de portabilité : copier `envoi_gpt/` dans un dossier vide et
  vérifier que les faits, images, identifiants, unités et limites se comprennent sans
  repo, HTML interactif, localhost ou conversation précédente.
- [ ] Distinguer `ready`, `limited`, `draft`. Sans référence expliquée, fournir au mieux
  un dossier de régularité personnelle `limited` sans norme de trajectoire ; ne pas
  annoncer que l'acceptation B avec référence est atteinte. Pas de cible chiffrée
  comparative si la mesure/profil de la référence n'a pas été qualifié.

**Fichiers :** `application/coaching_media.py`, `visualization/coaching_dossier.py`,
`adapters/coaching.py`. Fonctions métier hors adaptateur ; réutiliser les lecteurs
A4, l'interpolation bornée et FFmpeg pour les médias. Tests réels des index/temps sur
petites vidéos synthétiques, cohérence JSON/CSV/PNG et absence de sortie partielle.

Commande **cible, non existante aujourd'hui** :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.coaching build \
  --case PATH_TO_CASE_YAML --output NEW_DIRECTORY --require-complete
```

**Livrable :** un premier dossier attachable, ouvert et vérifié. L'agent livre aussi
la liste exacte des pièces à joindre, pas une URL locale censée être accessible à GPT.

### Lot 5 — Tester le dossier avec GPT, pas seulement le générateur

- [ ] Faire un essai dans une conversation sans historique du projet. Le pilote joint
  les pièces indiquées ; aucun envoi automatique de fichiers par l'agent.
- [ ] Le prompt demande d'identifier les pièces lues, citer les IDs des mesures/images,
  séparer faits/hypothèses/inconnues, choisir une priorité, proposer un exercice et un
  critère de réussite mesurable. Interdire chiffres inventés, mètres issus de `s`,
  cause certaine à partir des pédales seules et conclusion sur 100% non qualifié.
- [ ] Relire la réponse : chaque nombre correspond à une mesure, chaque observation de
  placement à une image, les incertitudes empêchent les faux « plus tôt/plus tard ».
  Un commentaire vague sans exercice applicable n'est pas une réussite.
- [ ] Si GPT manque de contexte, consigner la conclusion impossible et la pièce qui
  manque, compléter uniquement cette pièce, puis refaire l'essai. Ne pas modifier les
  données pour obtenir une réponse agréable. Conserver chaque réponse et sa revue.
  Continuer jusqu'au critère d'exploitabilité ou jusqu'à une dépendance externe précise
  et documentée ; aucun nombre arbitraire de tentatives ne rend le rapport terminé.

**Livrable :** réponse réelle + `coach-review.json`, un exercice applicable compris
par le pilote, ou refus précisément expliqué. C'est la première preuve d'exploitabilité
par GPT ; une simulation de réponse écrite par le générateur ne la remplace pas.

### Lot 6 — Vérifier que le coaching sert réellement à progresser

- [ ] Faire au moins trois passages comparables avec la consigne, puis une séance de
  rappel sans aide si possible. Conserver voiture, repères et conditions connues.
- [ ] Générer le même dossier sans changer les règles de mesure/comparaison. Comparer
  médiane, dispersion, couverture, incidents et réussite de l'exercice, pas seulement
  le meilleur tour. Une différence de carburant/conditions reste une explication possible.
- [ ] Publier le résultat : exercice compris/appliqué, effet observé ou indéterminé,
  une prochaine priorité. Ne pas attribuer automatiquement un gain au coach.

**Livrable :** premier retour avant/après revu. Le plan C/replays/`d` ne se discute
qu'ensuite, à partir d'une limite récurrente démontrée par ces dossiers.

## 5. Organisation, effort et règles d'arrêt

| Lot | Unité de travail indicative | Point de contrôle utilisateur |
| --- | --- | --- |
| Audit/plan + essai manuel initial | Livrés dans cette tâche | Comprendre les vrais manques du rapport |
| 0 — cas/référence | 1 séance de préparation, puis réception des pièces | Un cas concret et une référence qualifiable |
| 1 — mesure | 1–2 séances techniques bornées | Comparatif des seuls défauts utiles, pas nouvelle revue intégrale |
| 2 — indépendant | 1 séance de capture  + 1–2 séances d'annotation/calcul | Une décision documentée sur les six contrôles |
| 3 — faits de virage | 1–2 séances d'implémentation | Tableau des vrais passages et métriques |
| 4 — dossier | 1–2 séances d'implémentation/revue | Dossier portable attachable |
| 5 — GPT | 1 essai initial, puis cycles ciblés sur les pièces manquantes | Une faiblesse comprise, une correction étayée et un exercice |
| 6 — utilité | Séance de pilotage suivante | Effet observé ou résultat indéterminé |

Une séance technique désigne une tranche avec un livrable revu, pas une promesse de
latence ou de quota. Estimation à réviser à la sortie du lot 1, surtout si la présence
HUD échoue ; attendre des sources n'est pas du temps d'implémentation. Ne pas promettre
un coach validé à une date fixe avant réception/qualification de la référence et du
holdout. En revanche, aucune tranche ne se termine avec seulement « plus de recherche ».

Avant chaque tranche : déclarer l'entrée, le défaut/livrable, le test de sortie et ce
qui sera rejoué. Après : montrer le fichier, les résultats et une prochaine action.
Un défaut n'est rouvert qu'avec une preuve nouvelle. Aucun sous-agent, ajout d'OCR/ML,
régression de vitesse ou recalage de seuil sans besoin matériel démontré. Tests ciblés,
full suite, docs-list, commit atomique et push sur la branche autorisée, sans merge.

## 6. Statut et prochaine action exacte

- [x] Analyser le code réel, vérifier les artefacts run-024 et identifier les composants absents.
- [x] Écarter explicitement le web et définir le dossier local envoyé manuellement à GPT.
- [x] Définir les lots, dépendances, livrables, critères et limites de travail.
- [x] Tenter manuellement le coaching avec run-024 et intégrer les lacunes observées au plan.
- [ ] Exécuter les lots 0–6 après demande explicite de reprise ; aucune implémentation commencée.

**Prochaine action à la reprise demandée : commencer le lot 0, figer la fiche du cas
McLaren/Les Combes (ou un autre cas explicitement choisi), sélectionner les passages
comparables et qualifier la référence. Préparer ensuite la matrice de clôture A du
lot 1. Aucun replay complet ni nouveau compteur au seul titre de cette préparation.**
La dernière demande est « juste le plan » : arrêter après publication de ce document,
avec Gate A toujours bloqué. Ne pas lancer les lots d'implémentation implicitement.
