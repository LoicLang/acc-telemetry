---
summary: task-by-task implementation of raw lap observations, field provenance, bounded comparison and independent reliability validation
read_when:
  - starting the first implementation work after the September 5 audit
  - correcting extraction-to-export reliability before corner coaching
---

# A — Fiabilité des mesures : Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. No subagent delegation is required by this plan.

**Goal:** Fermer les cinq défauts reproduits dans l'audit et livrer des mesures dont
la qualité reste visible jusqu'aux consommateurs, avec validation indépendante.

**Architecture:** Conserver l'extracteur et la fusion existants. Introduire des
observations explicites, un export moderne et des comparaisons bornées, puis tester
les vrais enchaînements. Le corpus annoté valide les mesures indépendamment de `s`.

**Tech Stack:** Python 3.13.2, dataclasses, unittest, OpenCV, NumPy, CSV/JSON, FFmpeg.

## Lecture et état initial

Lire `AGENTS.md`, `docs/current-status.md`, `docs/technical-audit-2026-09-05.md`,
`docs/superpowers/specs/2026-09-05-reference-corner-coach-design.md` et les fonctions
citées dans chaque tâche. Base auditée : `d24809f` (code identique à `c6a06bb`).
Le commit de plan se trouve ensuite dans l'historique ; utiliser la branche contenant
ces documents, pas un `main` plus ancien qui perdrait les corrections déjà réalisées.

Toutes les commandes ci-dessous partent de la racine du repo. Les nouveaux scripts
mentionnés sont à créer à la tâche indiquée, ils n'existent pas encore.

## Règle de commit pour chaque tâche

Avant chaque commit : test ciblé indiqué, suite complète, index docs, diff check.
Actualiser le handoff et les cases de la tâche dans le même commit. Ne pas changer
les critères pour obtenir un résultat vert. Une correction imprévue reçoit son test
RED et son commit cohérent, puis le plan est annoté avec le résultat.

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
./scripts/docs-list
git diff --check
git status --short
```

Ajouter uniquement les fichiers de la tâche, du plan et du handoff. Jamais `data/lab/`
ou `data/sessions/`. Les sorties de tests et replays vont dans un nouveau répertoire
ignoré, par exemple `data/lab/coaching-reliability/run-001/`.

## Fichiers et responsabilités

| Fichier | Responsabilité |
| --- | --- |
| `domain/observations.py` (nouveau) | Observation par champ et spans de visibilité |
| `extraction/laps.py` | Lecture OCR brute distincte des filtres historiques |
| `extraction/controls.py` | Observation valide ou absente, sans zéro inventé |
| `application/pipeline.py` | Propagation et production des échantillons normalisés |
| `application/lap_state.py`, `domain/progress.py` | Évidence et délai de confirmation |
| `normalization/samples.py` | Respect de la provenance exportée |
| `application/session_artifacts.py` (nouveau) | Écriture atomique des artefacts et manifestes |
| `analysis/alignment.py` (nouveau) | Interpolation bornée, couverture commune |
| `analysis/validation.py` (nouveau) | Mesures d'erreur indépendantes |
| `adapters/web/models.py`, `api/telemetry.py` | Contrat sans perte et imports corrects |
| `scripts/annotate_capture.py`, `scripts/validate_capture.py` (nouveaux) | Préparation des annotations et benchmark |

Les chemins sans préfixe dans ce tableau sont sous `src/acc_telemetry/`.

### A0 — Préparer une baseline reproductible

**Fichiers :** lecture seule code ; mise à jour `docs/current-status.md`.

- [ ] Vérifier la branche propre ; créer `codex/coaching-reliability` depuis l'état
  courant contenant les plans (réutiliser si c'est déjà la branche de reprise).
- [ ] Exécuter les 186 tests de base. Si l'état a évolué, noter le nombre réel et
  expliquer les écarts avant de commencer, sans ramener le repo à un ancien commit.
- [ ] Exécuter les deux reproductions de l'audit si elles existent localement :

```bash
PYTHONPATH=src .venv/bin/python data/lab/2026-09-05-technical-audit/reproduce_integration.py
PYTHONPATH=src .venv/bin/python data/lab/2026-09-05-technical-audit/reproduce_metrics.py
```

  Leurs PASS signifient « défaut reproduit », pas « logiciel correct ». Si elles
  manquent, les cas de régression des tâches suivantes reconstruisent les preuves.
- [ ] Confirmer les vidéos du handoff et `.venv/bin/python`, `ffmpeg`, `ffprobe` ;
  utiliser les fichiers existants, aucune réinstallation automatique nécessaire.
- [ ] Noter état initial et commande suivante A1 dans le handoff ; commit
  `docs: start coaching reliability implementation` après vérification commune.

### A1 — Donner l'OCR réellement brut au confirmeur

**Modifier :** `src/acc_telemetry/extraction/laps.py` (`extract_lap_number`),
`application/pipeline.py` (`run`), `application/lap_state.py`, `domain/progress.py`.
**Créer :** `src/acc_telemetry/domain/observations.py`, `tests/test_lap_observations.py`.
**Modifier tests :** `tests/test_application_pipeline.py`, `tests/test_lap_state.py`.

- [ ] Écrire `test_blank_ocr_is_missing_even_after_a_valid_lap` et
  `test_pipeline_passes_raw_not_held_lap_to_confirmer`. Utiliser un faux backend texte
  comme dans la reproduction audit ; ne pas simuler seulement le confirmeur pur.

```python
# Contrat du nouveau helper pur, testé sans Tesseract.
def parse_lap_text(text: str) -> int | None:
    value = text.strip()
    return int(value) if value.isdecimal() and 0 <= int(value) <= 999 else None

