# ACC Telemetry — plateforme de données de conduite pour agents IA

**Transformer une vidéo de conduite en données stockées, mesurables et explorables
par un agent.** L'agent pourra comparer trajectoires et commandes, consulter une
référence, rechercher les difficultés récurrentes et demander les preuves utiles.
La plateforme est la destination ; un PDF est un export facultatif.

**Priorité actuelle : récupérer et qualifier les données depuis la vidéo.** La base
applicative, le serveur MCP et les skills de navigation viendront après ce socle.
L'acquisition directe PC pourra ensuite remplacer une partie de l'extraction vidéo,
en conservant les concepts de mesures, passages, références et qualité.

## Reprendre le travail

1. [État courant et prochaine action](docs/current-status.md).
2. [Plan actif unique](docs/plans/video-to-agent-platform.md).
3. [Audit du code : données réellement disponibles](docs/video-data-audit.md).
4. [Catalogue des72 entrées recherchées](docs/driving-metrics.md).

Le code lit déjà vitesse, frein/gaz, rapport et compteur ; il estime une progression
normalisée et indexe les transitions de commande. **Trajectoire métrique, dynamique
et synthèse des pertes récurrentes restent à construire.** Gate A reste FAIL,
`coaching_eligible=false` ; données manquantes et incertitudes sont conservées.

## Exécuter le moteur local

Environnement de l'audit : Python3.13.2. Utiliser Python3.12+ ; le code emploie notamment
`StrEnum`, incompatible avec l'ancienne indication3.10. Tesseract et FFmpeg/FFprobe
sont nécessaires. Depuis la racine :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Seules les nouvelles captures **1920x1080 à exactement60 fps CFR**, avec HUD compatible
et profil `ps5_full_map_1080p`, sont acceptées. Pas d'upscaling, resampling ou59,94fps.
Exemple pour une nouvelle source, lorsque le traitement est nécessaire :

```bash
PYTHONPATH=src python main.py \
  data/sessions/2026/example/raw/session-1080p60.mov \
  --profile ps5_full_map_1080p --measurement-mode automatic \
  --output data/sessions/2026/example/reports \
  --artifact-dir data/sessions/2026/example/processed/session-001
```

Le mode explicite `automatic` extrait sans annotation d'entrée et conserve les raisons
de visibilité non vérifiée. Le mode `reviewed`, défaut historique, exige des plages
revues pour publier vitesse/pédales. [Signaux](docs/signal-treatment.md) et
[artefacts telemetry-v2](docs/session-artifacts.md).

Les épisodes de commandes sont livrés. Run-031 contient les pédales recalibrées et
préserve les autres canaux hérités de run-024 ; c'est la base actuelle pour les prochains
contrôles temporels. Suivre la passation pour choisir les artefacts, sans relancer l'OCR
pour des calculs aval. Les sources et exports personnels restent locaux, hors Git.

## Résultats expérimentaux conservés

- [Extraction automatique run-024](docs/automatic-system-trial.md).
- [Épisodes et pédales recalibrées run-031](docs/control-episodes.md).
- [Lecteur d'un tour, run-027](docs/perception-package.md) : vidéo, courbes, zones et index.
- `session_coaching.md`, run-026 : [contrat reproductible](docs/specs/2026-09-13-session-coaching-report.md).
- run-028 : un essai externe de perception sur PDF ; bon retour local, volume impropre
  à une séance entière. Les fichiers et limites figurent dans la passation.

Ces livrables prouvent des briques du système ; ils ne constituent pas la plateforme.

## Architecture, données et vérification

`capture -> extraction -> normalisation -> domaine -> analyse -> visualisation`.
Les couches applicatives sont partagées entre adaptateurs. Les composants web hérités
restent utilisables ; ils ne sont pas le futur serveur MCP. [Architecture](docs/architecture.md).

Sources dans `data/sessions/.../raw/`, dérivés dans `interim/`, `processed/` ou `reports/`.
[Organisation des données](data/README.md). Aucune vidéo ou télémétrie personnelle dans Git.

Vérifications proportionnées à la modification ; commandes disponibles :

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
./scripts/docs-list
```

[Règles](AGENTS.md) · [Contribution](CONTRIBUTING.md) · [Preuves historiques](docs/archive/README.md).
La vision vit ici, la séquence de réalisation dans un seul plan et la reprise dans
une seule passation. Les anciens documents de cadrage redondants ont été retirés.
