---
summary: technical audit of the PS5 telemetry pipeline, verified reliability defects, and proposed evidence-first coaching roadmap
read_when:
  - planning reliability corrections after the September 5 technical audit
  - evaluating coaching metrics or the replay-based lateral perception proposal
  - interpreting current progress validation and field-quality claims
---

# Audit technique et proposition de direction — 5 septembre 2026

## Autorité et périmètre

Audit demandé par le propriétaire : remettre en question le code, la logique de
mesure et la proposition `.rpy -> vidéo -> d/heading`, pour obtenir un coach utile
depuis les captures ACC PS5. Le premier résultat souhaité est un débrief de séance
avec une erreur prioritaire, un exercice et un critère de réussite. La comparaison
est un moyen de justifier ce débrief ; le programme sur plusieurs semaines vient
plus tard.

Les défauts ci-dessous sont des constats sur `c6a06bb`, branche
`fix/boundary-visual-anchor`. Les architectures, seuils et étapes proposés restent
à discuter : ce document n'est pas une spécification d'implémentation approuvée.
Aucun comportement de production n'a été modifié pendant l'audit. Aucun modèle
visuel n'a été entraîné, aucun replay ACC n'a été parsé ou rendu par cet audit.

Vérification : les 186 tests passent sous Python 3.13.2 avec
`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`. Ils n'exercent pas
une session réelle complète. Les trois résumés locaux de validation du 5 septembre
ont été lus ; leurs compteurs correspondent au handoff. Les chemins de captures et
preuves référencés ont été vérifiés sur cette machine.

## Verdict

La fondation mérite d'être conservée : séparation des couches, pipeline partagé
CLI/web, observations visuelles candidates, odométrie, refus des topologies ambiguës,
tests synthétiques rapides, données brutes immuables et historique Git explicite.
Le choix de fusionner plusieurs indices est raisonnable pour une vidéo console.

En revanche, les contrats annoncés sont plus solides que leur intégration actuelle.
Une sortie numérique plausible et une suite verte ne suffisent pas à autoriser un
diagnostic. Le risque principal est de présenter au coach des estimations comme des
observations, puis de transformer une corrélation en explication causale.

Recommandation : terminer une tranche verticale limitée de coaching, après correction
des défauts de preuve, et réserver `d/heading` à une expérimentation séparée. Éviter
une réécriture générale ou une chaîne ML complète avant de mesurer l'utilité du
premier débrief.

## Défauts confirmés ayant un impact coaching

Les références de lignes se rapportent au code audité, resté inchangé.

| Priorité | Constat | Preuve et conséquence |
| --- | --- | --- |
| P1 | Le confirmeur ne reçoit pas l'OCR brut | `application/pipeline.py:173,193` transmet la sortie de `extract_lap_number`; `extraction/laps.py:224-254` applique majorité, monotonie et maintien du dernier numéro. Une sortie lissée suivie de quatre lectures OCR vides peut achever la confirmation à confiance 1.0. Les valeurs maintenues ne sont pas cinq nouvelles preuves. |
| P1 | La qualité de vitesse est perdue à la sortie | `pipeline.py:175-195` transmet `speed_quality` à la fusion, mais les records à partir de la ligne 229 ne la conservent pas. `normalization/samples.py:104-107` classe par défaut toute valeur présente comme observée. Une vitesse HELD redevient OBSERVED après le vrai pipeline et la normalisation. |
| P1 | HUD absent et commandes nulles sont confondus | `extraction/controls.py` retourne zéro en absence de pixels détectés, sans validité du HUD. Des ROI entièrement noirs produisent frein/gaz/volant/TC/ABS à zéro, puis OBSERVED en normalisation. Cela peut inventer une phase sans pédales ou masquer une intervention. |
| P1 | La comparaison remplit des zones sans mesure | `visualization/interactive.py:1004-1028` trie par position, interpole sur 0–100% et étend les extrémités sans masque de qualité ni limite de trou. Deux mesures à 20% et 30% donnent 201 points sur un tour entier. Les deltas et courbes deviennent trompeurs sur une couverture partielle. |
| P1 | Le modèle des points de comparaison API perd le contrat moderne | `adapters/web/models.py:42-55` n'a pas les champs modernes de progression ; `api/telemetry.py:227-232` utilise ce modèle. La sérialisation retire `s_fused`, composants, source, incertitude et raisons. Ce constat concerne ce chemin typé, pas l'affirmation que tous les endpoints retirent ces champs. |

