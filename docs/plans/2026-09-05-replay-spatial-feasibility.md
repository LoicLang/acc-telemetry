---
summary: bounded feasibility experiment for ACC replay extraction and synchronized cockpit labels, with stop conditions before spatial ML
read_when:
  - deciding whether ACC replays can supply a lateral perception training dataset
  - executing the optional replay experiment after the coaching reliability work
---

# C — Faisabilité `.rpy -> vidéo + labels` : Implementation Plan


**Goal:** Produire une décision démontrée sur la possibilité de générer des images
cockpit avec labels spatiaux depuis un replay ACC, sans lancer un dataset massif.

**Architecture:** Expérience isolée des chemins de production. Un adaptateur lit le
replay, ACC rend une caméra documentée, un validateur relie les deux horloges. La
géométrie et la qualité des labels sont évaluées avant d'envisager `d/heading`.

**Tech Stack:** Lecteur `.rpy` à identifier et vérifier, ACC PC sur une machine
accessible, capture locale à cette machine, Python/NumPy, FFmpeg/ffprobe.

## Statut et budget de l'expérience

Plan séparé, **non actif**, à lancer sur décision explicite après le plan A. Il
n'autorise ni achat de logiciel/données, ni prise de contact, ni changement de scope
du coach. Aucun lecteur compatible n'est supposé déjà disponible. Les liens dans
l'audit sont des pistes vérifiées au 5 septembre, pas des dépendances installées.

**Priorisation approuvée le 9 septembre :** livrer d'abord les premiers débriefs B
avec placement visuel revu. Ouvrir ce plan seulement si leurs limites récurrentes
justifient une mesure latérale et qu'une décision explicite le confirme. `d` n'est
pas un prérequis de B. Ce plan produit une preuve de faisabilité, pas directement
un modèle prêt à coacher. Les vidéos rendues/analysées devront être en 1080p60 natif.

Périmètre fixe : un replay Spa, un passage de 30–60 secondes pour une première
voiture, puis le même intervalle pour une deuxième voiture si disponible. Deux rendus
de la même première caméra pour vérifier reproductibilité/synchronisation. On ne
rend pas une course entière pour découvrir que les labels manquent.

Limiter la recherche de lecteur existant à une session de travail documentée. Si
aucun lecteur exportable et vérifiable n'est identifié, produire `no_go_parser` avec
preuves et options ; ne pas entreprendre automatiquement du reverse engineering.

## Organisation des fichiers

À créer seulement lorsque ce plan est exécuté :

- `scripts/replay_poc.py` : adaptateur CLI de format documenté, sans import dans production.
- `src/acc_telemetry/analysis/replay_validation.py` : contrôles de labels/temps purs.
- `tests/test_replay_validation.py` : données synthétiques, aucun replay propriétaire.
- `docs/replay-feasibility-result.md` : conclusion synthétique avec frontmatter.
- `data/lab/replay-spatial-poc/run-001/` : fichiers personnels et sorties ignorés.

Les noms de fichiers d'entrée sont enregistrés dans `experiment.json`, pas codés dans
les scripts. Hash, version ACC, DLC requis, version du lecteur, unité, car_id et source
de géométrie accompagnent chaque sortie. Le fichier brut reste immuable.

### C1 — Prouver l'accès aux données nécessaires

- [ ] Inspecter un replay fourni localement, noter hash/taille/version connue et
  droit d'usage fourni. Si absent, demander un fichier accessible à l'utilisateur ;
  ne pas télécharger ou acheter arbitrairement une référence.
- [ ] Identifier un lecteur **ACC**, pas Assetto Corsa ; vérifier sa licence, méthode
  d'export et format réellement obtenu. Noter la commande exacte et la version dans
  `experiment.json`. Un visualiseur propriétaire sans export ne suffit pas.
- [ ] Exiger un export lisible documentant au moins temps, car_id et position 3D.
  Champs orientation/inputs absents restent absents. Livrable `labels-native.csv` :

```text
car_id,replay_time_s,x_m,y_m,z_m,yaw_rad,position_origin,quality,source_sample_id
```

  L'adaptateur ne peut nommer les colonnes `_m`/`_rad` qu'après établissement des unités.
  Si unités ou axes inconnus, produire `labels-undecoded.csv` et `no_go_units`, pas
  des labels prêts à entraîner. Ne pas confondre direction du déplacement et yaw.
- [ ] Décider `parser_pass` ou `no_go_parser/units/coverage`. Si échec, arrêter ce
  plan et documenter le besoin d'un export du fournisseur ou d'une capture PC
  vidéo+télémétrie simultanée. Aucun dataset ni réseau n'est entraîné.

### C2 — Valider le contrat des labels avant le rendu

**Créer :** `analysis/replay_validation.py`, `tests/test_replay_validation.py`.

- [ ] RED : timestamps désordonnés, identifiants mélangés, unités absentes, saut de
  téléportation, yaw inconnu et gaps doivent être détectés. Le lecteur peut avoir
  une fréquence d'export différente de la fréquence native : les deux sont distinctes.
- [ ] Lancer `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_replay_validation.py' -v`.
- [ ] Implémenter contrôle par voiture, delta t et vitesse dérivée ; seuils configurés
  dans `experiment.json`, pas constantes de voiture/circuit en production.

