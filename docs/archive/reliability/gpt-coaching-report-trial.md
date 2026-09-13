---
summary: actual manual coaching attempt from run-024 exposing missing approach context, car identity, aligned passages and an admitted driver reference
read_when:
  - assessing whether the current report supports a specific coaching recommendation
  - choosing the next report improvement from observed information gaps
---

> Historical evidence only — archived13 September2026. Old instructions, gates and next actions below are not current. Follow [current status](../../current-status.md).

# Test réel du rapport comme entrée de coaching

Le12 septembre2026, le propriétaire a demandé au modèle de tenter le coaching avec
le rapport existant, et de juger le rapport sur sa capacité à comprendre une faiblesse
et proposer sa correction. Ce test complète l'audit/plan : les livrables techniques
ne suffisent pas si le lecteur ne peut pas produire un débrief étayé.

**Verdict : run-024 est utile pour observer, insuffisant pour un coaching spécifique
complet et validé.** Gate A reste en échec. Aucun générateur B ou mécanisme de coaching
a été implémenté. Il s'agit d'une analyse manuelle explicitement demandée, dans la
conversation courante ; ce n'est pas un test aveugle indépendant dans un nouveau chat.

## Matériel et méthode

1. Lire le texte/tableaux du rapport run-024 et ses preuves accessibles.
2. Tenter le débrief en séparant observations, hypothèses et conclusions interdites.
3. Identifier la pièce manquante à chaque blocage ; consulter un complément source
   limité si celui-ci permet d'expliquer comment améliorer le dossier.
4. Conserver le rapport initial et les annotations : ne pas présenter l'enrichissement
   comme une capacité déjà présente dans run-024.

Preuve locale : `data/lab/coaching-reliability/run-025/reports/essai-gpt/ESSAI_COACHING.md`,
`preuves.json`, `points-contexte.csv` et trois illustrations. Le paquet de travail est
marqué diagnostic provisoire, pas dossier ready. L'audit de planification vérifie les
artefacts run-024 et ne change aucune mesure ou annotation acceptée.

## Débrief possible et limites

- Le freinage187–190s montre une attaque/palier puis une dégressivité. Vitesse contrôlée
  260/191/120km/h à187/188,5/190s. Aucun fondement pour affirmer une absence de défreinage.
- L'incident montre une sortie de piste puis une rotation ;103/89/38km/h contrôlés
  à348/349/350s. Priorité provisoire : obtenir des sorties propres et reproductibles
  de la dernière droite des Combes, avant de rechercher davantage de vitesse.
- Une reprise des gaz après la sortie de piste ne prouve pas la cause initiale. Les
  blips près des rétrogradages ne prouvent pas non plus une mauvaise action volontaire.
- Exercice proposé comme test prudent : même repère d'approche, marge de vitesse,
  préparation de la dernière droite, reprise progressive compatible avec la sortie,
  trois passages sans graviers/perte de contrôle. Comparer ensuite les mêmes repères.
  Aucune vitesse idéale, mètre de freinage, réglage TC/ABS ou gain promis.

## Ce qui a réellement changé l'analyse

L'extrait d'incident347–352s commence déjà dans les graviers. Il montre principalement
les conséquences/récupération. Huit images de336 à349s, après vérification source et
1080p60CFR, ajoutent l'approche et les changements de direction. Aucun nouvel OCR,
aucune campagne exhaustive et aucun ajout aux ledgers d'annotations.

La séquence est identifiée visuellement comme la fin des Combes/Malmedy, avant
Bruxelles ; ses limites physiques exactes restent à annoter. Le cockpit porte McLaren
720S GT3 ; original/EVO reste inconnu.62,0L est visible à349s, pas nécessairement au
point de départ. Le matériel de pilotage et le contexte initial manquent au rapport.
Le cas BMW/Bruxelles proposé historiquement ne doit pas être imposé à cette vidéo.

À344s, la source affiche145km/h, troisième, gaz proches du plein ; à346–347s, la voiture
quitte la trajectoire de sortie. C'est une piste pour examiner placement/reprise,
**pas une causalité établie**. Les passages réussis au même repère et une référence
qualifiée restent nécessaires. Le rapport actuel ne prouve pas un défaut répétitif.

## Référence pédagogique et référence numérique

Un [guide explicatif de Spa](https://coachdaveacademy.com/tutorials/circuit-de-spa-francorchamps-track-guide/)
et une [publication McLaren/Spa de Nils Naujoks](https://popometer.io/acc/setups/1125)
ont été consultés. Ils sont des candidats pédagogiques ; le second concerne1.9.0 en2023.
Aucun média/télémétrie du pack n'est acquis, aucune compatibilité quantitative ou
résolution/cadence native n'est prouvée. Ne pas fixer une cible à partir de ce chrono.
Une vidéo publique de coaching ancienne a été repérée mais son contenu n'a pas pu
être ouvert par l'outil de lecture ; aucun visionnage ni recommandation de son contenu
n'est revendiqué.

Les croix noires du rapport sont des contrôles d'extraction, jamais une référence de
conduite. Le futur dossier doit employer ces deux termes distinctement.

## Critère de sortie et révision du plan

Le dossier ne sera complet pour ce cas que s'il permet de relier une faiblesse aux
preuves, de la comparer à des passages pertinents, de discuter ses causes alternatives,
de proposer une correction praticable et de vérifier son effet. Aucune simple check-list
de fichiers ne remplace ce test. Répéter la lecture critique à chaque amélioration,
avec une nouvelle pièce précise par blocage ; aucune boucle de commentaires génériques.

Prochaine préparation : confirmer contexte McLaren/variante/matériel, retenir la zone
observée, aligner les passages personnels et qualifier une référence expliquée. Ce
travail de sélection/revue et l'essai manuel sont permis pendant A ; l'implémentation
B et sa présentation comme coaching validé attendent toujours le gate compatible.
Le plan local du12 septembre intègre désormais cette boucle comme critère central.
