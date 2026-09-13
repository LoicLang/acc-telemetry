---
summary: verified run-024 automatic extraction baseline and concrete evidence limitations for the first export
read_when:
  - reusing run-024 without rerunning extraction
  - assessing available data and the scope of existing annotations
---

# Run-024 — point de départ existant

La vidéo incidents a été intégralement traitée par la vraie CLI et `TelemetryPipeline`,
en `measurement_mode=automatic`, sans annotation d'entrée. Aucun nouveau traitement
n'est nécessaire pour commencer le premier export. Le mode reviewed reste le défaut.

Artefacts : `data/lab/coaching-reliability/run-024/processed/crash-session/`.
Mesures : `run-024/reports/results.json`, `annotated-validation.json`,
`final-verification.json`. Rapports et scripts expérimentaux restent locaux/ignorés.
`read_session_artifacts()` vérifie le manifeste, les hashes et les enveloppes avant usage.

Source du manifeste : `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`,
SHA-256 `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`,453613415 bytes.
Format natif 1920×1080 exactement 60 fps CFR ;29402 images présentées,490.033s. Décodage et
PTS alignés. Le compteur conteneur29416 inclut14 paquets discard ; ne pas l'utiliser
comme dénominateur des images. Temps relatifs à ce clip d'entrée.

| Champ | Disponible /29402 | Signification |
| --- | --- | --- |
| Vitesse |29298|99.65% d'extraction, pas d'exactitude générale |
| Frein/gaz |29402 chacun|Visibilité toujours non vérifiée hors revue locale |
| Compteur brut |29402|Toutes les lectures fraîches exactes face à run-022 |
| Rapport engagé |28913|Exactitude générale non qualifiée |
| Direction |29232|Exactitude non testée, pas de conseil sur angle volant |
| `s` fusionné |26844|Estimation disponible, précision spatiale inconnue |
| TC/ABS |0|Non supportés |

Les 104 vitesses absentes gardent les raisons :95 OCR vides,5 refus de variation,
3 hors plage,1 texte invalide. Les 29402 textes OCR sont identiques à run-023 ; aucun
lissage/maintien n'a été ajouté. Les 1366 valeurs de pédales des anciens points/plages
revus sont inchangées. L'interpolation d'odométrie est distincte de la mesure.

Contrôles a posteriori : vitesse exacte21/21 ; pédales sur 21 points chacune,
MAE frein/gaz1.60/3.12, P95 5.62/5.88, maximum 5.88 points. Les 18 segments de visibilité
couvrent683 images :679 vitesses,683 valeurs par pédale ; V-CRASH-15 reste28/31.
Ces plages de visibilité ne sont pas une vérité numérique dense.

Le plein gaz autour de 94.12%, les petits résidus et le vrai39km/h rejeté après66→39
à l'impact restent des limites connues. Ne pas les interpréter comme erreurs du pilote.
Le compteur donne4 transitions exactes sans manque/extra ; confirmation66.7ms après le
premier chiffre, distincte du reset chronomètre et d'un franchissement physique.

L'essai manuel run-025 montre le manque de contexte du vieux clip d'incident : il débute
à347s, déjà hors piste. Des images336–349s donnent l'approche de la fin des Combes/Malmedy.
Le cockpit indique la famille McLaren 720S GT3 ; variante/hardware non confirmés.
Ce test est une analyse provisoire, pas le fichier généré ni une revue GPT indépendante.

**Gate A reste FAIL ; `coaching_eligible=false`.** Depuis la décision du 13 septembre,
ces limites ne bloquent pas tout export expérimental : utiliser seulement les faits
localement soutenus et leurs limites dans le [premier fichier](specs/2026-09-13-session-coaching-report.md).
La référence professionnelle et la validation indépendante complète ne sont pas ses
prérequis. [Current status](current-status.md) donne la seule prochaine action.
