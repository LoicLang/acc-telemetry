---
summary: executable tasks for source admission, physical landmark annotation, corner metrics, paired trajectory images and a ChatGPT evidence dossier
read_when:
  - implementing the first reference-based corner coaching dossier after reliability gate A
  - acquiring a reference or preparing user and reference videos for coaching
---

# B — Virage, référence et dossier ChatGPT : Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. No subagent delegation is required by this plan.

**Goal:** Livrer un dossier réel où ChatGPT dispose de tes mesures, d'une référence
expliquée et d'images permettant d'examiner la trajectoire des deux passages.

**Architecture:** Réutiliser les artefacts versionnés du plan A. Un manifeste local
décrit les sources et repères ; des fonctions pures calculent événements/métriques ;
des adaptateurs produisent clips, images, JSON, Markdown et HTML. Aucun appel LLM
automatique et aucun modèle `d` ne sont nécessaires.

**Tech Stack:** Python 3.13.2, unittest, dataclasses, YAML/JSON/CSV, NumPy,
Matplotlib pour PNG, Plotly pour HTML, FFmpeg pour médias. Bibliothèques déjà présentes.

## Dépendance obligatoire et travail humain

Ne commencer **aucune implémentation B** tant que le gate A n'est pas passé et
consigné dans `docs/current-status.md`. Lire le plan A et la spécification commune.
Le plan B utilise des vidéos autorisées fournies localement : il n'achète rien,
ne contacte personne et n'extrait pas derrière un accès privé.

Un futur agent peut construire les tests synthétiques après A sans référence réelle.
Il ne peut pas valider B avec une référence absente. L'utilisateur doit fournir ou
choisir une source et valider les annotations demandées aux tâches B2/B3.

Proposition de cas : **Spa / Bruxelles**, trois passages minimum de la session BMW
du 3 septembre. Cette sélection est une hypothèse de travail, à confirmer dans les
images. Ne pas inventer les temps du virage ni le modèle de voiture. Une fois le
cas confirmé, ses choix vivent dans `data/lab/coaching-spa-bruxelles/case.yaml`.

## Responsabilités de fichiers

| Fichier sous `src/acc_telemetry/` | Responsabilité |
| --- | --- |
| `domain/coaching.py` | Types du cas, métriques, comparaison, preuves et revue |
| `application/coaching_config.py` | Chargement validé de `config/coaching.yaml` |
| `application/coaching_case.py` | Validation des sources, métadonnées, annotations et gate A |
| `analysis/corner_events.py` | Hystérésis, épisodes frein/gaz, couverture |
| `analysis/corner_metrics.py` | Les sept métriques et références de preuve |
| `analysis/corner_comparison.py` | Comparabilité, deltas, dispersion, constats descriptifs |
| `application/coaching_media.py` | FFmpeg, frames appariées et clips à vitesse réelle |
| `visualization/coaching_dossier.py` | JSON/CSV/Markdown, PNG et HTML |
| `adapters/coaching.py` | CLI `init`, `validate`, `prepare`, `build` |

**Tests nouveaux :** `test_coaching_case.py`, `test_corner_events.py`,
`test_corner_metrics.py`, `test_corner_comparison.py`, `test_coaching_media.py`,
`test_coaching_dossier.py`, `test_coaching_cli.py`.

Chaque tâche : RED ciblé, correction minimale, GREEN ciblé, full suite + docs-list +
diff-check, puis commit des seuls fichiers concernés et handoff/cases. Le nombre de
tests augmente : noter le résultat réel, ne pas conserver « 186 » par habitude.

### B1 — Définir un cas et les paramètres mesurables

**Créer :** `domain/coaching.py`, `application/coaching_config.py`,
`application/coaching_case.py`, `config/coaching.yaml`, `tests/test_coaching_case.py`.

- [ ] RED : source sans hash, vidéo absente, repères inversés/hors source, identifiant
  dupliqué, `measurement_fingerprint` du gate A incompatible, zéro largeur d'intervalle inconnue,
  seuils inversés, NaN doivent être refusés. Un manifeste de brouillon peut contenir
  des listes vides ; `validate --require-ready` doit alors échouer avec raisons.
