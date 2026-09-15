---
summary: first downstream HUD pedal episodes with temporal descriptors, raw evidence and bounded annotation checks
read_when:
  - generating brake and throttle episodes from frozen telemetry-v2 artifacts
  - interpreting episode boundaries, missing data, peaks, release tails or overlap
---

# Épisodes de commandes HUD — incrément 1A

Implémentation : [analyse](../src/acc_telemetry/analysis/control_episodes.py),
[publication](../src/acc_telemetry/application/control_episodes.py),
[commande](../scripts/control_episodes.py). Aucun nouvel OCR, décodage vidéo, lissage
ou changement de seuil. **Gate A reste FAIL ; `coaching_eligible=false`.**

## Reproduire

Depuis la racine, choisir un dossier de sortie neuf :
la commande ci-dessous reproduit la version historique run-029. Pour le travail
courant sur les pédales recalibrées, utiliser la séance run-031 indiquée dans la
passation et une nouvelle destination ; conserver les deux provenances distinctes.

```sh
PYTHONPATH=src .venv/bin/python scripts/control_episodes.py \
  data/lab/coaching-reliability/run-024/processed/crash-session \
  data/lab/coaching-reliability/run-029/processed/control-episodes \
  --annotations data/lab/coaching-reliability/run-008/processed/agent-reviewed-corpus-v2/b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124/labels.json
```

`--settings` peut désigner un fichier au format de `config/perception.yaml` ; les
valeurs par défaut sont reprises sans campagne de seuils. Les artefacts doivent déjà
porter la preuve de format natif 1920×1080 exactement 60 fps CFR. Le lecteur vérifie
empreintes/enveloppes, puis le calcul vérifie l'ordre et la correspondance frame/temps.
La vidéo n'est pas ouverte ; sa provenance est celle du manifeste vérifié. Publication
atomique dans un nouveau dossier, refus d'écraser ou d'écrire dans raw/les sources.

## Données et définitions

- `episodes.json` (`control-episodes-v1`) : épisodes, événements originaux, lacunes,
  relations coupure/reprise, intersections frein/gaz, configuration et provenance.
- `pedal-samples.jsonl` : valeurs, qualités et raisons originales des deux pédales,
  y compris null. Chaque profil se retrouve par ses frames inclusives. Les épisodes
  bornés incluent la frame de fin dans leur profil pour montrer le résidu final.
- `annotation-checks.json` : points numériques et écarts, deux événements B2 déjà
  annotés, contexte fourni ; aucun label nouveau. Optionnel sans `--annotations`.
- `integrity.json` : empreintes des résultats et vérification finale des entrées.

| Objet | Convention |
|---|---|
| Début/fin | Candidats de `control_events` : hystérésis 5/2 %, persistance 0,1 s. Conserve instant candidat, confirmation et preuve précédente. |
| Épisode actif | Intervalle semi-ouvert début candidat → fin candidate. De brefs retours sous le seuil non confirmés peuvent rester à l'intérieur. |
| Bord actif sans début connu | `initial_active_evidence`, `start_candidate=null`, troncature gauche ; aucune apparition initiale présentée comme une reprise confirmée. |
| Lacune | Toute lecture non fraîche/hors plage ou frame absente coupe le segment. Aucun appariement à travers un trou, même inférieur à `max_gap_s`. |
| Bord sans fin confirmée | Fin observée au dernier sample frais ; `end_candidate=null`, troncature droite. Pas d'extrapolation à la frame suivante. |
| Durée | Fin candidate − début candidat ; null si une borne manque. `observed_span_s` décrit seulement le fragment observé. |
| Pic | Maximum des lectures avant la fin candidate, avec première et dernière frames exactement égales au maximum ; reste un **pic observé**. |
| Temps au pic | Premier pic observé − début candidat ; null si début tronqué. Sur une fin tronquée, le vrai pic peut être hors fenêtre. |
| Queue de relâchement | Dernier maximum exact → fin candidate, durée et pente moyenne en points de %/s. Le profil peut remonter ; ce n'est pas un début de relâchement détecté. Fin manquante → null. |
| Reprise | Relation entre épisodes successifs d'une même commande dans un même segment continu, avec durée de l'état inactif candidat. Pas de groupement par virage ni détection des modulations internes. |
| Chevauchement | Intersection des intervalles d'états candidats frein/gaz. Durée observée et indicateur de bornes limitées ; pas une preuve de commandes physiques simultanées. |

Les liens d'épisode portent frames/temps natifs, champ et segment d'évidence.
`clip_origin` donne l'origine du temps source. L'absence d'intersection dans la liste
ne prouve pas une absence de chevauchement pendant les lacunes : consulter `gaps`.
La visibilité revue s'ajoute comme preuve séparée, sans effacer les raisons originales
`hud_visibility_unverified` ni transformer la disponibilité en exactitude.