```python
import numpy as np

def interval_speeds(times, xyz):
    times, xyz = np.asarray(times, float), np.asarray(xyz, float)
    dt = np.diff(times)
    if xyz.shape != (len(times), 3) or not np.all(np.isfinite(xyz)):
        raise ValueError("invalid position series")
    if not np.all(np.isfinite(times)) or np.any(dt <= 0):
        raise ValueError("invalid time series")
    return np.linalg.norm(np.diff(xyz, axis=0), axis=1) / dt
```

  Publier distribution delta t, fraction disponible, quantification apparente,
  vitesses/jumps et orientation manquante. Ne pas interpoler un saut/retour stand.
- [ ] GREEN puis full suite/docs-list/diff-check ; commit
  `feat: validate candidate replay spatial labels`.

### C3 — Rendre le passage avec une caméra reproductible

- [ ] Vérifier qu'ACC se lance et charge ce replay sur la machine choisie. Tester
  CrossOver seulement si déjà disponible/autorisé ; sinon accès PC approprié à
  établir. Ne pas déduire le succès d'une page de compatibilité.
- [ ] Configurer cockpit, FOV, siège, mouvements de tête, HUD, rendu 1920x1080 et
  fréquence cible 60 FPS ; sauvegarder captures des réglages et caméra/car_id.
- [ ] Capturer sur la machine qui rend, à vitesse de lecture 1x. Inclure plusieurs
  secondes avant/après le passage et un repère de temps replay consultable. OBS ou
  autre capture locale admise, mais mesurer ses timestamps et frames dupliquées.
- [ ] Répéter ce rendu pour la même voiture ; puis tester une deuxième voiture.
  Livrables `render-car-a-1.mp4`, `render-car-a-2.mp4`, `render-car-b.mp4` si possible,
  manifeste et rapport FFprobe. Pas de capture de la fenêtre cloud distante sur Mac.
- [ ] Arrêter avec `no_go_render` si replay incompatible, caméra non contrôlable,
  rendu instable non mesurable ou champ nécessaire absent. Ne pas passer à ML.

### C4 — Mesurer la synchronisation

**Étendre :** `analysis/replay_validation.py`, `tests/test_replay_validation.py` ;
**créer :** `scripts/replay_poc.py` avec commande `validate-sync`.

- [ ] RED sur séquence synthétique avec offset 1.5 s et dérive 0.1%, image dupliquée,
  pause et rupture de temps ; une seule paire d'ancres ne prouve pas la dérive.
- [ ] Implémenter `t_replay = a * t_video + b` sur >=3 ancres indépendantes,
  vérifier sur >=2 ancres tenues hors fit ; refuser si résidus non compatibles avec
  une transformation affine. Conserver toute pause/seek comme rupture à segmenter.

```python
def fit_clock(video_times, replay_times):
    a, b = np.linalg.lstsq(
        np.column_stack([video_times, np.ones(len(video_times))]),
        replay_times, rcond=None)[0]
    return float(a), float(b)
```

  Ancres : événements visibles ou affichage temps replay dont latence et précision
  sont contrôlées. La précision d'affichage donne une borne ; ne pas prétendre 20 ms
  si le seul timecode lisible est à la seconde. Objectif initial P95 <=20 ms sur les
  ancres de validation, erreur d'annotation incluse. Le résultat peut être no-go.
  Association labels/frame : interpolation entre samples voisins dans une même run,
  avec provenance et seuil max gap du lecteur ; orientation interpolée avec wrap,
  jamais naïvement entre +179° et -179°.
- [ ] Mesurer sur les deux rendus de car-a et car-b. Écrire `sync.json`,
  `frame-labels.csv`, planches surimprimées et `sync-review.json`.
- [ ] GREEN + vérification commune ; commit `feat: measure replay video synchronization`.

### C5 — Déterminer si ces labels permettent réellement `d/heading`

- [ ] Définir le point de la voiture représenté et la convention d'axes ; obtenir une
  géométrie de piste utilisable avec provenance. La trajectoire d'une seule voiture
  ne donne pas la largeur ni les bords de piste.
- [ ] Comparer les positions/orientations à une source indépendante lorsqu'elle
  existe : enregistrement PC simultané ou géométrie et repères contrôlés. La capacité
  de relire un replay n'implique pas que la shared memory fournisse toute la physique.
  Sans vérité indépendante, marquer précision métrique `not_established`.
- [ ] Produire `decision.json` : états `parser`, `units`, `coverage`, `camera`,
  `synchronization`, `geometry`, `label_accuracy`, `usage_rights`, chacun pass/fail/
  not_established avec preuves. `go_metric_dataset` exige tous pass et des budgets
  d'erreur en mètres/degrés définis **avant** l'évaluation avec l'usage visé. Sans
  objectif métrique mesurable établi, seul `go_visual_exploration` est possible.
- [ ] Écrire le résultat daté dans `docs/replay-feasibility-result.md`, enregistrer
  les commandes exactes et limites. Full suite/docs/diff ; commit documentaire.

## Ce qui vient seulement après un go

Créer une nouvelle spécification ML ; ne pas prolonger ce plan automatiquement.
Elle devra fixer : cible liée au repère stable de piste plutôt qu'à un tour idéal,
baseline sans image, baseline sans `s`, modèle temporel, erreurs de `s` injectées,
split par replay/session/pilote, test PS5 indépendant, métriques erreur/couverture,
annotation cible et apprentissage progressif. Aucun quota de tours ne remplace ces
preuves. Le premier débrief du plan B reste utilisable pendant cette recherche.