- [ ] Lancer le fichier ciblé ; constater l'absence de contrats.
- [ ] Définir ces dataclasses, compléter leurs validations dans le loader :

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Landmark:
    landmark_id: str
    frame_lo: int
    frame_hi: int
    time_s: float              # milieu de l'intervalle, issu des timestamps A
    error_bound_s: float       # demi-largeur + résolution temporelle
    reviewer: str
    evidence_id: str

@dataclass(frozen=True)
class Passage:
    passage_id: str
    source_id: str
    role: str                 # driver | reference
    landmarks: tuple[Landmark, ...]
    eligible: bool
    exclusion_reasons: tuple[str, ...]

@dataclass(frozen=True)
class MetricResult:
    name: str
    value: float | None
    unit: str
    status: str               # available | unavailable | not_comparable
    coverage: float
    error_bound_s: float | None
    reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]
```

  Le loader retourne `CaseManifest` avec `case_id`, `schema_version`, `gate_a_path`,
  `sources` (mapping source_id -> path/hash/profile/artifacts/context),
  `landmark_definitions` (mapping id -> description/repère illustré),
  `passages` (tuple Passage), `reference_notes_path`, `visual_review_path`.
  La classe `CaseManifest` est définie ici dans `domain/coaching.py`, son chargement
  YAML/JSON dans `application/coaching_case.py`, jamais dans le domaine.

  Configuration initiale complète :

```yaml
events:
  pedal_on_pct: 5.0
  pedal_off_pct: 2.0
  sustain_s: 0.10
  max_sample_gap_s: 0.05
  brake_release_high_fraction: 0.80
  brake_release_low_fraction: 0.20
  release_recross_tolerance_pct: 2.0
  min_brake_peak_pct: 10.0
metrics:
  min_coverage: 0.95
  max_interpolation_gap_s: 0.10
  min_driver_passages: 3
media:
  context_before_s: 2.0
  context_after_s: 2.0
  event_context_s: 0.20
  max_pair_images: 12
validation:
  speed_mae_kmh: 2.0
  speed_p95_kmh: 5.0
  pedal_mae_pct: 5.0
  event_p95_s: 0.10
```

  Vérifier `off < on`, `low < high`, chaque intervalle positif, fractions dans [0,1],
  identité des seuils benchmark A/B ; si B change une cible du gate A, une nouvelle
  validation A est obligatoire, pas une acceptation automatique d'un ancien rapport.
  Ne pas comparer seulement le hash Git global : les commits B ajoutent du logiciel
  sans nécessairement modifier les composants de mesure validés par A.
- [ ] GREEN tests loader/contrats, vérification commune.
- [ ] Commit `feat: define reference corner case and metric contracts`.

### B2 — Obtenir et qualifier la référence réelle

**Créer :** `adapters/coaching.py` (`init`, `validate`),
`docs/reference-admission.md`, `tests/test_coaching_cli.py`.
**Étendre :** `application/coaching_case.py`, `tests/test_coaching_case.py`.

- [ ] RED : cas sans référence ne peut pas devenir `ready`; une URL seule n'est
  pas une vidéo analysée ; météo inconnue ou voiture différente bloque les cibles
  normatives quantitatives, pas la lecture des fichiers.
- [ ] Lancer `test_coaching_cli.py`.
- [ ] Implémenter la commande de création du brouillon (arguments réels ci-dessous) :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.coaching init \
  --case-id coaching-spa-bruxelles \
  --driver-video '/Users/loiclang/Movies/2026-09-03 22-42-08.mov' \
  --driver-profile ps5_full_map_1080p \
  --gate-a data/lab/coaching-reliability/run-001/validation/gate-a.json \
  --output data/lab/coaching-spa-bruxelles
```

  `init` crée `case.yaml`, `reference-notes.md`, `visual-review.json`,
  `missing-inputs.md`. Il ne copie pas la vidéo pilote. La source externe est liée
  avec hash et taille ; les dérivés iront à `interim/`/`reports/`. Le brouillon contient
  `sources.reference: null`, `passages: []`, `status: draft`, aucune mesure fictive.

  `missing-inputs.md` doit demander exactement : vidéo onboard du **même virage**,
  modèle/conditions connus ou inconnus, explication du passage (texte fourni, guide
  cité avec passages précis, ou revue technique), possibilité d'utiliser localement
  la vidéo et ses extraits. Un pack cité dans l'audit est une piste, pas une acquisition.
  L'utilisateur choisit/fournit ; l'agent vérifie ensuite les fichiers.

  Qualification de référence : vérifier présence cockpit, durée continue de l'approche
  à la sortie, repères visibles, cuts/ralentis, vitesse/frein/gaz disponibles ou non,
  même voiture si comparaison quantitative. Réutiliser un profil existant seulement
  après contrôle des ROI ; sinon ajouter un profil nommé selon HUD/résolution avec
  tests et calibration sur frames revues, pas un crop arbitraire.
  Les mesures de référence doivent elles aussi passer les vérifications d'exactitude
  et de visibilité sur leur source/profil ; la validation PS5 du pilote ne couvre pas
  automatiquement une vidéo PC recadrée. En l'absence de cette preuve, les valeurs
  de référence restent non comparables et le dossier est limité au visuel.
  Si télémétrie CSV fournie, n'admettre que `telemetry-v2` ou un mapping documenté
  colonne/unité/temps passé par le contrat A ; un `.ld` seul bloque cet import.
