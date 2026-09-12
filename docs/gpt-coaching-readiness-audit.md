---
summary: verified local repository audit separating working extraction from the missing portable GPT coaching dossier
read_when:
  - deciding what actually remains before a useful GPT coaching report
  - resuming the September 12 local-only delivery plan
---

# Audit : de la télémétrie locale au dossier de coaching GPT

Vérifié le 12 septembre 2026 sur `f4c43ed`. Analyse et planification seulement : aucune
nouvelle extraction de télémétrie, modification du moteur ou campagne exhaustive.
L’essai manuel complémentaire et ses huit images de contexte sont décrits séparément
dans `gpt-coaching-report-trial.md`.
La demande porte sur **notre amélioration locale**, puis sur des fichiers que le pilote
joint lui-même à GPT. L'ancienne interface web n'est pas un livrable de ce plan.

## Conclusion

Le moteur sait maintenant extraire une vidéo entière. Le produit qui transforme ces
mesures en un dossier de coaching autonome n'est pas implémenté. Refaire le compteur
ou afficher encore les mêmes courbes n'ajouterait pas cette partie manquante.

La prochaine livraison doit être définie par ce que GPT pourra effectivement lire :
contexte, passages comparables, métriques calculées et sourcées, preuves visuelles,
limites et consigne d'analyse. Le plan opérationnel est
[2026-09-12-local-gpt-coaching-delivery.md](plans/2026-09-12-local-gpt-coaching-delivery.md).

## Faits vérifiés et conséquences

| Sujet | Preuve actuelle | Conséquence pour le produit |
| --- | --- | --- |
| Extraction complète | Run-024 : 29 402 images, 1080p60 CFR, environ 400,53 s pour 490,03 s de vidéo | Le temps d'extraction n'explique pas une semaine d'itérations ; aucune optimisation de performance prioritaire |
| Vitesse | 29 298 valeurs, 99,65 % de disponibilité ; 21/21 points approuvés exacts | Série utilisable pour inspection ; exactitude hors points annotés inconnue |
| Pédales | 100 % de valeurs ; MAE frein/gaz 1,60/3,12 points sur 21 références par champ | Suffisant pour voir les formes ; plein gaz souvent à 94,12 %, résidus de 0,65–1,70 %, maximum d'erreur 5,88 points |
| Compteur | Run-024 face à run-022 : 29 402 lectures fraîches exactes, 4 événements sans extras/manques ; BMW déjà vérifié séparément | Réutiliser la vérité ; ne plus refaire sa revue sur les captures connues |
| Progression `s` | 26 844 valeurs, 91,30 % ; aucune précision spatiale indépendante établie | Aide à retrouver une zone ; ne pas convertir les écarts en mètres ni en faire l'alignement obligatoire du premier dossier |
| Valeurs absentes | 104 vitesses manquantes ; segment V-CRASH-15 à 28/31 malgré 679/683 au total | Le taux global ne qualifie pas un minimum ou un événement situé dans un trou |
| Visibilité automatique | Le mode automatique lit sans annotation et marque la visibilité non vérifiée | 100 % de pédales ne prouve pas un HUD lisible ; il manque une qualification de cette admission |
| Provenance | `TelemetrySample`, observations et artefacts avec hashes, temps, qualités, raisons | Base réutilisable ; pas besoin d'un nouveau format de télémétrie brute |
| Rapport lisible | Générateur run-024 `publish.py` local ignoré ; HTML/vidéos consultables localement | Démonstration réussie, mais génération du dossier non intégrée dans une commande versionnée |
| Analyse métier | `analysis/` contient `alignment.py` et `validation.py`, pas de modules de virage | Épisodes frein/gaz, sept métriques, comparaison et export de coaching restent à écrire |
| Sources de coaching | Une capture BMW candidate existe ; aucun cas prêt ni référence admise dans le code/les preuves actives | Confirmer le virage, trois passages et la référence ; ne pas inventer une cible idéale |
| Fiabilité | 323 tests passent ; Gate A reste bloqué, validation indépendante compatible manquante | Les tests logiciels ne remplacent pas la mesure sur une nouvelle capture |

