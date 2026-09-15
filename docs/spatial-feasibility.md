---
summary: run-034 spatial feasibility and first local appearance-model training; dense labels and metric geometry still missing
read_when:
  - preparing spatial segmentation labels or a model experiment
  - interpreting run-034 image coordinates, model scores and missing metric positions
---

# Faisabilité spatiale — premier essai entraîné

Run-034 explore six images natives des trois passages des Combes de run-026, avec
contexte de commandes provenant de la base run-033. Aucun nouveau décodage vidéo/OCR,
modification des données de conduite ou entraînement cloud.

Un modèle d'apparence a réellement été ajusté : régression logistique couleur Lab et
texture locale,20 carrés annotés sur deux images P1 pour apprendre ;35 carrés P2/P3 sur
quatre images séparées pour essayer. Labels visuels provisoires par modèle ; deux zones
ambiguës exclues avant ajustement. Pas de recherche de paramètres, ni de répartition
aléatoire mélangeant les frames voisines. Une seule capture : pas de test indépendant
sur une autre session, et encore moins de preuve de transfert PC→PS5.

| Résultat d'essai | Règle couleur | Modèle |
|---|---:|---:|
| Corrects sur35 carrés |25|28|
| Rappel piste |11/11|9/11|
| Rejet hors-piste |14/24|19/24|
| Moyenne des deux rappels |79,2 %|80,5 %|

Le gain est limité ; le modèle confond encore piste, dégagement et barrières et manque
les deux points de piste dans l'image d'excursion. Il ne possède pas le contexte requis.
Ce diagnostic ne qualifie ni un masque dense ni un réseau plus puissant non essayé.
Les pixels des patches ne sont pas autant de scènes indépendantes.

## Données livrées et limites

Sous `data/lab/coaching-reliability/run-034/` (ignoré) :

- `processed/appearance-model.npz` : poids, moyenne et échelle appris localement.
- `interim/labels.json` : images/empreintes,55 patches, partition, paramètres figés.
- `reports/model-results.json` : matrice de confusion, labels/prédictions et scores
  non calibrés en confiance. IoU dense/erreur de bord/erreur métrique restent null.
- `processed/spatial-observations.json` : propositions de contours à y=600, intervalles
  visuels provisoires, occultations/nulls, provenance et contexte de commandes run-033.
- `reports/results.md` : analyse, visualisations et commandes locales de reproduction.

Canny produit8–19 contours candidats par image sur la ligne examinée, sans savoir
choisir le bord de piste. Une proximité avec une référence choisie manuellement n'est
pas un détecteur de bord évalué. Les deux approches restent expérimentales.

La ligne d'image n'est pas une section géométrique commune. Ni le centre de l'image
ni le HUD steering ne fournissent la pose physique de la voiture. Caméra, point de
contact et géométrie métrique manquent : `s_m`, `d_m`, orientation et position voiture
restent null. Les repères A/B hérités ne sont pas une calibration métrique.

## Décision de méthode

Préparer des masques piste/vibreur/dégagement/cockpit et des bords visibles/occultés,
puis évaluer un modèle de segmentation préentraîné avant une adaptation spécialisée.
SAM2 constitue une piste pour l'annotation assistée/propagation et fournit du code
d'adaptation sur images/vidéos ; ce n'est pas un modèle ACC déjà validé ni un choix
matériel arrêté. [Documentation officielle](https://github.com/facebookresearch/sam2/blob/main/training/README.md).

Pour les mètres, il faut une validation géométrique distincte. Depth Anything V2
sépare modèles relatifs et modèles ajustés avec labels métriques ; leur existence ne
qualifie pas la géométrie de notre capture. [Projet officiel](https://github.com/DepthAnything/Depth-Anything-V2).

Tout run-034 est désormais du développement. Réserver une autre capture pour le test
indépendant futur. Critères utiles : erreur de bord visible en pixels, confusion avec
le dégagement, couverture/abstention et stabilité temporelle ; erreur en mètres seulement
lorsque la vérité géométrique est disponible. Voir le [plan unique](plans/video-to-agent-platform.md).