- [ ] Exécuter `validate --case ... --require-ready`. Code de sortie 2 + liste
  `reference_missing`/`reference_notes_unreviewed` tant que pièces absentes.
  `reference-notes.md` doit expliquer placement d'entrée, compromis du virage, sortie,
  exceptions et provenance ; aucune explication générée non revue n'est une autorité.
- [ ] Vérification commune ; commit `feat: admit reference sources with explicit limits`.
  Marquer la tâche terminée côté logiciel séparément du gate **référence réelle reçue**.

### B3 — Annoter les passages et la trajectoire observable

**Étendre :** `adapters/coaching.py` (`prepare`), `application/coaching_case.py`.
**Créer :** `application/coaching_media.py` (préparation initiale),
`tests/test_coaching_media.py`.

- [ ] RED : mêmes labels mais repères physiques différents non validés ; passage
  tronqué, frames au-delà de la durée, erreur d'origine de clip doivent être refusés.
  Définir test synthétique deux vidéos temporaires de couleurs/compteurs différents.
- [ ] Lancer le fichier ciblé.
- [ ] Implémenter :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.coaching prepare \
  --case data/lab/coaching-spa-bruxelles/case.yaml
```

  Réutiliser la préparation d'annotations A6. Écrire une planche de sélection et
  permettre des fenêtres `[frame_lo,frame_hi]` dans `case.yaml`. Pour chaque passage,
  l'agent propose `entry`, `middle`, `exit` et des images ; l'utilisateur valide la
  définition du passage (ex. un détail de vibreur arrivant à une ligne d'image définie).
  Si les caméras empêchent une correspondance suffisamment précise, choisir un
  autre repère visible ou classer la comparaison temporelle `not_comparable`.

  Le milieu est un repère physique fixe, pas « là où chaque pilote atteint son apex ».
  Les instants de freinage/gaz ne servent pas de repères d'alignement.
  Stocker plusieurs frames plausibles et leur erreur, sans forcer une frame unique.
  Associer des plages de visibilité par champ, revue humaine et raisons d'exclusion
  (trafic, sortie de piste, portion manquante). Trois passages personnels minimum.

  `visual-review.json` contient par repère : `pair_id`, sources/frames, `status`,
  `observation`, `limitations`, `reviewer`. Valeurs de statut : `unreviewed`,
  `human_observed`, `indeterminate`. Une annotation manuelle ne devient pas un label
  métrique `d`. Ne pas comparer directement des pixels de deux FOV pour annoncer
  un écart latéral physique.
- [ ] GREEN synthétique. Faire valider les annotations du vrai cas ; si elles ne sont
  pas fournies, noter le blocage réel et ne pas fabriquer de temps. Vérification commune.
- [ ] Commit `feat: prepare reviewed physical landmarks and trajectory pairs`.

### B4 — Extraire les événements temporels sans traverser les trous

**Créer :** `analysis/corner_events.py`, `tests/test_corner_events.py`.

- [ ] RED avec séquences à timestamps irréguliers : pulse 40 ms rejeté, plateau
  >=100 ms admis, seuil hystérésis, trou 200 ms, absence sous seuil après freinage,
  signal déjà actif au début de segment (`left_censored`).
- [ ] Lancer `test_corner_events.py`.
- [ ] Définir `Episode(start_s,end_s,start_error_s,end_error_s,censored,reasons)`
  dans `corner_events.py`, puis
  `detect_episodes(times, values, qualities, *, on, off, sustain_s, max_gap_s)`.
  Algorithme exact :

```text
Traiter les observations dans l'ordre temporel, sans tri ni suppression des absences.
Une qualité autre que observed ou un gap > max_gap_s casse la run.
Inactif -> candidat à la première valeur >= on.
Candidat -> actif si valeurs restent >= on pendant sustain_s.
Une valeur < on avant confirmation annule le candidat.
La date retenue est celle du candidat, pas celle de la confirmation.
Actif -> candidat de sortie à la première valeur <= off.
Sortie confirmée après sustain_s <= off ; retenue au début du candidat de sortie.
Un retour > off avant confirmation annule cette sortie.
Une rupture en état actif crée un épisode censuré, jamais une fin de freinage connue.
Les bornes d'événement couvrent au moins l'intervalle entre dernière preuve inverse
et première preuve du nouvel état. Si cet intervalle manque, borne inconnue/censurée.
```

  Faire les tests avec des littéraux explicites, par exemple :

```python
times = [0., .05, .10, .15, .20, .25, .30, .35, .40]
values = [0., 0., 20., 20., 20., 0., 0., 0., 0.]
episodes = detect_episodes(times, values, [QualityFlag.OBSERVED] * len(times),
                          on=5., off=2., sustain_s=.10, max_gap_s=.051)