# Assertions minimales du test d'intégration avec le vrai LapDetector instrumenté :
# _read_lap_text doit être remplacé par Mock(side_effect=["1", "", "1"]).
self.assertEqual(detector.observe_lap_number(frame).value, 1)
self.assertIsNone(detector.observe_lap_number(frame).value)
self.assertEqual(detector.observe_lap_number(frame).value, 1)
```

  Ajouter les cas `12x3`, saut +2, baisse, observations manquantes, initialisation,
  passage réel suivi d'un trou, OCR erroné +1 puis retour. Exiger absence de frontière
  après une seule lecture fraîche suivie de quatre absences ; cinq vrais +1 donnent
  une seule frontière. Garder la limitation documentée des erreurs OCR soutenues.
- [ ] Lancer `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_lap_observations.py' -v`.
  Attendu RED sur helper/méthode manquants.
- [ ] Introduire le type suivant ; mettre imports et dataclass dans le domaine :

```python
from dataclasses import dataclass
from typing import Generic, TypeVar
from acc_telemetry.domain.telemetry import QualityFlag

T = TypeVar("T")

@dataclass(frozen=True)
class FieldObservation(Generic[T]):
    value: T | None
    quality: QualityFlag
    raw_value: str | float | int | bool | None
    reasons: tuple[str, ...] = ()
    last_observed_time_s: float | None = None
```

  Extraire **sans changement** le bloc crop/prétraitement/backend de
  `extract_lap_number` dans `_read_lap_text(frame) -> str`. Ajouter
  `observe_lap_number(frame) -> FieldObservation[int]` qui appelle ce helper une fois,
  parse strictement et ne touche pas `_lap_number_history` ni `_last_valid_lap_number`.
  Le wrapper historique réutilise le helper puis ses règles actuelles ; le chemin
  production générique appelle seulement `observe_lap_number`.

