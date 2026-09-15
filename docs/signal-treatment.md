---
summary: current video measurement semantics, missing values and evidence requirements for derived metrics
read_when:
  - interpreting or changing speed and pedal measurements
  - implementing video-derived metrics without inventing missing measurements
---

# Traitement des signaux et faits utilisables

Le code extrait la vidéo complète en mode explicite `automatic`, puis les annotations
servent à contrôler les résultats. Elles ne limitent pas toute l'extraction aux seules
plages annotées. Le mode `reviewed` garde son contrat historique de visibilité préalable.

## Contrat invariant

| Signal | Valeur publiée | Limite |
| --- | --- | --- |
| Vitesse | Lecture fraîche admise ou null, texte OCR conservé | Pas de médiane, ancien chiffre réutilisé ou reconstruction sous statut observed |
| Frein/gaz | Décodage de la barre avec qualité/raisons | Pas de lissage des attaques, dégressivité, interruptions ou blips |
| HUD absent/lecture inexploitable | Absence et raison, brut si disponible | Aucun zéro fabriqué ni maintien déguisé |
| `s` dérivé | Estimation avec composantes, provenance et incertitude | Pas de précision spatiale présumée ni distance latérale |

`observed` signifie lecture fraîche, pas vérité. En automatique les raisons de visibilité
non vérifiée demeurent. Une ROI grise non noire peut encore produire un zéro de pédale :
la présence du HUD n'est pas qualifiée par cette seule lecture. Le zéro d'une commande
relâchée et l'absence de HUD ne sont pas interchangeables.

L'admission de vitesse applique les paramètres validés dans `config/telemetry.yaml`
(variation et gap) sans remplacer la valeur rejetée. Contexte, temps et ruptures remettent
à zéro le support temporel. Le refus d'une vraie chute à l'impact reste une limite
possible ; ne pas ajuster des seuils pour embellir le premier rapport.

Les wrappers legacy et anciens artefacts HELD restent lisibles et distincts. Les
interpolations internes d'odométrie ne remplissent pas la série de vitesse publiée.
Une régression/lissage de vitesse serait une série estimée séparée ; elle est différée.

## Calibration des pédales native 1080p — correction du 15 septembre 2026

Le profil `ps5_full_map_1080p` utilisait une largeur de153 pixels pour une barre utile
allant de x=1758 à1901 inclus, soit144 pixels. La marge droite de9 pixels faisait
lire un plein gaz à144/153×100 =94,12 %. `config/roi_config.yaml` borne désormais
les deux pédales à144 pixels ; aucune modification de seuil couleur ou temporel,
aucun lissage ni remise à l'échelle arbitraire des pics de séance.

Sur les21 images natives annotées existantes de la source incidents, relues uniquement
pour les barres, l'erreur absolue moyenne passe de1,60 à0,25 point pour le frein et
de3,12 à0,41 pour les gaz. Les2 points frein et7 points gaz annotés100 % lisent100 %.
Les niveaux intermédiaires s'améliorent aussi (frein54 % :50,98→54,17 %).
Petits résidus persistants : erreur maximale0,97 point frein et1,81 point gaz sur
ces points. Ce contrôle local n'établit ni calibration générale ni précision temporelle.

Preuves locales : `data/lab/coaching-reliability/run-030/reports/point-checks.json`,
`verification.json` et `verify_calibration.py`. Empreintes des21 images vérifiées,
format1920×1080/60 vérifié par les métadonnées existantes ; aucun nouvel OCR ni replay
vidéo. Régression reproduite avant correction,24 tests profil/contrôles/config passent.
Les profils historiques720p restent inchangés, sans nouvelle investigation.

La correction s'applique aux extractions avec ce profil ; la séance run-031 et ses
épisodes utilisent désormais les pédales réextraites. Les artefacts
run-024 et les épisodes run-029 gardent leur ancienne calibration et ne sont pas
réécrits. Pour publier une séance corrigée, réextraire les seules pédales dans de
nouveaux artefacts et recalculer les épisodes : ne pas simplement remplacer leurs
pics par100 %, ni supposer les événements inchangés près des seuils. Les valeurs
manquantes/raisons et Gate A FAIL, `coaching_eligible=false`, restent préservés.

## Admission des faits et portée du contrat historique

Le [contrat de l’export déjà implémenté](specs/2026-09-13-session-coaching-report.md) autorise le rapport
expérimental sans déclarer Gate A réussi. Il exige une décision locale par fait :
source, champ, valeur/intervalle contrôlé, qualité, raison, borne et limite.

- Une annotation ponctuelle ne valide pas toute la courbe.
- Une durée/épisode nécessite la revue de son intervalle pertinent.
- Un minimum peut être caché par un trou ; il reste alors non comparable.
- Le plein gaz souvent extrait à94.12% et les résidus0.65–1.70% ne prouvent pas une
  erreur de conduite. Aucun calcul sensible à ces extrêmes sans qualification adaptée.
- Un blip peut être automatique. Ne pas conclure à une action volontaire ni inférer
  TC/ABS, angle volant ou trajectoire idéale depuis les seules pédales.
- Les observations visuelles sont revues et attribuées, ou restent inconnues.

Les seuils de validation générale, rôles de sources, approbations et exclusions ne
changent pas. `coaching_eligible=false` reste inchangé. La priorité est désormais de
récupérer les données depuis la vidéo avant la plateforme, selon le
[plan unique](plans/video-to-agent-platform.md). Les conditions spécifiques de l'ancien
export ne deviennent pas une obligation de revue visuelle exhaustive de chaque future métrique. Les résultats passés sont
[archivés](archive/README.md). [État de départ](automatic-system-trial.md).