self.assertEqual(len(episodes), 1)
self.assertAlmostEqual(episodes[0].start_s, .10)
self.assertAlmostEqual(episodes[0].end_s, .25)
```

  Ne pas interpoler les pédales avant de détecter un événement. Les 100 ms sont un
  filtre de persistance, pas la précision garantie de l'événement.
- [ ] GREEN et tests de gaps ; vérification commune.
- [ ] Commit `feat: detect quality-aware braking and throttle episodes`.

### B5 — Calculer les sept métriques

**Créer :** `analysis/corner_metrics.py`, `tests/test_corner_metrics.py`.

- [ ] RED : fixture synthétique connue avec frein 1–3 s, gaz 4–6 s ; coasting 3–4 s,
  minimum de vitesse 80 km/h, sortie 100 km/h. Puis retirer la mesure du minimum,
  placer un trou sur la reprise gaz, ajouter un second freinage et tester les nulls.
- [ ] Lancer le fichier ciblé.
- [ ] Implémenter `compute_corner_metrics(samples, passage, settings) -> tuple[MetricResult,...]`.
  Lire `samples` normalisés ; aucune dépendance à un DataFrame legacy dans la logique.
  Méthodes exactes :

  1. `segment_time_s` : sortie moins entrée, borne erreur = somme des bornes de repères.
  2. `brake_onset_s` : début premier épisode complet dans le segment moins entrée.
     Si déjà en freinage à l'entrée, unavailable `left_censored`.
  3. `brake_release_s` : premier épisode de frein principal = pic maximal, puis durée
     du passage descendant 80% du pic à 20%. Chercher après le dernier pic ; refuser
     si remontée > tolérance avant 20%, pic <10%, gap ou fin censurée. Garder l'épisode
     brut dans evidence pour qu'une autre stratégie de freinage ne disparaisse pas.
  4. `coasting_s` : somme de dt entre échantillons observés où les deux pédales sont
     <= off aux deux extrémités, dt<=max_gap. Si couverture insuffisante : valeur
     complète null, durée observée partielle dans les preuves, pas extrapolée.
  5. `minimum_speed_kmh` : minimum des vitesses observed ; si un intervalle inconnu
     dans la fenêtre pourrait cacher un minimum, ne pas comparer ce minimum. Une
     tolérance de petit gap n'est autorisée que si interpolation bornée validée et
     explicitement qualifiée ; v1 peut rester conservatrice avec null.
  6. `throttle_onset_s` : premier épisode de gaz après le pic du frein principal,
     moins entrée ; autoriser overlap de pédales et le signaler. Le nombre
     `throttle_interruptions` compte ses sorties confirmées puis reprises avant exit.
     C'est un sous-indicateur de la sixième métrique, pas une cause de trajectoire.
  7. `exit_speed_kmh` : vitesse au temps de sortie, exacte ou interpolation A5 entre
     deux vitesses observed séparées de <=.10 s. Aucune extrapolation.

  Calcul de couverture temporelle (pas proportion de frames) :

```python
def observed_duration(times, admitted, *, max_gap_s):
    return sum(b - a for a, b, ok_a, ok_b in
               zip(times, times[1:], admitted, admitted[1:])
               if ok_a and ok_b and 0 < b - a <= max_gap_s)