```python
# Dans TelemetryPipeline.run, branche générique :
lap_observation = self.laps.observe_lap_number(self.video.current_frame)
raw_lap_number = lap_observation.value
# progress.observe_frame(..., raw_lap_number=raw_lap_number)
# Le chemin position legacy continue d'appeler extract_lap_number.
```

  Ajouter `first_candidate_time_s` / `confirmed_at_s` au résultat de confirmation,
  champs optionnels par défaut pour compatibilité. Réinitialiser le candidat sur
  observation manquante ; ne pas déplacer l'ancre au premier candidat dans ce commit.
  Exporter le dernier instant frais de l'ancien tour pour borner le passage probable.
  Le ratio de consensus reste un score, pas une probabilité d'exactitude.
- [ ] Exécuter les nouveaux tests, `test_lap_state.py`, `test_application_pipeline.py`,
  puis vérification commune. Adapter FakeLaps pour exposer le nouveau contrat,
  sans supprimer les tests du chemin historique.
- [ ] Commit `fix: confirm laps from fresh OCR observations`.

### A2 — Conserver vitesse et rapport avec leurs preuves

**Modifier :** `extraction/laps.py`, `application/pipeline.py`,
`normalization/samples.py`, `tests/test_speed_ocr_mode.py`, `tests/test_normalization.py`.
**Créer :** `tests/test_quality_roundtrip.py`.

- [ ] Écrire les tests vrais pipeline -> DataFrame -> CSV temporaire -> `normalize_row`.
  Cas vitesse HELD, vitesse manquante, rejet hors plage avec valeur brute conservée,
  rapport OCR manquant après rapport valide, et nombres non finis refusés en moderne.

```python
# row doit provenir de TelemetryPipeline avec FakeLaps HELD, pas être fabriqué
# directement avec la qualité attendue.
self.assertIn("speed_kmh:held", row["quality_hint"])
sample = normalize_row(row, settings.normalization)
self.assertEqual(sample.field_quality["speed_kmh"], QualityFlag.HELD)
```

- [ ] Lancer le fichier ciblé ; attendu RED car le record perd la qualité.
- [ ] Exposer `observe_speed` et `observe_gear` retournant `FieldObservation` : une
  seule lecture backend par frame/champ, texte avant validation conservé, valeur
  maintenue marquée HELD, valeur absente MISSING. Ne pas modifier silencieusement le
  filtrage vitesse existant. Pour le rapport, lire le symbole frais ; ne pas classer
  une médiane historique comme nouvelle lecture. N/R non implémentés restent absents
  avec raison `unsupported_gear_symbol`, jamais convertis en 1.
  Produire le format **déjà accepté** par `_quality_hints`, pas un dict stringifié :

```python
quality_hint = ";".join(
    f"{name}:{flag.value}" for name, flag in sorted(field_quality.items())
)
record["quality_hint"] = quality_hint
record["raw_lap_number"] = raw_lap_number
record["speed_raw"] = speed_observation.raw_value
record["gear_raw"] = gear_observation.raw_value
```

  Conserver les raisons par champ dans les artefacts modernes A4. `lap_number` est
  confirmé, mais sa qualité à une frame dépend de l'évidence fraîche ; un état
  maintenu n'est pas `observed`. Conserver les raisons du confirmeur dans le résultat
  session pour que le pipeline ne les reconstruise pas par heuristique.
- [ ] Tester également export/import des raisons et de tous les champs `s_*` avec
  valeurs nulles ; vérification commune.
- [ ] Commit `fix: preserve speed gear and lap provenance through records`.

### A3 — Distinguer commande à zéro et absence de HUD

**Modifier :** `extraction/controls.py`, `application/pipeline.py`,
`application/components.py`, `adapters/cli.py`.
**Créer :** `tests/test_control_observations.py`.
**Étendre :** `domain/observations.py` avec `VisibilitySpan(field,start_s,end_s,reviewer)`.

- [ ] RED : ROI vide/noir -> MISSING et `None` ; HUD visible et pédale relâchée ->
  OBSERVED et 0 ; absence de candidat volant -> MISSING ; aucune annotation de
  visibilité -> pas d'affirmation de zéro observé. Tester un overlay qui invalide
  une plage et les bornes incluses/exclues.
