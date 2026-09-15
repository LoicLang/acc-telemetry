# Archives — preuves, pas instructions

Ces documents sont conservés pour leurs résultats, approbations, limites ou détails
de conception. **Leurs anciens plans, gates de livraison et prochaines actions ne
font pas autorité.** Commencer par [current-status](../current-status.md) et suivre
[le seul plan actif](../plans/video-to-agent-platform.md).

Le13 septembre2026, le propriétaire a adopté le premier export expérimental
`session_coaching.md` et demandé la suppression des documents obsolètes. Les anciens
plans/instructions remplacés ont été supprimés ; leur contenu reste dans Git avant
ce nettoyage (`55f32cc`). Les preuves uniques restent ici, hors découverte normale.
Aucune vidéo, annotation acceptée ou télémétrie n'a été supprimée ou modifiée.

## Preuves à consulter seulement pour une question historique précise

- [Compteur incidents complet](reliability/incidents-counter-results.md) — vérité run-022 réutilisable.
- [Compteur BMW complet](reliability/exact-counter-state-review.md) — revue run-021 réutilisable.
- [Validation générale A7](reliability/capture-validation-results.md) — résultats de l'ancien fingerprint, pas nouveau gate.
- [Annotations et approbations](reliability/capture-annotations-history.md) — portée, auteurs, lineage et corpus A6.
- [Contraintes de reprise A6/A7](reliability/coaching-reliability-resume.md) — sémantiques conservées, pas ordre de travail actuel.
- [Corrections d'admission](reliability/admission-correction-results.md) et [mesures fraîches](reliability/fresh-measurement-results.md).
- [Visibilité des segments](reliability/speed-visibility-results.md) et [calibration BMW](reliability/calibration-lap-results.md).
- [Ancien dossier compteur](reliability/lap-counter-dossier.md), [échecs de revue](reliability/counter-review-recovery.md), [essai borné](reliability/astra-review-trial.md).
- [Essai run-023](reliability/real-system-trial-results.md) — montre les trous de l'ancien mode et le défaut d'aplats corrigé.
- [Audit technique initial](reliability/technical-audit-2026-09-05.md).
- [Audit de préparation GPT](reliability/gpt-coaching-readiness-audit.md) et [essai manuel de lecture](reliability/gpt-coaching-report-trial.md) — limites utiles, ancien seuil de dossier complet remplacé.
- [Ancienne passation complète](2026-09-13-handoff-before-export.md) — historique des runs, non applicable comme instruction de reprise.

## Conception du code déjà présent

- [Fusion de progression générique](design/2026-09-03-generic-s-fusion-design.md).
- [Ancres visuelles aux bornes de tour](design/2026-09-05-generic-boundary-visual-anchor-design.md).

Ces designs ne demandent pas de nouvelle implémentation. La documentation opérationnelle
est [architecture](../architecture.md). Les anciens diagnostics du prototype conservés
pour leur preuve sont listés dans [legacy](../legacy/README.md).

## Nettoyage du15 septembre2026

Le cadrage produit est consolidé dans README et le plan unique. Les deux anciennes
synthèses `product-context` / `acc-ps5-plan`, les consignes d'agent archivées et la
copie de l'ancien main ont été supprimées ; historique consultable dans Git. Les
preuves de mesure et diagnostics uniques ci-dessus restent conservés. Les contrats
des exporteurs encore présents dans le code ne sont pas des plans de réalisation.