Reproductions synthétiques autonomes, sans moteur OCR ni vidéo privée :
`data/lab/2026-09-05-technical-audit/reproduce_integration.py` et
`integration-results.txt` (ignorés). Le test du numéro de tour initialise le tour 1,
envoie onze textes OCR « 2 » pour faire basculer le lissage historique, puis quatre
textes vides. La frontière est émise au quatrième texte vide. Cela démontre la perte
de provenance ; cela ne mesure pas le taux de fausses frontières sur les vidéos.

Corrections à concevoir : un objet d'observation par champ, une seule autorité pour
confirmer les tours, normalisation avant consommation métier, comparaisons seulement
sur couverture commune valide et schéma API explicite. Le critère de test doit porter
sur tout le trajet extraction -> pipeline -> export -> import -> analyse.

## Ce que les validations de `s` prouvent réellement

Les métriques de `scripts/diagnose_progress.py:84-154` sont utiles pour détecter
certaines incohérences. Elles ne constituent pas une mesure indépendante de position.

- Les checkpoints sont définis par `s_odometry`, qui participe aussi à la fusion.
  Deux courbes identiquement biaisées peuvent avoir une dispersion nulle.
- La fin prématurée est comptée lorsque `s_fused >= .999` mais l'odométrie est sous
  `.99` ou absente. Si les deux sont prématurément hauts, le compteur reste à zéro.
- Un saut n'est compté que sur des valeurs consécutives disponibles, au-delà de 10%
  du tour. Ce n'est pas un test de précision de quelques mètres ni de relocalisation
  après un trou.
- L'interpolation des checkpoints ne borne pas la largeur des trous.
- Les références de replay ont servi à ajuster plusieurs règles : ce sont des
  régressions utiles, pas un jeu de test indépendant et intact.

Reproduction : pour deux tours avec `s_fused = s_odometry ** 2`, tous les compteurs
de sécurité sont nuls et la dispersion est zéro. À `s_odometry=.5`, la progression
rendue vaut pourtant `.25`. Une ligne sans frontière avec les deux coordonnées à 1
ne déclenche pas non plus le compteur de fin prématurée. Script et sortie ignorés :
`data/lab/2026-09-05-technical-audit/reproduce_metrics.py`, `metrics-results.txt`.

La dernière dispersion vaut environ .001547 sur le contrôle propre, .005740 sur le
nouveau BMW et .017384 sur le contrôle avec incidents. Sur une échelle illustrative
de 7 km, cela représente environ 11, 40 et 122 m. Ce ne sont **pas** des erreurs
spatiales mesurées ; cette conversion montre seulement pourquoi ces scores ne
justifient pas « freinage 7 m trop tôt ».

### Le repère doit devenir explicite

L'intégrale de la vitesse estime une distance parcourue par la voiture. La longueur
de la centerline de minimap est une longueur d'image. Une abscisse physique de piste
est encore une autre grandeur. Des valeurs normalisées dans [0,1] ne rendent pas ces
repères automatiquement interchangeables. Trajectoire, dénivelé, sortie de piste,
marche arrière et calibration peuvent modifier leur relation.

Conserver l'odométrie comme prédiction locale, mais définir à terme :

- `distance_travelled_m` : intégration avec qualité et limites ;
- `s_map` : coordonnée sur une carte identifiée et versionnée ;
- `s_track_m` : abscisse sur une géométrie de référence validée, si disponible ;
- un recalage explicite entre ces repères et un `reference_id`.

Le départ est actuellement ancré au moment où la confirmation est émise. Il faut
distinguer `event_time` (passage estimé) et `confirmed_at` (preuve suffisante obtenue),
avec une incertitude temporelle. Sinon le délai OCR/lissage déplace l'origine.

