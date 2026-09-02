---
summary: durable ACC PS5 telemetry roadmap, reliability stage gates, and blocked downstream coaching work
read_when:
  - working on ACC PS5 telemetry reliability
  - changing s, lap transitions, quality, segmentation, or coaching priorities
---

# ACC PS5 telemetry plan

## Current baseline

The validated baseline is a 1280×720 ACC PS5 recording with the static full-map HUD. The extractor reads controls, speed, gear, lap state, and minimap position. The map profile uses relaxed white bounds and 60 samples across the complete video.

## Longitudinal coordinate `s`

`s` represents progress along the extracted minimap path. In the domain it is normalized from `0.0` at the captured lap start to `1.0` near the next crossing. CSV compatibility currently exposes the same information as `track_position` from 0 to 100.

`s` is an estimated path coordinate, not physical distance in meters. Confidence depends on correct map extraction, lap anchoring, travel direction, and red-dot detection.

## Passages imparfaits

Les passages imparfaits ne doivent pas disparaître silencieusement. Une occlusion, un point rouge mal détecté, un saut OCR ou une transition de tour incertaine reste visible dans la qualité des données. Une valeur peut être conservée, tenue temporairement ou interpolée, mais son origine doit rester explicable.

L’analyse pilote doit pouvoir exclure une zone de faible confiance sans supprimer les observations brutes.

## Qualité et anomalies

Le contrat distingue : observé, manquant, tenu, interpolé et anormal. Les anomalies portent une raison concrète, par exemple vitesse hors plage ou `s` hors de `[0, 1]`. Les valeurs sources sont conservées pour permettre une validation humaine et améliorer l’extracteur.

Les seuils actifs de position, récupération OCR et normalisation sont versionnés. Une modification de seuil doit être testée sur une fixture puis sur une vidéo locale connue.

## Futur latéral `d`

`d` représentera un jour l’écart latéral signé par rapport à une ligne de référence. Il n’est pas calculé aujourd’hui : le minimap vidéo fournit une position le long du tracé, mais pas encore une largeur de piste ni une projection latérale suffisamment fiable.

Avant d’ajouter `d`, il faudra définir une géométrie de référence, un signe gauche/droite, une unité, une confiance et une méthode d’évaluation sur des virages connus.

## Prochaines étapes hors cleanup

1. Exécuter une session Spa contrôlée et conserver la vidéo dans une fiche de séance.
2. Mesurer la couverture et la monotonie de `s` sur un tour complet.
3. Annoter manuellement quelques passages imparfaits et comparer les drapeaux qualité.
4. Définir un premier segment de virage avant tout score de coaching.

Ces étapes sont une direction produit, pas des fonctionnalités incluses dans la remise à plat actuelle.
