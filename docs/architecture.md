---
summary: existing video extraction and artifact layers, with future agent platform boundaries and current acquisition-first priority
read_when:
  - changing package boundaries or measurement data flow
  - separating current video acquisition from the future agent platform
---

# Architecture

## Chaîne existante

```text
capture immuable -> extraction -> normalisation -> domaine -> analyse -> visualisation
                                        application = orchestration
                                        CLI/web = adaptateurs
```

**Cible : plateforme de données de séances navigable par un agent**, avec outils/MCP,
comparaisons et preuves à la demande. **Travail actif : extraction et qualification des
données vidéo avant la plateforme.** L'[audit du code](video-data-audit.md) distingue
les capacités présentes des métriques du catalogue. [Plan unique](plans/video-to-agent-platform.md).

Le premier `session_coaching.md` reste un export implémenté, décrit par son
[contrat](specs/2026-09-13-session-coaching-report.md). Le service web hérité existe ;
il ne constitue pas le futur MCP. Aucune infrastructure supplémentaire requise pour
les prochains calculs sur les artefacts existants.

| Module | Responsabilité existante |
| --- | --- |
| `extraction/video.py` | Métadonnées, validation1080p60CFR, images/ROI et couverture de décodage |
| `extraction/laps.py` | Lectures fraîches vitesse/rapport/compteur ; wrappers legacy isolés |
| `extraction/controls.py` | Barres frein/gaz, candidat de direction, raisons d'absence |
| `application/components.py`, `pipeline.py` | Configuration et traitement séquentiel partagé ; progression hors ligne |
| `normalization/samples.py`, `domain/telemetry.py` | Unités, valeurs nullable, qualités, raisons et valeurs sources |
| `application/session_artifacts.py` | Écriture/relecture telemetry-v2, hashes et publication exclusive |
| `analysis/validation.py`, `application/capture_validation.py` | Évaluation des annotations et preuves des gates |
| `analysis/alignment.py` | Interpolation bornée et comparaisons diagnostiques |
| `visualization/interactive.py` | CSV/HTML et résumés de session ; pas le premier fichier GPT |
| `adapters/cli.py` | Entrée locale `main.py` |

Domaine/normalisation ne dépendent pas d'OpenCV, Plotly ou FastAPI. Les règles partagées
appartiennent à l'application/analyse, pas aux adaptateurs. Les modules de compatibilité
sous `src/` et `main.py` délèguent aux modules packagés.

## Configuration et mesures

`config/roi_config.yaml` définit la géométrie du HUD ; `config/telemetry.yaml` contient
les paramètres de lecture, admission et progression, chargés/validés par `load_settings()`.
Le format des nouvelles captures est strictement1920×1080 à exactement 60 fps CFR.
FFprobe contrôle les timestamps de présentation ; les paquets MOV marqués discard ne
sont pas des images à publier. Autres formats refusés avant extraction, sans conversion.

`TelemetryPipeline` lit la vidéo séquentiellement et la ferme dans `finally`. Elle
collecte les observations puis confirme les tours, calibre l'odométrie et fusionne la
progression hors ligne. Les observations brutes du compteur et son état confirmé sont
séparés ; les événements conservent premier candidat, confirmation et dernière preuve
ancienne. La confirmation n'est pas un franchissement physique de ligne.

Le mode `reviewed`, par défaut, exige des plages de visibilité revues pour publier
vitesse/pédales. Le mode explicite `automatic` refuse des annotations d'entrée et lit
les mêmes ROI sans revue préalable. Les résultats portent `speed_hud_unverified` /
`hud_visibility_unverified`; cela ne qualifie pas un détecteur automatique de HUD.
La visibilité est documentée dans [speed-visibility](speed-visibility.md) et
[control-visibility](control-visibility.md).

La vitesse moderne conserve une lecture OCR fraîche ou une absence, sans médiane ni
maintien. `speed_admission.py` applique les limites validées de variation/gap et conserve
la lecture brute rejetée ; aucun chiffre estimé ne remplace la mesure. Les pédales ne
sont ni lissées ni rescalées. TC/ABS restent indisponibles. Les artefacts anciens gardent
leurs statuts HELD et leur sémantique, sans qualification rétroactive.

Les qualités (`observed`, `missing`, `held`, `interpolated`, `predicted`, `fused`,
`anomalous`) et raisons atteignent CSV, `TelemetrySample` et telemetry-v2. `observed`
indique la fraîcheur, pas une exactitude vérifiée. Les consommateurs doivent conserver
nulls et raisons. [Traitement des signaux](signal-treatment.md).