Les incertitudes actuelles combinent croissance configurée et scores heuristiques.
Elles ne sont ni une probabilité calibrée ni un intervalle en mètres. De plus,
`LapLengthCalibration.uncertainty` n'est pas transmise au constructeur de fusion dans
`application/progress.py:964` et suivants. Une faible dispersion de longueurs ne
prouve pas l'absence de biais commun. Ne pas produire « confiance 95% » à partir de
ces nombres.

La calibration rejette les outliers de durée et distance seulement à partir de trois
tours éligibles (`odometry.py:275`). Deux tours, dont un incidenté, ne bénéficient pas
de ce rejet. Une durée inhabituelle est par ailleurs un indicateur de contexte,
pas une preuve suffisante d'une mauvaise mesure de distance.

## Qualité du code et organisation

Le nouveau domaine et les fonctions pures rendent les corrections locales possibles.
Les défauts se concentrent aux frontières et dans les chemins historiques. Priorités :

1. Faire du contrat typé et de sa provenance la sortie réelle de l'application ;
   dériver les anciens dictionnaires dans les adaptateurs.
2. Séparer, quand ces zones sont modifiées, orchestration de session, association
   visuelle, récupération d'ancre et estimation temporelle. `progress.py` dépasse
   1 100 lignes ; cette concentration complique la vérification des invariants.
3. Déplacer comparaison et métriques hors de la visualisation vers l'analyse.
4. Persister les observations compactes dans `interim/`, avec hash vidéo, version du
   code, configuration et profil. Rejouer fusion et analyse sans refaire tout l'OCR.
5. Vérifier durée, profil, HUD, résolution, timestamps et complétude de décodage avant
   de déclarer une session exploitable. `video.py` utilise `frame/fps` et termine au
   premier échec de lecture : acceptable sous hypothèse CFR validée, insuffisant pour
   des captures arbitraires.
6. Déclarer et tester la version Python réellement supportée : le README annonce
   3.10+, mais le domaine importe `StrEnum` (introduit en 3.11), et l'audit a tourné
   uniquement en 3.13.2. Ajouter ensuite une CI minimale ; aucun `.github/` n'est présent.

Pas de nécessité immédiate de microservices. Pour un usage personnel, un traitement
local hors ligne suffit. Avant un produit hébergé : jobs persistants et reprenables,
limites de ressources, séparation des utilisateurs, politique de rétention et mesures
de temps/mémoire/coût par minute vidéo. Le `JobManager` actuel est en mémoire et le
pipeline matérialise plusieurs collections par frame ; aucun benchmark de charge
n'a été effectué pendant cet audit.

La documentation a de bonnes règles mais `current-status.md` accumule d'anciens états
et compteurs. Certaines affirmations « end to end » ou « raw » sont contredites par
le code. Préférer à l'avenir un handoff court et les rapports datés pour l'historique.

## Mesures utiles au premier débrief

Le premier produit doit comparer quelques passages comparables, puis proposer une
expérience. La meilleure référence initiale est un ensemble de tes passages propres
et reproductibles, pas nécessairement le meilleur tour isolé ou un tour professionnel.
Fixer voiture, version/BoP si connue, réglage, météo, état de piste, carburant initial
et aides ; marquer les informations inconnues. Exclure trafic, incidents et stands
du groupe de référence sans effacer ces observations du dataset.