- [ ] Lancer `test_control_observations.py` et constater le défaut actuel.
- [ ] Ajouter `observe_frame_telemetry(rois, *, time_s, visibility)` à côté du wrapper
  historique. Le premier mode strict utilise des plages de visibilité **revues**,
  lues depuis `--visibility-json` ; il n'essaie pas de deviner un HUD valide à partir
  d'un seul seuil de luminosité. Ajouter un validateur de spans triés, non inversés,
  sans chevauchement contradictoire, durée comprise dans la vidéo.

```python
@dataclass(frozen=True)
class VisibilitySpan:
    field: str
    start_s: float
    end_s: float
    reviewer: str

def visible_at(spans, field: str, time_s: float) -> bool:
    return any(s.field == field and s.start_s <= time_s < s.end_s for s in spans)

def unavailable_control(reason: str) -> FieldObservation[float]:
    return FieldObservation(None, QualityFlag.MISSING, None, (reason,))
```

  Pour chaque champ : ROI vide/noir refuse la mesure même si le span est visible.
  Hors span revu : `hud_visibility_unverified`. Dans un span valide, appliquer les
  méthodes de décodage existantes. Faire retourner une absence interne au détecteur
  du point de volant s'il n'y a aucun candidat ; le wrapper legacy peut conserver son
  comportement historique, mais la méthode d'observation utilise cette absence.
  TC/ABS : qualité MISSING `indicator_semantics_unverified` jusqu'à annotation
  confirmant qu'il s'agit d'une intervention, pas du réglage. Les valeurs historiques
  peuvent rester visibles dans les preuves brutes, pas dans le coaching.
- [ ] Tester le roundtrip A2 avec ces commandes et chaque champ marqué missing.
  Mettre à jour CLI/web : sans spans, sorties strictes dégradées, jamais succès de
  coaching implicite. Vérification commune.
- [ ] Commit `fix: make control visibility explicit for coaching`.

### A4 — Produire un artefact moderne rejouable pour l'analyse

**Créer :** `application/session_artifacts.py`, `tests/test_session_artifacts.py`.
**Modifier :** `pipeline.py`, `adapters/cli.py`, `adapters/web/services/processing.py`.

- [ ] RED : export JSONL puis relecture conserve valeur brute, held, raisons, null,
  source/frame ; destinations `raw/`, fichier source, sortie existante refusées.
  Les anciens records restent disponibles pour les consommateurs existants.
- [ ] Lancer `test_session_artifacts.py` ; attendu méthode absente.
- [ ] Ajouter `samples` et `observations` à `PipelineResult` avec defaults compatibles.
  Normaliser les records à la fin du pipeline avec les settings explicites transmis
  à sa construction. Les observations conservent la qualité à l'extraction. Écrire
  un manifeste `telemetry-v2` avec SHA-256, taille, code Git, hash config, profil,
  capture CFR/PTS validée, temps et origine du clip. Utiliser `json.dumps(...,
  allow_nan=False)` et enum `.value` ; écrire dans un dossier temporaire voisin,
  puis renommer si la destination n'existe pas.

```python
# Sérialisation des membres MappingProxyType : conversion explicite.
serialized_quality = {k: v.value for k, v in sample.field_quality.items()}
serialized_source_values = dict(sample.source_values)
```

  Sorties : `observations.jsonl`, `samples.jsonl`, `telemetry.csv`, `manifest.json`.
  Les analyses du plan B réutilisent ces fichiers. Ce commit ne promet pas de
  relancer la fusion sans OCR : les candidats visuels nécessaires à ce replay
  complet ne sont pas tous persistés par ce premier contrat.
- [ ] Tester une interruption simulée : absence de dossier final partiel. Relecture
  de la version 2 obligatoire ; version inconnue refusée ; CSV legacy lisible mais
  manifeste absent -> `coaching_eligible=false`. Vérification commune.
- [ ] Commit `feat: export versioned telemetry evidence artifacts`.

