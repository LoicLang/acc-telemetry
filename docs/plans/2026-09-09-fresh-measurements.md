---
summary: executable follow-up plan for fresh speed observations, unchanged pedal dynamics and separately gated optional regression
read_when:
  - implementing the September 9 signal-treatment decision after A7
  - preparing RED tests for speed freshness or assessing optional speed smoothing
---

# A8 — Mesures fraîches et respect des transitions

**Statut : plan préparé, implémentation non commencée.** Demande actuelle : documenter
et planifier. A8 poursuit la fiabilité A après son échec mesuré, sans démarrer B.
Spécification active : `docs/signal-treatment.md`. Référence produit :
`docs/specs/2026-09-05-reference-corner-coach-design.md`.
Résultats gelés : `docs/capture-validation-results.md`.

## Préparation réalisée

- [x] Lire AGENTS.md, l'index, le handoff, la spécification/plan A et Git.
- [x] Vérifier les artefacts et labels de développement : OCR brut exact sur 40/40
  points sélectionnés, avec erreurs introduites ensuite par la médiane.
- [x] Conserver le diagnostic séparé dans
  `data/lab/coaching-reliability/run-009/reports/speed-raw-vs-output.json`.
- [x] Formaliser : pas de lissage des pédales ; vitesse fraîche prioritaire ;
  régression de vitesse distincte, optionnelle et différée.

Ne modifier ni sources raw, ni corpus accepté, ni anciens rapports. Réutiliser la
branche `codex/coaching-reliability`, sans sous-agents. Les sorties d'implémentation
iront dans un **nouveau run libre**, pas par écrasement de run-008/run-009.

## S1 — Reproduire le retard sur le vrai chemin moderne (RED)

Fichiers : créer `tests/test_fresh_speed_observations.py` ; étendre si nécessaire
`tests/test_quality_roundtrip.py` et `tests/test_application_pipeline.py`.
Lire `extraction/laps.py`, `tests/test_speed_ocr_mode.py` et ses faux backends avant
modification. Les chemins de package ci-dessous sont sous `src/acc_telemetry/`.

- [ ] Faire lire une séquence descendante au **vrai** `LapDetector.observe_speed`
  avec backend texte contrôlé, puis au vrai pipeline. Préconditionner assez de lectures
  pour remplir l'historique ; vérifier qu'une nouvelle lecture « 246 » donne 246 à
  sa frame, jamais une médiane 255 marquée OBSERVED. Ajouter le cas ascendant.
- [ ] Vérifier un seul appel OCR par image/champ. Ne pas remplacer `observe_speed`
  par un mock retournant déjà le bon objet : cela masquerait le défaut.
- [ ] Cas trou OCR après valeur valide, texte mixte, non fini, ROI inexploitable,
  valeur hors limites, reprise après trou : brut/raison conservés, aucune mesure
  moderne fraîche provenant du passé. Garder les tests d'import des anciens HELD.