| Mesure | Acquisition proposée | Ce qu'elle permet / limite |
| --- | --- | --- |
| Temps du segment et régularité | Deux repères physiques annotés sur vidéo ; timestamps validés ; médiane et dispersion des passages | Comparaison locale avant un `s` métrique global ; séparer erreur de mesure et variation du pilote |
| Début de freinage | Barre de frein, hystérésis et durée minimale en secondes, timestamp puis position validée | Comparer les repères ; le pourcentage HUD n'est pas une pression hydraulique |
| Durée et profil du relâchement | Signal de frein validé, filtrage borné et absence explicite | Travail sur la progressivité ; qualifier de trail braking seulement si le début de virage est aussi établi |
| Temps sans pédales | Frein et gaz tous deux observés sous leur seuil | Indice descriptif ; le coasting n'est pas automatiquement une erreur |
| Reprise des gaz et interruptions | Franchissements soutenus de seuils configurés, retours sous seuil, qualité | Évaluer la continuité de sortie ; ouvrir plus tôt n'est pas toujours préférable |
| Vitesse minimale et vitesse de sortie | OCR validé dans une fenêtre et à un repère fixe | Comparaison locale ; vitesse minimale et apex géométrique ne sont pas synonymes |
| Rapport et changements | OCR avec état missing/held et horodatage | Contexte et séquence de conduite ; pas une prescription universelle de rapport |
| Placement entrée/apex/sortie | Images de passage annotées, puis modèle visuel évalué | D'abord catégories ou largeur relative visible ; mètres seulement avec calibration |
| Volant / turn-in | HUD ou volant cockpit après vérification de la signification et de la réponse | Proxy d'input, pas directement angle des roues ni rotation du véhicule |
| ABS / TC | Valider le témoin réellement observé et sa signification | Ne pas confondre réglage de l'aide, activation et durée d'intervention |

Ne pas promettre pour la première version : adhérence résiduelle, charge roue,
sideslip, angle exact des roues, regard du pilote ou cause certaine d'un sous-virage.
L'optical flow mélange translation, rotation caméra, relief et mouvement de tête ;
il ne mesure pas seul le survirage. L'orientation du véhicule et la direction de sa
vitesse sont également distinctes.

### Budgets d'erreur proposés, à négocier puis mesurer

Ces nombres sont des cibles de PoC, pas des performances acquises.

| Domaine | Évaluation proposée | Première cible indicative |
| --- | --- | --- |
| Vitesse | MAE, P95, taux de grosses erreurs et couverture sur annotations indépendantes | MAE <= 2 km/h, P95 <= 5 km/h sur images déclarées lisibles ; publier aussi abstentions |
| Pédales | Erreur en points de pourcentage, précision/rappel actif-inactif | MAE <= 5 points ; surtout aucune absence du HUD transformée en observation |
| Tours | Précision/rappel des événements, délai et erreur du passage estimé | Aucun faux événement dans le corpus audité ; chaque vrai passage annoté apparié, sans prétention statistique globale |
| Frein/gaz | Erreur temporelle médiane/P95 par événement | P95 <= 0,10 s pour comparer des écarts de plusieurs dixièmes ; réduire sinon la précision des conseils |
| Alignement spatial | Résidus sur repères physiques indépendants, par tour et session | P95 <= 5 m si une référence métrique existe ; sinon publier des secondes et repères, pas des mètres |
| Disponibilité | Couverture par champ et segment, trou maximal, erreur après relocalisation | Au moins 95% du segment cible, sans trou traversant un événement utilisé ; seuil spécifique à la mesure |
| Diagnostic | Relecture de chaque affirmation, lien vidéo, exactitude des nombres | 100% des affirmations chiffrées traçables ; abstention sur causes non observables |
| Progrès pilote | Réussite de l'exercice, médiane/dispersion du segment, validité, rétention | Gain supérieur au bruit de mesure, reproductible et sans hausse des incidents |

Une erreur de temps de 0,10 s à 200 km/h vaut déjà environ 5,6 m de déplacement.
Ne pas annoncer un décalage de 3 m quand l'alignement est incertain à cette échelle.
L'incertitude de la référence doit entrer dans celle de la comparaison.

Créer un corpus annoté court : passages complets et fenêtres d'événements répartis
sur plusieurs séances, cas lisibles et cas dégradés, avec identifiants de sources.
Annoter des repères vus dans l'image cockpit, indépendants des sorties du modèle.
Une annotation de passage donne une vérité temporelle ; elle ne donne pas à elle
seule une distance en mètres. Garder une séance intacte pour le test final.

## Réévaluation de `d` et des replays

### `d_reference` devrait être une mesure dérivée

Une trajectoire de référence change selon voiture, conditions, objectif et niveau.
Un écart à un tour rapide n'est pas automatiquement une erreur.

Préférer un état spatial lié à une géométrie stable de piste : projection sur une
centerline versionnée, décalage latéral signé, orientation relative à sa tangente,
limites utilisables gauche/droite et incertitude. Le point de la voiture représenté
(centre, essieu, autre) doit être défini, de même que le plan local et la convention
de signe, notamment avec relief et dévers.

