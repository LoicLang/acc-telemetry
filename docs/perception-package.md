---
summary: implemented M1 full-lap perception package, neutral event settings, media clocks and local preview
read_when:
  - generating or reviewing the M1 scene and control timeline
  - changing neutral event detection, zone routing or media synchronization
---

# M1 — un tour complet, scène et commandes

Premier prototype livré sur le tour HUD4 de run-024 : frames19–8784, intervalle vidéo
[0,316667 ;146,416667[ s, soit8766 images. Les bornes sont celles du compteur confirmé,
pas un chronométrage physique ni une preuve de tour légal. Aucune nouvelle extraction OCR.

## Commandes locales

Génération dans une destination nouvelle (la commande n'écrase aucun dossier) :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.perception \
  --session data/lab/coaching-reliability/run-024/processed/crash-session \
  --zones data/lab/coaching-reliability/run-027/interim/zones.json \
  --output NOUVEAU_DOSSIER --lap 4 \
  --detail-start 39 --detail-end 57 \
  --sequence-start 49 --sequence-end 51 --sequence-step 0.1
```

Résultat déjà disponible : `data/lab/coaching-reliability/run-027/reports/lap-4/`.
Le lecteur requiert que ce dossier reste groupé. Prévisualisation locale facultative :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.perception_preview \
  --directory data/lab/coaching-reliability/run-027/reports/lap-4 --port 8767
```

Ouvrir `http://127.0.0.1:8767/`. Ce serveur de lecture est lié uniquement à localhost,
limité au dossier choisi et prend en charge les plages HTTP nécessaires à la recherche
dans les vidéos. Ce n'est pas une API métier ou un site hébergé. Ctrl-C l'arrête.
L'ouverture directe file:// n'a pas été validée par l'outil navigateur, qui la refuse ;
la navigation et la vidéo ont été vérifiées via la prévisualisation HTTP locale.

## Contenu et contrats

- `perception.json`, schéma `lap-perception-v1` : identité source/artéfact/fiche de zones,
  bornes du tour, réglages, tous les samples sélectionnés, qualités/raisons/bruts,
  index des zones, candidats d'événement et intervalles manquants.
- `samples.csv` :8766 lignes, temps vidéo et temps parent déclaré distingués ; les
  valeurs d'origine et leurs qualités restent conservées.
- `index.html` : vidéo du tour, sélection de zone, trois courbes, valeurs de l'image
  affichée, navigation image par image, événements et images du détail. Aucune ressource
  réseau extérieure. Les courbes et valeurs principales affichent les observations
  fraîches ; les valeurs non fraîches restent dans l'audit avec leur qualité.
- `video/lap.mp4`, `video/detail.mp4` : clips natifs1080p60CFR, plages de frames connues,
  sans redimensionnement ni resampling. Audio conservé s'il existe, comme contexte.
- `detail/` :21 PNG natifs à0,1s de49 à51s et quatre planches chronologiques. Le clip
  détaillé couvre39–57s, donc l'approche et la conséquence dépassent la séquence dense.
- `OBSERVATIONS.md` : index destiné à préparer les pièces réellement transmises au
  modèle. Texte seul ne donne pas accès aux images ou vidéos par leurs chemins locaux.
- `integrity.json` : hashes du paquet, correspondance des frames et conservation des
  entrées. Publication dans un dossier nouveau, via renommage exclusif.

Les zones doivent constituer une partition contiguë du tour, sans trou/chevauchement.
La fiche `perception-zones-v1` est liée au hash/taille de la vidéo et au numéro de tour.
Ses images de revue sont vérifiées. Les14 zones de cet essai sont des fenêtres de
navigation grossières attribuées après lecture de30 vues espacées d'environ5s ; ce
ne sont pas des débuts de virage/apex/sorties ou plans de chronométrage exacts.

## Événements neutres

`analysis/perception.py` est pur. `config/perception.yaml` contient les réglages
validés : seuil actif5%, inactif2%, persistance0,10s, rupture après0,05s sans continuité.
Ce sont des paramètres d'indexation, pas des cibles de conduite ou une qualification
empirique de latence. Aucun sample n'est lissé/modifié pour détecter les événements.

Le détecteur conserve premier candidat, confirmation, dernière preuve précédente,
qualité et raisons. Un état déjà actif au début/après lacune est nommé « actif, début
inconnu », jamais nouveau début certain. Absence, valeur non fraîche ou gap casse la
continuité et ne crée pas de relâchement fictif. Un changement de rapport exige deux
lectures fraîches adjacentes et reste un candidat ; une erreur OCR peut subsister.
Les blips de gaz ne deviennent pas des actions volontaires par leur durée.

Résultat du tour :95 candidats (12 attaques/12 fins de frein,13 reprises/13 coupures
de gaz,44 changements de rapport et1 état de gaz actif initial). Cela ne signifie pas
95 événements de pilotage indépendamment validés. Aucune qualification de faute.
Vitesse fraîche8757/8766, chaque pédale8766/8766, rapport8764/8766 ; les trous sont conservés.

## Horloges et vérification

Frame locale de la vidéo i = `lap.start_frame + i`. Le lecteur utilise
`requestVideoFrameCallback.mediaTime` lorsqu'il existe, donc le temps de l'image
présentée, pour choisir le sample. Le mode de secours suit l'horloge de lecture et
est explicitement approximatif. Les horloges affichées par le HUD ne remplacent pas
les timestamps source. Les bornes d'un détail sont ramenées aux frames natives et
ses bornes demandées/obtenues sont conservées.

Tests ciblés : transitions/pulses/gaps, états tronqués, zones couvrantes, horloges,
refus des mauvaises sources/destinations, échec sans publication, sérialisation HTML,
trim réel d'une vidéo synthétique et plages HTTP/confinement du prévisualiseur.
45 tests ciblés passent, y compris les régressions des artefacts et du premier rapport.
Pas de relance de toute la suite : nouveaux consommateurs isolés, moteur inchangé.

Revue navigateur : détail39s atteint la frame2340 ; image49s =frame2940, vitesse143 ;
avance d'une image =frame2941 à49,017s, vitesse144. La sélection de Pouhon atteint72s,
frame4320, puis le curseur suit la lecture. Les limites et les nulls restent affichés.
La première prévisualisation sans support Range ne cherchait pas dans la vidéo ; le
prévisualiseur local résout ce problème, sans modifier les médias ou refaire l'OCR.

## Limites et suite

Gate A FAIL, `coaching_eligible=false`, `d` indisponible. M1 couvre un tour et une
première fenêtre détaillée, pas encore toute une session ni toutes ses transitions
en images denses. L'entrée complète dans un modèle sans historique reste à tester.
L'extension à d'autres tours nécessite leurs zones revues, sans réutiliser des temps
absolus d'un autre tour. Le code n'effectue aucun diagnostic de conduite.

[Plan actif](plans/video-to-agent-platform.md) · [Passation](current-status.md).
M2 nécessite toujours le logiciel/service ACC sur Mac et la durée du créneau avant
préparation d'un logger PC adapté. Aucune capture PC ni entraînement n'a été lancé.