```

  Pour chaque métrique, préciser ses champs requis, sa couverture propre et les
  frames/événements utilisés. Évaluer aussi l'impact des bornes de repères en
  recalculant aux bornes pour vitesses de sortie et fenêtres temporelles.
- [ ] GREEN : unités, nulls, bornes, minimum occulté, aucune mesure au travers d'un
  gap critique. Vérification commune.
- [ ] Commit `feat: compute auditable single-corner metrics`.

### B6 — Comparer à la référence sans inventer la cause

**Créer :** `analysis/corner_comparison.py`, `tests/test_corner_comparison.py`.

- [ ] RED : référence absente, voiture différente, météo inconnue, deux métriques
  indisponibles, événements dont les intervalles se chevauchent ; aucun conseil
  « trop tôt/tard » automatique. Tester trois passages personnels et référence.
- [ ] Lancer le fichier ciblé.
- [ ] Implémenter `compare_corner(driver_metrics, reference_metrics, context)`.
  Résultat : valeurs individuelles, médiane et MAD personnelles (définir MAD =
  médiane des écarts absolus à la médiane), delta pilote-référence si admis,
  statut `descriptive_only` si conditions insuffisamment connues, evidence_ids.

```python
from statistics import median

def median_and_mad(values):
    if not values:
        return None, None
    center = median(values)
    return center, median(abs(v - center) for v in values)

def distinguishable_time_delta(driver, reference):
    if driver.value is None or reference.value is None:
        return False
    if driver.error_bound_s is None or reference.error_bound_s is None:
        return False
    return abs(driver.value - reference.value) > (
        driver.error_bound_s + reference.error_bound_s)
