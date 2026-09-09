---
summary: implementation planning specification for reliable reference-based visual corner comparison and a manually reviewed ChatGPT coaching dossier
read_when:
  - executing the coaching reliability or reference dossier implementation plans
  - defining observations, corner metrics, visual evidence or coaching output contracts
---

# Premier dossier de coaching avec référence visuelle

**Statut :** base de conception du plan demandé le 5 septembre 2026. Ce document
décrit le travail proposé ; il ne certifie ni gate passé ni résultat de coaching.
L’exécution du plan A est désormais demandée ; son avancement fait autorité dans
`../current-status.md` et les cases du plan actif.

## Besoin et critère de réussite

Décision confirmée le 9 septembre : A fiabilise les données 1080p60 ; B livre le
premier dossier avec placement visuel revu, un exercice et un suivi de son effet.
`d` métrique est hors B. L'éventuelle recherche replays sera décidée à partir des
limites constatées dans les premiers débriefs, sans retarder B pour construire `d`.
Le choix du cas et la préparation des sources peuvent avancer pendant A ; les
implémentations et conclusions chiffrées B restent bloquées par Gate A.

L'utilisateur veut progresser sur ACC PS5 avec un coach ChatGPT. Le coach doit
disposer d'une référence de conduite contextualisée **et** voir la trajectoire du
pilote. Une comparaison de pédales seule ne répond pas à ce besoin.

Acceptation finale : trois passages personnels complets minimum, un passage de
référence documenté, les mêmes repères physiques identifiés, les sept métriques
qualifiées, des images appariées et un débrief humainement vérifié produisant un
exercice mesurable. Avec référence seulement visuelle, le dossier est explicitement
limité : il ne remplit pas l'acceptation d'une comparaison quantitative de commandes.

## Frontières

```text
raw vidéo + manifeste/annotations
 -> observations brutes (extraction)
 -> TelemetrySample + provenance (normalization/domain)
 -> événements + métriques + comparaisons (analysis)
 -> dossier JSON/Markdown/images/HTML (visualization)
 -> utilisateur joint les fichiers à ChatGPT
 -> réponse revue + expérience de conduite
```

L'application orchestre, la CLI parse les arguments, la web API adapte les sorties.
Pas de dépendance OpenCV/Plotly/FastAPI dans domain ou normalization. Aucune nouvelle
dépendance ML ; Python 3.13.2 vérifié, bibliothèques existantes et FFmpeg/ffprobe.

## Contrats retenus

`FieldObservation` : valeur interprétée, qualité, valeur/texte brut, raisons et temps
de la dernière observation fraîche. Les identifiants de source et frame sont portés
par l'enveloppe `FrameObservation`. Une valeur absente est `null`, jamais zéro par
défaut. `observed` signifie lecture fraîche, pas vérité certaine.

La progression garde son estimateur existant. Les numéros de tours donnés au
confirmeur proviennent d'un chemin OCR non lissé. Le contrat de frontière distingue
moment de confirmation et intervalle de passage probable ; le premier correctif
conserve le temps de confirmation pour l'ancrage et expose son délai, sans déplacer
silencieusement les ancres. Un éventuel rebasage sera une correction testée distincte.

Le format moderne de session est `telemetry-v2` : observations JSONL, échantillons
normalisés JSONL, CSV avec `quality_hint` complet, manifeste JSON. Les dictionnaires
et pourcentages historiques restent disponibles. Les anciens CSV sans provenance
sont importables mais **non admissibles au coaching** sans revue/annotation ; aucun
test historique ne justifie de leur attribuer une qualité moderne inventée.

L'enveloppe moderne contient : `schema_version`, `source_id`, `source_sha256`,
`frame`, `time_s`, `source_time_s`, `profile`, `field_quality`, `field_reasons`,
`observations`, `sample`. La sérialisation refuse NaN/inf et convertit les mappings
immuables en objets JSON explicitement, sans dépendre d'un deepcopy de MappingProxyType.

`CaseManifest` relie sources, référence pédagogique, passages, annotations,
validité du HUD et métadonnées de comparaison. Aucun chemin ne peut écrire dans
`raw/`; toute sortie existante est refusée et un nouveau run est demandé.