### A5 — Empêcher comparateur et API de recréer des preuves

**Créer :** `analysis/alignment.py`, `tests/test_alignment.py`,
`tests/test_comparison_api_quality.py`.
**Modifier :** `visualization/interactive.py` (`_resample_lap_by_position`),
`adapters/web/models.py`, `adapters/web/api/telemetry.py`, `config/telemetry.yaml`,
`application/config.py`.

- [ ] RED : reprendre deux lignes entre 20 et 30% ; aucun point valide en dehors.
  Tester un trou interne, des doublons, une position qui recule, valeurs non finies,
  et aucune couverture commune. Le modèle API doit conserver champs modernes/null.
- [ ] Lancer les deux nouveaux fichiers de test ; constater les régressions audit.
- [ ] Implémenter une fonction pure (liste/NumPy, pas Plotly) avec ce contrat :

```python
def bounded_interpolate(x, y, targets, *, max_x_gap):
    # x strictement croissant, y fini ; une run valide est fournie par l'appelant.
    # Hors bornes -> NaN ; intervalle > max_x_gap -> NaN ; pas d'extrapolation.
    import numpy as np
    x, y, targets = map(lambda a: np.asarray(a, dtype=float), (x, y, targets))
    if len(x) != len(y) or len(x) < 2 or not np.all(np.diff(x) > 0):
        raise ValueError("expected increasing paired observations")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("non-finite observations")
    result = np.full(targets.shape, np.nan)
    for j, t in np.ndenumerate(targets):
        i = int(np.searchsorted(x, t))
        if i < len(x) and x[i] == t:
            result[j] = y[i]
        elif 0 < i < len(x) and x[i] - x[i-1] <= max_x_gap:
            f = (t - x[i-1]) / (x[i] - x[i-1])
            result[j] = y[i-1] + f * (y[i] - y[i-1])
    return result
```

  L'appelant découpe en runs **avant** de retirer les absences ; jamais de tri qui
  recolle un recul ou traverse un trou. Un doublon de position n'a pas un temps de
  passage unique : le marquer ambigu et scinder. Valeurs held/missing/anomalous non
  admises pour une comparaison coaching ; progression fused/predicted admise seulement
  si son gate et sa qualité locale le permettent. Settings position gap initial
  `.005` en s normalisé et time gap `.10` s, validés et explicitement nommés.
  Les points interpolés portent leur statut, jamais OBSERVED.

  Étendre `TelemetryDataPoint` avec les six `s_*`, `quality_hint`, raisons et contrôles
  nullable. Documenter cette nullabilité ; tester le client actuel sans supposer
  qu'une ancienne UI supporte null. Les endpoints dictionaries existants conservent
  leurs données. Corriger aussi l'import erroné du résumé vers
  `acc_telemetry.visualization.interactive`. Tester le véritable endpoint avec
  `unittest.IsolatedAsyncioTestCase` et stockage temporaire, puis valider/sérialiser
  le modèle de réponse déclaré. `httpx` n'est pas installé dans l'environnement de
  planification ; ne pas introduire TestClient sans déclarer sa dépendance de test.
  Ajouter un smoke HTTP manuel de comparaison et résumé avec Uvicorn/curl, en notant
  que le test direct de fonction seul ne couvre pas le routage HTTP.
- [ ] Recalculer le delta uniquement sur positions communes admises et temps depuis
  la frontière de tour confirmée, pas depuis le premier point survivant. Masquer les
  trous dans Plotly. Vérification commune et tests de compatibilité CSV/API.
- [ ] Commit `fix: preserve evidence coverage in comparisons and API`.

### A6 — Préparer des annotations indépendantes

**Créer :** `scripts/annotate_capture.py`, `analysis/validation.py`,
`tests/test_capture_annotations.py` ; `config/validation.yaml` et loader pur dédié
`application/validation_config.py` (testé, sans ajouter encore coaching.yaml).
**Modifier :** `extraction/video.py` (préflight, statut de décodage),
`tests/test_video_sampling.py`.