```

  Delta de début de freinage = différences de temps **depuis un repère**, pas
  différence de position : les vitesses d'approche peuvent différer. Le texte généré
  dit « délai depuis le repère », jamais « freine X mètres plus tôt ».
  Un freinage spatial ne se compare qu'avec une observation au même endroit validée.
  Ne pas transformer delta positive en erreur normative sans la référence expliquée.
  Les constats automatiques restent descriptifs ; causalité et exercice appartiennent
  au dossier de preuves et à la revue ChatGPT/humaine B9/B10.
- [ ] Vérifier mêmes données dans un ordre de source différent -> même comparaison ;
  aucune paire sans couverture commune. Vérification commune.
- [ ] Commit `feat: compare corner evidence with contextual restrictions`.

### B7 — Construire les preuves visuelles réellement consultables

**Étendre :** `application/coaching_media.py`, `tests/test_coaching_media.py`.

- [ ] RED : numéro de frame incorrect après découpage, timestamps manquants,
  ordre pilote/référence inversé, destination raw ou existante, vidéo source modifiée,
  sous-processus FFmpeg en échec. Tester avec vidéos synthétiques temporaires portant
  des numéros de frame, pas uniquement en mockant subprocess.
- [ ] Lancer le fichier ciblé.
- [ ] Implémenter `render_case_media(case, output_dir, settings)` : images côte à
  côte à entry/middle/exit, puis contexte d'événements à -0.20/0/+0.20 s lorsque
  disponible. Maximum 12 PNG pour le premier dossier, listés avec identifiants,
  source/time/frame et raison du choix. Conserver le champ cockpit complet ; un
  crop HUD supplémentaire ne le remplace pas. Ne pas déformer pour rendre les deux
  trajectoires ressemblantes. Le commentaire doit signaler les différences de caméra.

  Extraire les frames exactes par index sur la vidéo source validée, PTS enregistré.
  Appeler FFmpeg avec une liste d'arguments (`subprocess.run(...,check=True)`), jamais
  un shell interpolé. Clips à vitesse réelle, re-encodés H.264/yuv420p, hors raw :

```python
args = ["ffmpeg", "-nostdin", "-n", "-i", str(video),
        "-ss", str(start_s), "-t", str(duration_s),
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)]
```

  Cette commande produit un clip de revue ; sa provenance garde l'origine source,
  le trim et le temps de début réel vérifié après encodage. Les nombres du dossier
  proviennent toujours des timestamps source, pas d'un timecode vidéo re-encodé estimé.
  En mode côte à côte animé, synchroniser seulement à un repère annoncé, vitesse 1x
  des deux côtés ; ne pas prétendre qu'ils restent au même endroit tout le long.
- [ ] Contrôler avec ffprobe les sorties, ouvrir les vrais PNG, lire les extraits ;
  tous les landmarks doivent représenter le même repère physique. Vérification commune.
- [ ] Commit `feat: render traceable driver and reference visual evidence`.

### B8 — Générer le dossier et la commande complète

**Créer :** `visualization/coaching_dossier.py`, `tests/test_coaching_dossier.py`.
**Étendre :** `adapters/coaching.py` (`build`), `tests/test_coaching_cli.py`.

- [ ] RED : un dossier complet sans référence/notes/images/gate ne peut être publié ;
  NaN refuse JSON ; missing reste null ; chaque evidence_id résout un média ou un
  intervalle existant ; aucune trajectoire en mètres n'apparaît. Tester permissions
  des fichiers de sortie, échec média et absence de dossier partiellement complet.
- [ ] Lancer les deux tests ciblés.
- [ ] Implémenter `build_dossier(case, output_dir)` avec sortie atomique. Écrire :
  START_HERE, prompt, dossier, evidence.json, metrics.csv, comparison.html, images,
  clips, provenance. Le JSON contient :

```json
{
  "schema_version": "coaching-evidence-v1",
  "case_id": "synthetic-case",
  "status": "draft",
  "context": {},
  "reference": {},
  "passages": [],
  "metrics": [],
  "comparisons": [],
  "visual_observations": [],
  "evidence": [],
  "limitations": []
}
```

  Cet objet vide est un exemple **draft**, jamais une sortie `ready`. La version ready
  exige 3 passages driver, 1 référence, notes revues et médias. Si capacités manquantes,
  statut `limited` et raisons listées, code de sortie 2 avec `--require-complete`.
  Pour `ready`, exiger aussi temps du segment, début de freinage, remise des gaz et
  vitesse de sortie disponibles sur ces passages et leur référence, ou choisir un
  autre passage compatible avec ce premier cas d'usage. Les métriques secondaires
  peuvent être nulles avec raison ; un dossier aux sept métriques absentes n'est
  jamais complet. `visual_only` est un mode de comparaison, son statut reste `limited`.
  Les liens HTML sont relatifs dans le dossier ; Markdown affiche les noms de PNG à
  joindre, aucune prétention que ChatGPT ouvre des chemins locaux.
  PNG courbes : temps relatif au repère, vitesse/frein/gaz séparés, trous visibles,
  référence et chaque passage identifiés. Pas de double axe ambigu ni de remplissage
  des absences. Tableau relie chaque chiffre à sa source et son unité.

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.coaching validate \
  --case data/lab/coaching-spa-bruxelles/case.yaml --require-ready
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.coaching build \
  --case data/lab/coaching-spa-bruxelles/case.yaml \
  --output data/lab/coaching-spa-bruxelles/reports/run-001 --require-complete
```

- [ ] Vérifier chaque chiffre JSON contre le CSV et chaque evidence_id ; ouvrir HTML
  et PNG, vérifier lisibilité et ordre. Vérification commune.
- [ ] Commit `feat: export reference corner dossier for ChatGPT`.

### B9 — Donner une instruction précise à ChatGPT et revoir sa réponse

**Créer :** `docs/coaching-review-protocol.md` avec frontmatter et
`tests/test_coaching_prompt.py` ; **modifier :** générateur de prompt B8.

- [ ] RED : le prompt doit demander l'examen des images et empêcher une conclusion
  spatiale sur les seules pédales ; le dossier sans images lisibles reste limité.
  Test utile : rendu du dossier limité et de ses restrictions, pas simple test de mots.