`MetricResult` : nom, valeur nullable, unité, statut (`available`, `unavailable`,
`not_comparable`), couverture temporelle, erreur temporelle maximale si connue,
raisons et identifiants de preuve. Les scores heuristiques de fusion ne deviennent
pas des intervalles probabilistes.

## Repères et visualisation de trajectoire

Choisir des repères de **la scène** : ligne de peinture, début/fin de vibreur ou
autre détail identifiable des deux caméras. Écrire une définition opérationnelle
de passage et un intervalle de frames plausible. Ne pas nommer « apex » une simple
frame de vitesse minimale. Conserver les cas visuellement indéterminables.

Trois repères au minimum : entrée avant freinage, milieu physique fixe, sortie après
le virage. Ajouter un repère intermédiaire si la correspondance est ambiguë. Les
choix propres à Spa vivent dans le manifeste local, pas dans les règles d'extraction.

Pour les images : appariement aux repères, labels de source/temps et fenêtres autour
des événements. Pour les courbes : axe temps relatif, plus alignement à chaque repère
quand nécessaire. Pas de dynamic time warping des vitesses/pédales : il pourrait
effacer précisément les différences à coacher. Pas de conversion d'une interpolation
entre repères en distance physique. Les clips restent à vitesse réelle.

La revue de placement porte sur ces images. Une différence de FOV ou de caméra peut
empêcher la conclusion ; statut `indeterminate` obligatoire dans ce cas. Aucun
modèle automatique de ligne idéale n'est inclus.

## Admissibilité et référence

Voiture, circuit, version/BoP, météo, pneus, carburant et contexte sont conservés avec
valeurs inconnues explicites. Même circuit et même virage obligatoires pour toute
comparaison. Voiture incompatible : pas de cible quantitative comparative. Conditions
inconnues : comparaisons descriptives seulement, pas de conclusion normative sur les
chronos/vitesses. Documenter les raisons de chaque restriction.

La référence comporte vidéo, auteur/provenance, usage permis connu, modèle de voiture,
explication technique sourcée ou revue par une personne compétente et passages précis
auxquels elle s'applique. Un tour rapide non expliqué ne suffit pas pour affirmer
une cause ou prescrire une trajectoire comme idéale.

Si la source ne peut être obtenue automatiquement, l'agent prépare la liste exacte
des fichiers attendus et attend leur fourniture pour la validation réelle. Ne pas
acheter, contacter un tiers, contourner un accès ou affirmer un benchmark terminé.

## Gates

Ces gates désignent des contrôles de validation. Le « gate C : coaching » ci-dessous
ne désigne pas le **plan C de recherche replays** ; l'exercice et son suivi sont
déjà inclus dans les tâches B9/B10 du plan de dossier.

- **A : logiciel et preuve.** Cinq défauts de l'audit corrigés et testés sur les vrais
  chemins ; historique de tours replayé contre annotations ; corpus court récent
  avec erreurs vitesse/commandes/événements et couverture mesurées. Pas d'utilisation
  des seuls compteurs odométriques comme preuve spatiale.
- **B : comparaison.** Sources admises et même virage, repères revus, pas de mesure
  dérivée d'un trou, référence pédagogique et paires d'images présentes. Les métriques
  non mesurables restent nulles ; un dossier limité ne peut porter le statut complet.
- **C : coaching.** Chaque affirmation chiffrée renvoie à une mesure et une preuve.
  Toute affirmation de trajectoire possède un support visuel revu. Un exercice à la
  fois, avec critère de réussite et contrôle de validité. Pas de causalité automatique.

Les cibles d'erreur initiales sont versionnées dans `config/coaching.yaml` au plan B :
vitesse MAE 2 km/h/P95 5 km/h, pédales MAE 5 points, événements P95 0,10 s,
couverture du segment 95%. Aucune absence du HUD ne peut être déclarée observée.
Publier taille du jeu, exclusions, intervalles d'annotation et résultats par source.
Ce sont des critères de PoC à confirmer avec les mesures, non des promesses générales.

## Hors périmètre

Programme multi-semaines, entraînement d'un modèle de trajectoire, scores de skill,
achat de datasets, import MoTeC universel, nouveaux circuits, hébergement SaaS et
intégration API ChatGPT. Le plan de recherche replays livre une décision de
faisabilité, puis demandera sa propre spécification ML si les preuves sont bonnes.
