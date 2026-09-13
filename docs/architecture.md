---
summary: current local pipeline and artifact boundaries plus the unimplemented single-file experimental report extension
read_when:
  - changing package boundaries or measurement data flow
  - implementing the first local session report from existing artifacts
---

# Architecture

## Chaîne existante

```text
capture immuable -> extraction -> normalisation -> domaine -> analyse -> visualisation
                                        application = orchestration
                                        CLI/web = adaptateurs
```

Le livrable actif est le fichier expérimental `session_coaching.md`, préparé **localement**
puis joint à GPT par le pilote. [Contrat](specs/2026-09-13-session-coaching-report.md) et
[plan](plans/2026-09-13-first-gpt-export.md). Le service web hérité existe mais ne fait pas
partie de ce travail. Aucun appel API GPT ou hébergement à ajouter.

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
physique latérale. En automatique, `automatic_measurements_unverified` accompagne la
progression dérivée. Les contrôles représentatifs établissent la cohérence interne,
pas une précision spatiale indépendante.

Pour le premier rapport, comparer des repères physiques et des temps revus plutôt que
supposer `s` exact. Ne pas forcer l'approbation du gate des interpolations spatiales.
[Contrat de comparaison](comparison-reliability.md). Les anciens designs détaillés
sont dans [l'archive](archive/README.md), sans nouvelle action de recherche implicite.

## Extension autorisée, pas encore implémentée

Le futur assembleur **relit les artefacts existants**, sans exécuter `TelemetryPipeline` :

- `analysis/session_summary.py` : faits et comparaisons nécessaires, fonctions pures ;
- `application/session_report.py` : lecture artefacts/fiche et assemblage du texte ;
- `adapters/session_report.py` : commande locale, entrées/sorties/erreurs.

Ces chemins sont proposés. Ne pas créer un format brut ni un moteur de sept métriques
avant d'avoir un besoin précis. La fiche locale porte sources/repères/passages et revue.
Le Markdown fournit les faits au modèle ; le générateur ne produit pas de coaching.

**Gate A reste FAIL et les artefacts gardent `coaching_eligible=false`.** La décision du
13 septembre permet ce seul export expérimental avant qualification générale, à partir
de faits localement soutenus et de leurs limites. Elle ne valide ni le moteur entier,
ni une référence professionnelle, ni le coaching automatique. Voir le contrat actif.