- [ ] Exécuter le fichier ciblé.
- [ ] Générer ce prompt, avec la liste effective des pièces jointes insérée :

```text
Tu m'aides à progresser sur ACC PS5. Analyse le dossier et les images joints.
Commence par indiquer les pièces que tu as effectivement pu lire.
Compare mon passage à la référence expliquée ; examine entrée, milieu et sortie.
Pour chaque constat, cite un identifiant de métrique ou d'image du dossier.
Sépare : observation mesurée, observation visuelle, hypothèse causale, inconnue.
Ne déduis pas une erreur de trajectoire des seules courbes de vitesse ou de pédales.
Ne transforme pas une différence de FOV en distance latérale ni un délai en mètres.
Si les images/référence sont insuffisantes, demande la preuve manquante.
Choisis au maximum une priorité. Donne un exercice praticable et son critère de
réussite mesurable par les données disponibles, avec les explications alternatives.
N'invente aucun nombre, diagnostic physique, trajectoire idéale ou score de confiance.
```

  L'utilisateur joint les fichiers ; l'agent n'envoie rien à un service externe.
  Enregistrer la réponse dans `reports/run-001/coach-response.md` (ignoré) et créer
  `coach-review.json` : chaque affirmation -> preuve, vérification chiffre, revue
  visuelle, acceptable/unsupported/contradicted, reviewer. Une référence technique
  non revue implique que la causalité demeure une hypothèse.
- [ ] Faire relire la réponse réelle : aucun chiffre inventé, aucune cause certaine
  sans support, un exercice seulement et un résultat mesurable. Si ce n'est pas le
  cas, corriger dossier/prompt, garder le premier échec comme preuve et réévaluer.
- [ ] Vérification commune ; commit `docs: define evidence-linked coaching review`.

### B10 — Vérifier l'utilité à la séance suivante

**Créer :** `docs/first-coaching-session.md`, `tests/test_session_followup.py`.
**Étendre :** `analysis/corner_comparison.py` et export B8 avec `session_role`.

- [ ] RED : ancienne/nouvelle séance avec voiture ou repères différents ne produit
  pas de gain comparable ; meilleur tour isolé ne remplace pas la médiane du groupe.
- [ ] Lancer le fichier ciblé.
- [ ] Implémenter comparaison de deux dossiers v1 (mêmes case/landmarks compatibles,
  versions et critères qualité), sans recalculer OCR. Rapporter médiane/MAD, nombre
  de passages valides, réussite de l'exercice, couverture et incidents annotés.
  Protocole utilisateur : bloc de référence d'au moins 3 passages propres ; bloc
  suivant avec une consigne, même voiture/setup/conditions autant que possible ;
  retour sans aide à la séance suivante pour vérifier la rétention. Consigner
  carburant, échauffement et différences de contexte, ne pas attribuer automatiquement
  tout gain au coach.
  L'exercice précis dépend de la revue B9 ; il n'est pas inventé avant les mesures.
- [ ] Valider au moins un dossier réel et sa revue avant d'annoncer « premier coach
  fonctionnel ». La mesure à la séance suivante est une étape humaine séparée :
  tant qu'elle manque, statut `utility_not_yet_tested`, pas « progression prouvée ».
- [ ] Vérification commune ; commit `feat: compare follow-up coaching evidence`.

## Gate de sortie B et reprise

- [ ] Gate A passé et preuve compatible avec le code/config utilisé.
- [ ] Trois passages personnels et une référence réelle admise et expliquée.
- [ ] Même repères revus et images de trajectoire lisibles, limites caméra explicites.
- [ ] Sept métriques renseignées ou nulles avec raisons ; aucun zéro de remplacement.
- [ ] Dossier complet ou limité correctement classé, aucune prétention de `d` métrique.
- [ ] Réponse ChatGPT réelle revue ; un exercice mesurable retenu ou abstention justifiée.
- [ ] Suivi humain effectué ou explicitement en attente, sans revendication d'efficacité.
- [ ] `docs/current-status.md` donne un chemin de dossier et une seule prochaine action.

Si la référence reste introuvable : livrer le logiciel testé, le dossier `draft` et
la liste de fichiers manquants. Ne pas marquer ce gate passé et ne pas pivoter vers
un modèle ML massif pour masquer cette dépendance.