Les quatre fichiers de session run-024 occupent environ 171 Mo décimaux : observations
61,03 Mo, samples 89,09 Mo, CSV 21,24 Mo, manifeste 12,6 Ko. Leur rôle est l'audit local.
Le dossier destiné à GPT doit sélectionner les passages utiles et fournir les calculs,
pas demander au modèle de découvrir le cas dans les 29 402 lignes de la session.

## Vérification supplémentaire, sans vidéo ni OCR

Le lecteur de pédales automatique, alimenté avec une ROI synthétique uniforme grise
non noire, publie `0.0 / observed / hud_visibility_unverified` pour frein et gaz.
Cela démontre que le contrôle actuel « ROI non noire » ne suffit pas à reconnaître le
HUD. Ce n'est pas une mesure de fréquence de faux positifs sur les vidéos réelles.
Le zéro d'une pédale relâchée et l'absence de HUD doivent pouvoir être distingués avant
un conseil automatique sur le temps sans pédales ou le chevauchement.

L'audit local est conservé dans
`data/lab/coaching-reliability/run-025/reports/planning-audit.json`. Les hashes des
quatre fichiers d'artefact run-024 ont été revérifiés. Aucun ancien label n'a changé.

## Cartographie du code à réutiliser

| Chemin sous `src/acc_telemetry/` | Responsabilité confirmée |
| --- | --- |
| `application/components.py`, `pipeline.py` | Construction et exécution locales, mode automatique, orchestration et progression |
| `extraction/laps.py`, `controls.py` | Lectures fraîches, OCR, décodeur de barres ; défauts restants de mesure |
| `application/session_artifacts.py` | Export/rechargement versionné ; point d'entrée pour travailler sans relancer l'OCR |
| `domain/telemetry.py`, `normalization/samples.py` | Valeurs typées, unités, nulls, qualité et raisons |
| `application/capture_validation.py`, `analysis/validation.py` | Évaluation des annotations et construction des preuves de fiabilité |
| `analysis/alignment.py` | Interpolation bornée et comparaisons diagnostiques ; ne remplace pas les repères physiques du cas |
| `visualization/interactive.py` | Courbes et résumé de session ; ne produit pas le dossier de coaching |
| `adapters/cli.py` | Entrée locale existante ; point d'intégration sans service web |

Absences confirmées : `domain/coaching.py`, `application/coaching_case.py`,
`analysis/corner_events.py`, `analysis/corner_metrics.py`, `analysis/corner_comparison.py`,
`application/coaching_media.py`, `visualization/coaching_dossier.py`, `adapters/coaching.py`.
Le plan B du 5 septembre décrit ces composants ; il n'en constitue pas l'implémentation.

## Pourquoi l'effort n'a pas encore produit le résultat attendu

**Faits :** l'historique contient plusieurs préparations/reprises de revue du compteur,
des labels rejetés et des vérifications de plus en plus exhaustives sur les mêmes
sources. Le rapport complet est arrivé tard. Run-023 utilisait la visibilité annotée
comme permission d'extraire ; le propriétaire demandait une extraction complète,
puis une validation sur les annotations. Run-024 a corrigé cette distinction.

**Analyse :** les étapes techniques et leurs preuves ont pris la place du critère de
livraison. L'exactitude d'un compteur a été poursuivie sans que la fabrication du
rapport final ait un chemin court, un périmètre figé et une définition de terminé.
Le plan de coaching existait, mais la sortie de fiabilisation restait ouverte.

La solution est une séquence de lots bornés, chacun avec un fichier consultable et
une décision de sortie. Cela ne justifie pas de déclarer le gate passé ou de masquer
les défauts. Une preuve manquante doit avoir un travail précis, pas une enquête indéfinie.

## Ce qui n'est pas nécessaire au premier dossier

Pas de site, API d'upload, serveur hébergé, appel API GPT automatique, nouvelle UI,
modèle de trajectoire, import `.rpy`, métrique latérale `d`, qualification de tous les
circuits, perfectionnement global de `s`, ni conseil basé sur TC/ABS ou le volant.
L'anomalie de l'upload web héritée est réelle mais **hors chemin de livraison local**.
Les références physiques en images et le temps source suffisent à aligner un premier
virage ; les mesures spatiales restent exclues tant qu'elles ne sont pas qualifiées.
