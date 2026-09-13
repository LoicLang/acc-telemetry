# ACC Telemetry — premier export GPT local

Le premier livrable est **`session_coaching.md`**, un fichier expérimental autonome
produit à partir d'une vraie session ACC PS5, que le pilote joint lui-même à GPT pour
obtenir une priorité et des exercices étayés. **L’assembleur et le vrai fichier run-026
sont livrés** : trois passages personnels, repères physiques revus et limites explicites.

Commencer par [l'état courant](docs/current-status.md), puis suivre
[le plan actif en quatre lots](docs/plans/2026-09-13-first-gpt-export.md) et
[le contrat du fichier](docs/specs/2026-09-13-session-coaching-report.md).
Le dossier réutilise les artefacts run-024, sans refaire l'OCR.
Gate A reste FAIL et `coaching_eligible=false`, mais cet export
expérimental à portée limitée est explicitement autorisé. La qualification générale,
la référence professionnelle et le suivi de l'entraînement viennent ensuite.

## Reproduire le premier fichier

Le livrable privé est `data/lab/coaching-reliability/run-026/reports/session_coaching.md`.
La fiche et ses images de preuve restent locales et ignorées par Git. Depuis le dépôt :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.session_report \
  --session data/lab/coaching-reliability/run-024/processed/crash-session \
  --case data/lab/coaching-reliability/run-026/interim/case.json \
  --output data/lab/coaching-reliability/run-026/reports/reproduction-02/session_coaching.md
```

Choisir une sortie nouvelle : fichier existant, source, répertoire d’artefacts et `raw/`
sont refusés. L’export vérifie les artefacts, la fiche liée au manifeste et les empreintes
des preuves revues. Aucun OCR, GPT ou service web n’est appelé. La relecture par le même
assistant permet un exercice de régularité local ; l’essai dans une nouvelle conversation
GPT et l’efficacité à l’entraînement restent non réalisés.

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