Pas de début de relâchement qualifié (`release_onset_s=null`), de plein gaz calibré,
de paliers/réapplications internes, d'intégrale ou de distance dans cet incrément.
`s` reste une fraction ; `steering` reste un candidat HUD non physique. Les agrégats
hérités vitesse/tours ne sont pas utilisés ; leurs défauts connus restent hors scope.

## Calibration ultérieure

La [largeur native des pédales](signal-treatment.md) est corrigée en run-030.
Run-029 ci-dessous utilise toujours les samples historiques run-024 : modifier la
configuration ne recalibre pas un export déjà extrait. Ne pas comparer ses pics à
ceux d'une future extraction corrigée sans distinguer les deux calibrations.

Run-031 fournit maintenant une séance et des épisodes recalibrés dans
`data/lab/coaching-reliability/run-031/processed/`.91 épisodes restent présents, mais
une paire coupure/reprise est supprimée et une autre apparaît ; deux bornes se déplacent.
177 événements sur181 conservent leur identité et leurs temps. Les nouveaux pics à100 %
peuvent déplacer le premier/dernier maximum exact. Comparaison et quatre exemples dans
`run-031/reports/results.md` ; les chiffres run-029 ci-dessous restent historiques.

## Qualification temporelle ciblée — run-032

Huit fenêtres/208 images permettent une comparaison locale aux changements visibles
([passation](current-status.md), données locales `run-032/reports/timing-review.json`).
Les nouvelles revues sont provisoires, réalisées par modèle, non aveugles et distinctes
des annotations humaines. B2 : durée candidate2,950s compatible avec2,933–2,967s entre
les deux bornes relues ; pas de revue dense de l'intérieur ni de latence physique.

Deux disparitions de gaz donnent des décalages locaux50–66,7ms et33,3–50ms. Une paire
visible off/on12982/13018 manque : petits fragments colorés sous les textes produisent
2,0833%, maintenant l'état actif. L'épisode20190–20305 contient une interruption visible
non représentée comme coupure, avec des fragments donnant5%. La continuité calculée
est celle de l'hystérésis, pas nécessairement celle du remplissage HUD ou de la pédale.
Le lecteur doit conserver cette limite lors de toute utilisation des durées/reprises.

Le problème est localisé dans `extract_bar_percentage` : fragments recherchés partout
sur les lignes et lignes vides écartées du percentile. Aucun seuil/extracteur n'est
modifié par cette revue. Dernier maximum et certaines fins restent sans référence
univoque ; valeurs de précision correspondantes null, pas de score global.

## Correction des contre-exemples — base run-033

Le [mode de remplissage spatial](signal-treatment.md) corrige les fragments du HUD
sans changer les seuils temporels. La séance recalculée conserve les impulsions brèves
dans ses samples ; une impulsion sous la persistance requise ne devient pas un épisode
confirmé. Off/on12982/13018 réapparaissent, off2621 est retrouvé, l'épisode artificiel
20190–20305 disparaît. Les bornes du frein B2 restent11246/11423.

Base active : `data/lab/coaching-reliability/run-033/processed/`,83 épisodes (37 frein,
46 gaz),165 événements,53 intersections. Les comptes changés ne qualifient pas tous les
événements :208 images ciblées et21 points par pédale ont été vérifiés. Les limites
physiques et les ambiguïtés non résolues de run-032 restent distinctes. Voir les
résultats et listes ajoutées/retirées dans `run-033/reports/`.

## Résultat et portée des preuves

Run-029 : 91 épisodes (44 frein, 47 gaz), dont 89 bornés et deux gaz tronqués aux
bords de séance ; 89 relations de reprise, 61 intersections candidates, aucune lacune
numérique de pédales. Les 181 candidats frein/gaz sont identiques à l'index existant.
Les 29 402 lignes de pédales conservent exactement valeurs, qualités et raisons.
Exemples consultables dans `run-029/reports/examples.md` et vérification locale dans
`run-029/reports/verification.json` sous `data/lab/coaching-reliability/` (ignoré).

Les 21 points par pédale reproduisent MAE frein 1,60 et gaz 3,12 points, maximum 5,88.
B2 frein commence à la frame 11246 dans l'intervalle annoté 11245–11246. B2 gaz passe
sous 2 % à 11255, soit 0,250–0,267 s après le relâchement décrit à 11239–11240 :
définitions différentes. Ce contre-exemple interdit d'assimiler la résolution de
16,7 ms ou la persistance de 100 ms à une précision temporelle physique démontrée.

Aucune vérité dense d'épisode complet : précision de durée, temps au pic et relâchement
restent null dans les preuves. Les pics proches de 94 %, résidus et blips automatiques
ne sont pas des défauts du pilote. Voir le [catalogue](driving-metrics.md) B03–B06,
A01/A03/A04/A06 et Q02/Q03 pour les capacités qui restent à qualifier.

Vérification : 33 tests ciblés analyse/événements/publication/artefacts, contrôle des
empreintes, invariance des 181 candidats et des pédales, arithmétique de quatre exemples.
Aucune suite vidéo complète ni nouvelle expérimentation de seuils.