Comparer ensuite la voiture et la référence à une même station de piste :
`delta_d(s) = d_driver(s) - d_reference(s)`. Une projection locale de type
`d = dot(P - C(s), normal(s))` demande une géométrie et une association non ambiguës.
Le `s_fused` actuel peut aider la localisation mais ne doit pas être traité comme
un `s_track_m` exact. Propager sa qualité, tolérer son absence et mesurer le modèle
avec un `s` bruité comparable à la vraie entrée PS5.

Pour commencer, des catégories de placement ou une fraction de largeur visible
peuvent suffire à une revue humaine. Une fraction d'image ne devient pas une fraction
de largeur physique sans modèle géométrique. Une estimation métrique sans géométrie
ni calibration ne doit pas être exposée comme une mesure.

### Ce qui est vérifié sur les sources externes

- [ACCReplay](https://www.accreplay.com/) propose analyses et téléchargements de
  replays/ghosts. Cela confirme un écosystème exploitable, pas un accès garanti à un
  dataset massif, une API publique ou la précision de toutes ses variables.
- [ACC Replay Visualizer](https://accrv.dyun.dev/) décrit un parsing serveur de `.rpy`,
  des positions exportées à 10 Hz et des indicateurs de qualité. Il distingue les
  chronos approximatifs dérivés de télémétrie des résultats exacts fournis séparément.
  La fréquence d'export annoncée ne démontre pas la fréquence native du replay. Aucun
  parseur ouvert et directement réutilisable n'a été vérifié pendant cet audit.
- Le [pack McLaren Spa cité](https://popometer.io/acc/setups/295) affiche bien 5,50 €,
  plusieurs tours de télémétrie et un tour marqué vidéo + replay. Il date de la
  version 1.8.18 ; il ne constitue ni un benchmark contemporain garanti ni un dataset
  de perception diversifié. Vérifier aussi les formats effectivement exportables.
- Le [repo universitaire](https://github.com/ESRLAccount/SimRacing_KPITelemetryDataAnalysis)
  décrit 174 participants et 1 327 tours à Brands Hatch. Le fichier public
  [Lap dataset.csv](https://github.com/ESRLAccount/SimRacing_KPITelemetryDataAnalysis/blob/master/Lap%20dataset.csv)
  consulté contient pourtant 476 lignes agrégées, 124 PID distincts et `TrackName`
  égal à `Laguna_Seca, Laguna_Seca` sur toutes ces lignes. Ce décalage demande
  clarification ; le corpus brut synchronisé décrit dans la discussion n'est pas
  établi. Aucune vidéo cockpit synchronisée n'est listée dans le dépôt consulté.
- [CodeWeavers](https://www.codeweavers.com/compatibility/crossover/assetto-corsa-competizione)
  référence ACC et un essai de 14 jours ; cela ne valide pas son rendu sur ce Mac.
  [Shadow](https://shadow.tech/discover-shadow-pc-in-2-minutes/) fournit un PC Windows
  avec installation de logiciels : candidat au test, pas banc de rendu déjà vérifié.

La consultation publique ou l'achat d'un pack ne doit pas être supposé couvrir
l'entraînement, la redistribution ou l'exploitation commerciale : documenter les
droits fournis et demander au fournisseur les usages manquants avant acquisition
massive. L'audit n'a pas conclu juridiquement sur les licences. Aucune acquisition
payante ni prise de contact n'a eu lieu.

### PoC à réaliser avant toute collecte industrielle

1. Obtenir un replay ACC identifié et compatible, avec autorisation d'usage et version
   du jeu. Éviter de confondre les outils Assetto Corsa et ACC.
2. Extraire sur un passage : identifiant voiture, temps natif, position 3D et
   orientation si présente. Documenter axes, unités, point d'origine, quantification,
   fréquence, discontinuités et champs réellement disponibles. Positions seules ne
   donnent ni bord de piste ni heading du châssis avec garantie.
3. Rendre une caméra cockpit reproductible, FOV/siège/mouvements documentés ; capturer
   sur la machine qui rend plutôt que réenregistrer le flux cloud reçu sur Mac.
4. Mesurer le lien entre horloge replay et timestamps vidéo : offset, dérive,
   pauses, seeks, doublons et images perdues. Valider sur plusieurs événements du
   passage, pas un seul départ. Une cible initiale de 20 ms implique déjà 1,1 m de
   déplacement à 200 km/h, sans que ce soit nécessairement l'erreur latérale.
5. Comparer les labels à une source indépendante (télémétrie PC simultanée quand elle
   existe, repères géométriques, surimpression contrôlée). Ne pas présumer que relire
   un replay réactive toute la télémétrie physique native.
6. Vérifier une deuxième voiture du même replay : couverture et qualité peuvent
   différer de la voiture qui a enregistré la session. Le nombre de voitures n'est
   pas le nombre de trajectoires utilisables.
7. Produire un petit lot de frames labellisées, avec revue visuelle et budget d'erreur.
   Mesurer coût par minute utile avant de décider d'étendre.

Si le parsing ou les droits échouent, comparer le coût à une courte acquisition
vidéo + télémétrie par un partenaire PC volontaire. Un accès PC ponctuel sert alors
d'instrument de mesure ; le produit et son utilisateur restent PS5. Ne pas faire de
reverse engineering prolongé une dépendance obligatoire au premier coach.

### Apprentissage et transfert PS5

L'idée ACC PC professeur est plausible. Le modèle peut combiner image, fenêtre
temporelle, vitesse et progression avec leur qualité. Mais le principal risque est
le transfert de caméra/rendu et le manque de labels de validation sur PS5.

Commencer sur une voiture, un circuit et une caméra ; comparer une référence triviale
(placement moyen conditionné par `s`), une estimation visuelle géométrique/catégorielle
et un petit modèle temporel supervisé. Garder aussi une variante sans `s` pour vérifier
que l'image apporte une information réelle. Injecter les erreurs et absences de `s`
observées sur PS5 pendant l'apprentissage ; ne pas entraîner avec `s` parfait puis
annoncer la même performance avec `s_fused` bruité.

Varier ensuite FOV, siège, cockpit, lumière, météo, compression et occlusions de façon
contrôlée. La [randomisation de domaine](https://arxiv.org/abs/1703.06907) est une
méthode de recherche pertinente, pas une garantie de transfert ACC PC -> PS5.

Séparer entraînement/test par session/replay et pilote autant que possible : ni
frames voisines ni autres caméras du même événement dans les deux ensembles. Une
course avec 25 voitures ne fournit pas 25 environnements indépendants. Des tours IA
peuvent enrichir la perception mais ne représentent pas les erreurs humaines ni toute
la diversité utile. Les quotas 20–30 ou 100–200 tours ne sont pas des garanties :
décider avec courbes d'apprentissage, couverture des erreurs et test PS5 tenu à part.

Pour `d/heading`, mesurer erreur médiane/P95, biais par zone, dérive temporelle,
couverture, abstention et fiabilité de l'incertitude. Sans vérité métrique PS5, limiter
les conclusions PS5 aux catégories et repères effectivement vérifiés. Le test sur un
nouveau circuit est un objectif distinct, avec sa géométrie/caméra connue ou inconnue
explicitée ; il ne remplace pas le test de transfert de plateforme.

## Architecture proposée pour une sortie exploitable par IA

```text
vidéo immutable + manifeste de session
  -> observations versionnées par champ + références de frames
  -> état normalisé + qualité + repères
  -> événements et métriques sur intervalles exploitables
  -> comparaisons contextualisées
  -> constats / hypothèses / exercice proposé
  -> LLM pour dialogue et explication
  -> retour pilote et mesure à la séance suivante
```

Le LLM peut expliquer, poser une question utile et adapter un exercice. Les calculs,
seuils d'admissibilité et liens vers les preuves doivent être reproductibles. Une
observation structurée doit comporter valeur, unité, temps, qualité, source, version
et intervalle d'incertitude lorsqu'il a été calibré. Ne pas appeler « intervalle »
un score heuristique non étalonné.

Un objet de débrief devrait séparer : contexte de comparaison, métriques avec unités
et couverture, référence utilisée, liens frame/clip, fait observé, causes possibles,
information manquante, exercice, indicateur de réussite et conditions d'arrêt. Exemple
de structure, sans chiffres de performance inventés :

```json
{
  "schema_version": "coaching-evidence-proposal-v1",
  "segment_id": "manually-reviewed-corner",
  "reference_id": "same-session-clean-passages",
  "metrics": [],
  "evidence_refs": [],
  "observations": [],
  "hypotheses": [],
  "unavailable_claims": ["metric_lateral_offset", "certain_cause_of_time_loss"],
  "exercise": null
}
```

Ce schéma illustre une séparation de responsabilités ; il n'est pas encore un
contrat d'API adopté. Un conseil tel que « entrée trop intérieure -> sortie fermée »
exige du placement observé et un contrôle des explications alternatives. Une reprise
des gaz tardive seule autorise un constat temporel, pas cette chaîne causale.

## Trois stratégies et ordre recommandé

| Option | Intérêt | Risque | Avis |
| --- | --- | --- | --- |
| Débrief limité, preuves vidéo et comparaisons ciblées | Retour utile rapide, apprentissage des besoins réels, évaluation humaine | Certaines causes restent indéterminées | Recommandée comme trajectoire produit principale |
| Reconstruire d'abord l'état spatial complet avec replays et ML | Ouvre trajectoire et placement métriques | Dataset, synchronisation et transfert PS5 peuvent retarder tout coaching | PoC séparé, avec décision de poursuite mesurable |
| Confier directement les vidéos à un modèle multimodal | Prototype conversationnel et assistance à l'annotation | Mesures et diagnostics difficiles à rendre reproductibles | Assistant de revue ; insuffisant comme autorité quantitative |

Ordre proposé :

1. Concevoir puis corriger les observations de tours et la conservation de provenance,
   avec tests des chemins complets. Ne pas démarrer un downstream bloqué.
2. Rejouer la capture historique, en comparant désormais l'OCR brut, les événements
   annotés et les frontières confirmées. Construire en même temps le benchmark de
   précision indépendant sur quelques passages récents.
3. Fermer les pertes de qualité CSV/API et les interpolations injustifiées, valider
   frein/gaz/vitesse sur le segment choisi. Les sorties legacy restent des adaptateurs.
4. Après ces gates, obtenir un débrief vérifié sur un seul virage : plusieurs passages
   comparables, une différence démontrée, un exercice, puis mesure de son effet à
   la séance suivante. Des repères annotés évitent d'exiger une carte métrique globale.
5. Tester séparément le PoC `.rpy` sur un passage, avant d'acheter ou rendre un corpus.
   L'étendre seulement si labels, synchronisation et test PS5 le justifient.
6. Ajouter d'autres virages et séances ; introduire `d` lorsqu'une limite concrète du
   coaching justifie son coût. Curriculum multi-circuits et skill model ensuite.

Ne pas coupler automatiquement curriculum pilote et plan d'acquisition ML. Le pilote
doit s'entraîner sur la compétence utile ; le dataset doit couvrir les situations qui
manquent au modèle. Le retour ultérieur à Spa est une expérience de transfert de
compétence intéressante, mais l'ordre de quatre circuits n'est pas une nécessité
technique à imposer maintenant.

Pour valider le produit personnel : recueillir un bloc de passages de référence,
appliquer une seule consigne sur un bloc comparable, puis refaire un bloc sans aide
à la séance suivante. Examiner médiane, dispersion, taux de tours valides et réussite
du geste, pas seulement le meilleur chrono. Un seul avant/après ne prouve pas une
causalité : échauffement, carburant, fatigue et familiarisation peuvent expliquer
une partie du gain. La généralisation commerciale demandera ensuite d'autres pilotes.

## Prochaine décision

Valider le périmètre d'une correction des observations brutes et de la provenance
avant le replay historique, puis choisir le premier virage et les mesures du débrief.
Les propositions de ce rapport n'autorisent pas encore une implémentation ML ni une
dépense. Le but du brainstorming suivant est de transformer le premier périmètre
retenu en spécification courte avec critères mesurables.
