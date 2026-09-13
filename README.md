# ACC Telemetry — premier export GPT local

Le prochain livrable est **`session_coaching.md`**, un fichier expérimental autonome
produit à partir d'une vraie session ACC PS5, que le pilote joint lui-même à GPT pour
obtenir une priorité et des exercices étayés. L'extraction existe ; cet assembleur et
le fichier final ne sont **pas encore implémentés**.

Commencer par [l'état courant](docs/current-status.md), puis suivre
[le plan actif en quatre lots](docs/plans/2026-09-13-first-gpt-export.md) et
[le contrat du fichier](docs/specs/2026-09-13-session-coaching-report.md).
Le premier travail est de relire les artefacts run-024 et sélectionner les passages,
sans refaire l'OCR. Gate A reste FAIL et `coaching_eligible=false`, mais cet export
expérimental à portée limitée est explicitement autorisé. La qualification générale,
la référence professionnelle et le suivi de l'entraînement viennent ensuite.

## Moteur local existant

Seules les captures **1920x1080 à exactement 60 fps CFR**, avec HUD statique full-map ACC
et profil `ps5_full_map_1080p`, sont admises pour un nouveau traitement. Pas d'upscaling,
resampling,720p ou59,94fps. Prérequis : Python 3.10+ et Tesseract OCR.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Exemple d'extraction, **uniquement lorsqu'un nouveau traitement est nécessaire** :

```bash
PYTHONPATH=src python main.py \
  data/sessions/2026/example/raw/session-1080p60.mov \
  --profile ps5_full_map_1080p --measurement-mode automatic \
  --output data/sessions/2026/example/reports \
  --artifact-dir data/sessions/2026/example/processed/session-001
```

La CLI produit CSV, HTML et artefacts telemetry-v2. Le mode `automatic` extrait sans
annotations d'entrée ; les sorties gardent leurs raisons de visibilité non vérifiée.
Le mode historique `reviewed` reste le défaut et exige des plages revues pour publier
vitesse/pédales. Les nulls, lectures brutes et transitions de pédales restent conservés.
Voir [le résultat run-024](docs/automatic-system-trial.md) et
[le contrat des artefacts](docs/session-artifacts.md).

## Structure et données

`extraction -> normalization -> domain -> analysis -> visualization` ; l'application
orchestre et les adaptateurs restent minces. [Architecture](docs/architecture.md).
Les composants web hérités ne font pas partie du jalon local ; aucun hébergement,
service web ou appel API GPT n'est nécessaire.

Vidéos immuables dans `data/sessions/.../raw/`, dérivés dans `interim/`, `processed/`
ou `reports/`, expériences dans `data/lab/`. Vidéos, exports complets, OCR et rapports
personnels restent ignorés par Git. [Organisation des données](data/README.md).

## Vérifications et documentation

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
./scripts/docs-list
```

Les tests utilisent des fixtures et ne modifient pas les vidéos personnelles.
[Règles de travail](AGENTS.md) · [Contribution](CONTRIBUTING.md) ·
[Direction produit](docs/acc-ps5-plan.md) · [Contexte produit](docs/product-context.md).
Les documents historiques contenant des preuves sont [archivés](docs/archive/README.md) ;
les anciens plans et guides obsolètes ont été retirés pour éviter les reprises contradictoires.