- [ ] RED : timestamps non croissants, mauvaise résolution, decode incomplet,
  annotation hors vidéo et intervalle de frames inversé doivent invalider le run.
  Une absence de vérité terrain doit donner `not_evaluated`, jamais erreur zéro.
- [ ] Lancer le fichier ciblé et `test_video_sampling.py`.
- [ ] Implémenter deux sous-commandes :

```bash
PYTHONPATH=src .venv/bin/python scripts/annotate_capture.py prepare \
  --video '/Users/loiclang/Movies/2026-09-03 22-42-08.mov' \
  --profile ps5_full_map_1080p --output data/lab/coaching-reliability/run-001/annotations
PYTHONPATH=src .venv/bin/python scripts/annotate_capture.py validate \
  --annotations data/lab/coaching-reliability/run-001/annotations/labels.json
```

  `prepare` écrit le manifeste FFprobe et une planche de sélection espacée (1 image
  toutes les 10 s), puis accepte des fenêtres de frames dans `selection.json` pour
  exporter chaque frame des fenêtres choisies lors d'un deuxième appel avec
  `--selection .../selection.json`. Ce deuxième appel crée un sous-dossier neuf de
  frames, sans réécrire les annotations existantes. `labels.json` stocke : source hash,
  frame/time, texte vitesse/rapport/tour ou null, pédales estimées et tolérance,
  visibilité par champ, passages physiques en intervalle `[frame_lo,frame_hi]`,
  annotateur, rôle `development` ou `holdout`. Le valideur refuse les labels non revus.
  Lire les timestamps FFprobe `best_effort_timestamp_time`, vérifier CFR et comparer
  à `frame/fps` à tolérance un intervalle frame ; si incompatible, arrêter avec
  `unsupported_timebase` (le support VFR n'est pas à improviser dans ce commit).

  Échantillonnage obligatoire : au moins 100 frames lisibles par champ vitesse/frein/gaz,
  20 cas dégradés, 20 fenêtres d'événements au total, plusieurs passages répartis sur
  deux captures minimum ; ne pas répartir les frames voisines entre dev et holdout.
  Ces tailles sont un minimum de PoC, pas une preuve de généralisation.
  L'agent prépare les images ; l'utilisateur confirme labels, visibilité et repères.
- [ ] Tester génération sur une vidéo **synthétique temporaire**, aucune vidéo privée
  requise par unittest. Config : speed MAE2/P95 5, pedal MAE5 points, event P95 .10s,
  min coverage .95 ; tests de paramètres invalides, y compris NaN.
- [ ] Commit `feat: add independent video annotation and validation inputs`.

### A7 — Rejouer l'historique et mesurer le gate A

**Créer :** `scripts/validate_capture.py`, `tests/test_capture_validation.py`.
**Modifier :** `scripts/diagnose_progress.py`, `analysis/validation.py`,
`docs/acc-ps5-plan.md`, `docs/current-status.md`.

- [ ] RED : courbes identiquement biaisées ne peuvent plus être qualifiées de
  spatialement exactes ; zéro annotation donne `not_evaluated`. Frontières doublées,
  manquantes et non appariées comptées séparément.
- [ ] Lancer `test_capture_validation.py` et `test_progress_diagnostic_cli.py`.
- [ ] Implémenter calculs indépendants : MAE/P95 et couverture par champ ; appariement
  un-à-un des événements avec annotations temporelles (fenêtre maximale configurée,
  rapport séparé des événements hors fenêtre). Mesurer erreur comme distance au
  **milieu annoté** et publier aussi demi-largeur de l'intervalle, pas zéro pour une
  annotation vague. Rapporter le délai de confirmation distinct de l'erreur du passage.
  Pour chaque repère physique, dispersion du `s_fused` entre passages ; ne pas la
  nommer erreur métrique absolue. Conserver les anciens compteurs comme diagnostics
  internes, annotés explicitement dans le JSON et les docs.
  Les fenêtres pédales annotées d'A6 servent ici à mesurer la latence de première
  observation fraîche au franchissement de 5%, sans implémenter les événements de
  coaching B4. Les épisodes soutenus seront validés séparément au plan B. Cette
  mesure de latence ne doit pas être nommée exactitude du détecteur B4.

```bash
PYTHONPATH=src .venv/bin/python scripts/diagnose_progress.py \
  data/sessions/2026/2026-09-01_spa_ps5_braking-baseline-aborted/raw/part-0.mov \
  --profile ps5_full_map_720p --output-dir data/lab/coaching-reliability/run-001/historical
PYTHONPATH=src .venv/bin/python scripts/validate_capture.py \
  --artifacts data/lab/coaching-reliability/run-001/session \
  --annotations data/lab/coaching-reliability/run-001/annotations/labels.json \
  --output data/lab/coaching-reliability/run-001/validation
```

  La sous-commande `validate_capture` lit les artefacts A4, ne relance pas l'OCR.
  Générer ces artefacts avec la CLI étendue en A4 (`--artifact-dir` et
  `--visibility-json`) avant la validation. Pour l'historique, annoter chaque
  transition suspecte et chaque vrai passage sur la capture complète ; ne pas se
  contenter d'un extrait propre. Sur les captures récentes, replays représentatifs
  clean/crash/BMW avec les mêmes définitions de métriques.

```bash
PYTHONPATH=src .venv/bin/python main.py \
  '/Users/loiclang/Movies/2026-09-03 22-42-08.mov' \
  --profile ps5_full_map_1080p \
  --output data/lab/coaching-reliability/run-001/legacy-reports \
  --artifact-dir data/lab/coaching-reliability/run-001/session \
  --visibility-json data/lab/coaching-reliability/run-001/annotations/visibility.json
```

  `annotate_capture validate` exporte `visibility.json` à partir des spans revus de
  `labels.json`. Le fichier doit être créé avant cette commande. Le script de
  diagnostic historique reste utile sans spans pour les seules frontières, mais
  n'est alors pas une preuve d'exactitude des commandes.
- [ ] Livrer `gate-a.json` avec champs `software_regressions`, `lap_events`,
  `field_accuracy`, `field_coverage`, `timebase`, `holdout`, chacun pass/fail/not_evaluated
  et chemin de preuve. Réussite exige tous pass ; champs unsupported sont déclarés
  absents et exclus des capacités de coaching, pas comptés comme mesures validées.
  Pour `s`, conserver validation locale de repères et interdiction des mètres.
  Ajouter `measurement_fingerprint` : hashes des modules effectivement utilisés
  extraction, pipeline, progress/lap_state/odometry, normalization, domain telemetry/
  progress/observations et session_artifacts, plus configuration résolue du profil
  et seuils de validation. Un nouveau commit de documentation ou du dossier B ne
  périme pas cette preuve ; un changement de ces composants la périme. Le hash Git
  global reste enregistré pour traçabilité mais n'est pas le seul test de compatibilité.
- [ ] Revoir visuellement les différences et les faux succès ; en cas d'échec, rester
  sur A et écrire le test de correction, sans commencer B. Suite complète, docs,
  commit `docs: record independent coaching reliability gate` avec les seuls résumés
  non personnels. Mettre B1 comme prochaine action uniquement si A passe.

## Sortie du plan A

- [ ] Les cinq reproductions ont leur test de non-régression vert et versionné.
- [ ] Le passage de tours historique est validé contre annotations, pas contre lui-même.
- [ ] Vitesse/frein/gaz du corpus sélectionné satisfont les seuils, ou le gate reste en échec.
- [ ] Provenance CSV/JSON/API reste intacte et les absences ne sont jamais recréées.
- [ ] `gate-a.json`, code/config/source hashes et annotations existent localement.
- [ ] Handoff, roadmap et cases synchronisés ; aucun push, aucune modification de raw.
