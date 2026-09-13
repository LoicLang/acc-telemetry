---
summary: current fresh-measurement semantics and evidence rules for the experimental session report
read_when:
  - interpreting or changing speed and pedal measurements
  - deciding how the first report handles missing or unverified values
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

## Admission des faits du premier export

Le [contrat actif](specs/2026-09-13-session-coaching-report.md) autorise le rapport
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
changent pas. `coaching_eligible=false` reste inchangé ; la nouvelle priorité porte sur
un fichier expérimental utile, pas une certification. Les résultats passés sont
[archivés](archive/README.md). [État de départ](automatic-system-trial.md).