- [ ] Exécuter le fichier ciblé, conserver le RED et son motif. Distinguer dépendance
  OCR indisponible et échec fonctionnel ; les tests avec faux backend doivent tourner.

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_fresh_speed_observations.py' -v
```

## S2 — Séparer lecture fraîche et filtre legacy (GREEN)

Fichiers : `extraction/laps.py`, éventuellement `application/config.py` et
`config/telemetry.yaml` si une nouvelle règle d'admission est réellement nécessaire.

- [ ] Extraire une lecture OCR vitesse commune, sans changement gratuit du crop,
  prétraitement ou backend ; restaurer le mode OCR partagé après succès et exception.
- [ ] Faire utiliser au chemin moderne la valeur de cette image, le texte brut et
  une validation explicite. Ne pas appeler un wrapper qui applique médiane/maintien
  avant de créer `FieldObservation`. Garder `extract_speed` legacy identifiable.
- [ ] Séparer l'admission/rejet de la reconstruction : un outlier rejeté devient
  absent/anomalous avec brut et raison, jamais remplacé par une valeur calculée
  OBSERVED. Préserver les accélérations/décélérations valides ; tout contrôle temporel
  tient compte de delta-t et redémarre proprement après absence/contexte changé.
- [ ] Ne pas rendre chaque nombre plausible admissible sans garde HUD : S4 garde ce
  problème explicitement ouvert. Les 40 points exacts ne justifient pas un succès
  sur toutes les frames. Aucun réglage de seuil sur les résultats holdout.
- [ ] Vérifier tests S1, modes OCR, récupération legacy et régressions existantes.
  Le format telemetry-v2 peut garder ses champs actuels si leur sens reste compatible ;
  documenter la nouvelle empreinte et refuser une réinterprétation des anciens exports.
- [ ] Suite complète, docs et commit atomique de la correction avec son handoff.

## S3 — Vérifier la propagation et protéger les pédales

Fichiers : `application/pipeline.py`, `normalization/samples.py`,
`application/session_artifacts.py`, `adapters/web/models.py` et consommateurs seulement
si un défaut de propagation est révélé. Tests : `test_quality_roundtrip.py`,
`test_session_artifacts.py`, `test_control_observations.py`,
`test_comparison_api_quality.py`, `test_odometry.py` et `test_progress_fusion.py`.

- [ ] Pipeline -> record -> normalisation -> artefact -> relecture -> API : mêmes
  valeur fraîche, frame/temps, qualité, raisons et brut. Tester aussi les nulls et
  les anciens HELD sans les reclasser. Corriger seulement les consommateurs fautifs.
- [ ] Protéger les transitions synthétiques frein/gaz 0→100 et 100→0, freinage maximal
  puis dégressif, interruption brève, blip et absence HUD. Exiger les valeurs et temps
  d'origine après roundtrip, sans rampe fabriquée ni suppression des pics lisibles.
- [ ] Aucun nouveau filtre de pédales, champ lissé public, moyenne de secours dans
  l'API, ou interpolation à travers une absence. Les calculs B4 restent hors périmètre.
- [ ] Vérifier ce que reçoit l'odométrie : mesure fraîche admise ou absence explicite.
  Toute prédiction interne de progression conserve sa propre provenance et ne revient
  pas dans `speed_kmh`. Tester l'effet d'un outlier et d'un trou sur l'intégration.
- [ ] Exécuter les tests ciblés et complets ; commit séparé si cette étape révèle
  une correction distincte de S2, sinon inclure les régressions avec S2.

## S4 — Revalider le développement et maintenir les blocages A

Fichiers : scripts/analyses A7 existants, tests de capture, documentation des résultats.

- [ ] Avant replay, geler code/config et choix de développement. Produire de nouveaux
  artefacts BMW/incidents avec les revues existantes, puis les mesurer sans OCR via
  `scripts/validate_capture.py`. Publier erreurs brutes et sorties modernes séparées,
  abstentions, qualité, dénominateurs, exclusions et hashes ; conserver l'ancien gate.
- [ ] Examiner les séquences autour des annotations, pas seulement les 40 points :
  rampes, grandes erreurs, trous, minima. Si des vérités supplémentaires sont utiles,
  préparer une revue indépendante et l'attribuer correctement, sans labels issus de
  la sortie du modèle. Ne pas chercher des annotations qui feraient passer le gate.
- [ ] Rejouer progression/calibration/repères car l'entrée vitesse a changé. Aucun
  recalage des seuils de `s` pour masquer une régression ; pas de conversion en mètres.
- [ ] Documenter séparément la validité HUD/vitesse. Définir sur développement un
  contrat visible/absent/inconnu et une preuve de validité (revue indépendante ou
  détecteur évalué). Tester avant implémentation : menu, ROI noire, texte numérique
  hors HUD, retour au HUD. Absent/inconnu ne doit pas être une mesure de coaching
  validée. Ne pas ajouter une règle copiée des six erreurs du holdout pour les cacher.
- [ ] Conserver la correction OCR historique comme chantier A distinct : reproduire
  les lectures 0→7 et 2/3→20/30, inspecter crop et traitement avant de choisir un moteur.
  Un comparatif OCR n'est ouvert que si le développement l'exige ; il est gelé avant
  tout test indépendant. Ne pas mélanger remplacement OCR et correction de médiane.
- [ ] Si l'un de ces chantiers dépasse cette tranche, le laisser explicitement en
  échec/not_evaluated avec un prochain test précis ; S2/S3 ne ferment pas Gate A.

## S5 — Publier une preuve compatible, sans recycler le holdout

- [ ] Vérifier source/annotations/reviewers immuables. Publier les six checks A7 pour
  le nouveau code ; aucun résultat A7 d'une ancienne empreinte n'est transféré.
- [ ] Le holdout run-008 est désormais connu. Après gel des corrections, un replay
  éventuel de celui-ci reste une régression historique ; ne pas réécrire sa réservation
  pour déclarer une compatibilité fictive ou une nouvelle indépendance.
- [ ] Pour une nouvelle acceptation indépendante, réserver une capture/enregistrement
  distinct avant inspection avec le nouveau code/config. Préparer le dossier précis
  seulement lorsque cette entrée devient nécessaire ; aucune demande de nouvelle
  vidéo n'est requise pendant la rédaction de ce plan.
- [ ] Garder les latences non annotées `not_evaluated`. E16 n'est pas un onset à 5%,
  les relâchements génériques ne sont pas des passages sous 5%, les candidats voisins
  non annotés ne sont pas automatiquement des faux positifs.
- [ ] Ne déclarer Gate A passé que si tous les contrôles nécessaires passent avec
  preuve compatible. Aucun B tant qu'un contrôle échoue ou manque.
- [ ] Synchroniser handoff, résultats et cases, vérifier, committer puis pousser sur
  la branche autorisée. Aucun merge vers main.

## R — Régression locale de vitesse : différée, hors tranche active

**Ne pas commencer R pendant que le gate A prerequisite est en échec.** Ce n'est pas
une condition pour livrer la correction des mesures fraîches. L'absence de régression
est une décision valide. Si un besoin subsiste après A :

- [ ] Définir avant expérimentation les critères d'amélioration et de non-déplacement
  temporel ; constituer vérité développement pour minima/ruptures si elle manque.
- [ ] Comparer aucun lissage et régression locale robuste hors ligne ; paramètres en
  secondes, support minimal et comportement aux bords configurés/validés.
- [ ] Tester rampe linéaire, valeurs aberrantes isolées, minimum, rupture de pente,
  bord de capture, trou et changement de tour. Pas d'extrapolation ni de pont sur absence.
- [ ] Publier une série estimée séparée avec qualité/support temporel et usage futur
  des points explicités. Aucune substitution à la vitesse mesurée, aux événements,
  aux pédales ou à l'odométrie. L'intégration UI/contrat d'export nécessitera une
  tranche dédiée après décision, pas une extension implicite de ce plan.
- [ ] Retenir la méthode seulement si l'amélioration mesurée est démontrée sans
  dégradation temporelle ; sinon conserver les lectures fraîches sans cette courbe.

## Vérification avant chaque commit

Tests ciblés pertinents, puis :

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
./scripts/docs-list
git diff --check
git status --short --branch
```

Enregistrer les logs dans le nouveau run ignoré. Committer uniquement les fichiers
cohérents de code/tests/config/docs, jamais les vidéos, assets OCR ou rapports générés.
La préparation de ce plan reçoit un commit **documentation uniquement** ; toutes
les cases d'implémentation restent ouvertes jusqu'à leur exécution réelle.