## Generic position estimation

```text
speed + delta time -> v * delta_t -> distance intégrée -> s_odometry
carte statique -> centerline -> candidats du point voiture -> s_visual
s_odometry + s_visual + tour confirmé -> s_fused + incertitude + raisons
```

Le tracker exige une centerline unique et des candidats cohérents ; seules les bornes
de tour confirmées ancrent la progression. La calibration utilise les distances
intégrées des tours admissibles. L'interpolation interne bornée d'odométrie conserve
sa provenance et ne remplit jamais la vitesse mesurée. Les longues incertitudes restent
manquantes. La compatibilité `track_position` est `s_fused * 100`, jamais une distance
physique latérale. `TelemetrySample.s` est actuellement sans unité, entre0 et1 ; le futur
`s_m` du catalogue doit rester explicitement distinct, comme `d_m`. En automatique, `automatic_measurements_unverified` accompagne la
progression dérivée. Les contrôles représentatifs établissent la cohérence interne,
pas une précision spatiale indépendante.

Pour le premier rapport, comparer des repères physiques et des temps revus plutôt que
supposer `s` exact. Ne pas forcer l'approbation du gate des interpolations spatiales.
[Contrat de comparaison](comparison-reliability.md). Les anciens designs détaillés
sont dans [l'archive](archive/README.md), sans nouvelle action de recherche implicite.

## Export expérimental implémenté

L’assembleur **relit les artefacts existants**, sans exécuter `TelemetryPipeline` :

- `analysis/session_summary.py` : faits et comparaisons nécessaires, fonctions pures ;
- `application/session_report.py` : lecture artefacts/fiche et assemblage du texte ;
- `adapters/session_report.py` : commande locale, entrées/sorties/erreurs.

La fiche locale `session-coaching-case-v1` porte source/manifeste/payloads, repères,
frames revues, lectures HUD ponctuelles, attribution et limites. Les images et preuves
complémentaires sont vérifiées par SHA-256. Les fonctions pures calculent disponibilité
et intervalles temporels ; une vitesse n’est admise que fraîche et concordante avec la
lecture locale. Nulls et raisons persistent. Les durées de commande ne sont pas calculées.
Le fichier est préparé entièrement puis publié par lien atomique sans remplacement,
hors source, `raw/` et répertoire d’artefacts. Aucun nouveau format brut n’est introduit.
Le Markdown fournit les faits au modèle ; le générateur ne produit pas de coaching.

**Gate A reste FAIL et les artefacts gardent `coaching_eligible=false`.** La décision du
13 septembre permet ce seul export expérimental avant qualification générale, à partir
de faits localement soutenus et de leurs limites. Elle ne valide ni le moteur entier,
ni une référence professionnelle, ni le coaching automatique. Voir le contrat actif.

## Perception temporelle M1 — premier prototype implémenté

`analysis/perception.py` construit un index d'événements neutres avec hystérésis,
persistance et ruptures explicites ; `config/perception.yaml` est validé séparément
sans modifier les paramètres d'extraction/qualification. Les zones sont une partition
source-bound revue, pas des limites spatiales supposées exactes.

`application/perception.py` relit les artefacts, vérifie source/zone/media, rend les
clips par plages natives de frames et publie le paquet atomiquement. Le rendu local
`visualization/perception.py` lie vidéo, curseur et valeurs via l'horodatage de l'image
présentée, avec fallback explicite. La CLI `adapters/perception.py` orchestre seulement
les arguments. `adapters/perception_preview.py` est un lecteur HTTP localhost facultatif,
confiné au dossier et compatible Range pour la navigation vidéo, sans API métier.

[Contrat et résultat M1](perception-package.md). Aucune modification du pipeline OCR.
Le premier export texte demeure disponible. Les labels PC et modèle image/séquence→d
restent planifiés : géométrie, horloges et transfert PS5 à démontrer. Le diagnostic et
les exercices appartiennent à l'IA consommatrice, pas aux détecteurs du pipeline.

## Plateforme future — frontières à préserver

Acquisition vidéo et futur adaptateur PC alimenteront un contrat commun, avec origine,
unités, temps et qualité. Sources immuables et dérivés versionnés existent déjà via
telemetry-v2 ; la nouvelle base de séances interrogeable reste à construire après le
socle de données. Comparaison, récurrences et sélection de preuves appartiendront aux
services applicatifs partagés. MCP sera un adaptateur fin ; skills éventuels = méthode
d'investigation, séparée des faits. PDF et lecteur humain resteront des vues facultatives.
