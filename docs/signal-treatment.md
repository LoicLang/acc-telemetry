---
summary: approved signal-treatment direction separating fresh measurements, invalid readings and optional speed regression
read_when:
  - correcting speed filtering after A7 or changing pedal signal processing
  - designing smoothing, HUD validity or downstream use of estimated signals
---

# Traitement des signaux après A7

**Décision du 9 septembre 2026, issue de la discussion avec le propriétaire.**
Ce document spécifie la correction à réaliser ; il ne décrit pas une correction
livrée. Le code conserve actuellement la médiane/reprise historique dans
`LapDetector.observe_speed()`. Gate A reste en échec. Plan d'exécution :
[2026-09-09-fresh-measurements.md](plans/2026-09-09-fresh-measurements.md).
La spécification générale de coaching du 5 septembre reste la référence produit.

## Pourquoi changer

A7 a mesuré des erreurs sur la vitesse publiée. Une inspection supplémentaire des
artefacts de développement distingue désormais la lecture OCR de son traitement :
**19/19 lectures BMW et 21/21 lectures du clip avec incidents correspondent exactement
aux annotations de vitesse**, avant le filtre. Ce constat porte sur ces 40 images
sélectionnées ; il ne prouve pas l'exactitude de chaque image des captures.

Exemples BMW : visible 246, OCR « 246 », sortie 255 ; visible 179, OCR « 179 », sortie
188. Exemple incidents : visible 145, OCR « 145 », sortie 149. Les raisons exportées
indiquent `speed_median_filtered`. La médiane traînante introduit ici du retard et
sa sortie porte pourtant `observed`. Les autres erreurs hors de ces points et la
meilleure méthode de rejet des valeurs aberrantes restent à diagnostiquer.

Preuve locale, sans relancer l'OCR ni analyser le holdout :
`data/lab/coaching-reliability/run-009/reports/speed-raw-vs-output.json`.
Ce fichier référence les labels et observations run-008 avec leurs SHA-256.
Le gate A7 d'origine reste inchangé et fait autorité pour son ancienne empreinte.

## Contrat cible

| Signal | Mesure publiée | Traitement autorisé |
| --- | --- | --- |
| Vitesse | Lecture numérique fraîche de cette image, validée, horodatée à cette image | Rejeter/signaler une lecture invalide ; ne pas la remplacer silencieusement par une médiane ou une prédiction |
| Frein / gaz | Lecture fraîche de la barre visible, avec sa qualité | Préserver reprises à 100%, attaques de frein, dégressivité, interruptions et blips visibles |
| HUD absent ou lecture inexploitable | Valeur absente et raison explicite, texte brut conservé si disponible | Aucun zéro fabriqué, maintien déguisé ou interpolation à travers l'absence |
| Courbe de vitesse estimée, éventuelle | Série distincte, explicitement estimée | Régression locale robuste, seulement si son utilité est démontrée ; jamais substituée aux mesures |

`raw_value` / `speed_raw` gardent le texte réellement lu, même rejeté. `speed_kmh`
et le record moderne `speed` représentent la même mesure fraîche validée. Une valeur
numérique plausible n'est pas une preuve de présence du HUD. `observed` signifie une
lecture fraîche admise, pas une probabilité d'exactitude.

Les artefacts historiques HELD restent lisibles et conservent HELD. Le nouveau chemin
moderne ne crée pas de mesure fraîche à partir d'un maintien. Les wrappers explicitement
legacy peuvent garder leurs comportements historiques ; leur périmètre doit rester
identifiable et ne doit pas contaminer le chemin générique CLI/web.

Un outlier peut être rejeté avec sa raison, mais un saut ne doit pas être éliminé
simplement parce qu'il est abrupt : c'est particulièrement important pour les pédales.
Les règles physiques de vitesse doivent considérer le temps réel entre observations,
les absences et les changements de contexte ; leurs limites sont configurées et
validées sur le développement. Aucune borne arbitraire n'est ajoutée pour verdir A7.

## Pédales : conserver les transitions

Aucun lissage, moyenne mobile, médiane ou régression n'est ajouté au frein ou aux gaz.
Les états observés 0 puis 100 restent 0 puis 100 aux mêmes frames. Un relâchement
progressif conserve ses paliers ; une brève interruption et un blip ne sont pas
supprimés automatiquement comme du bruit. Une lecture réellement douteuse garde une
qualité/raison explicite, distincte d'une variation rapide mais lisible.

Cette décision ne supprime pas les règles existantes de visibilité ou les limites
du décodeur de barres. Elle ne transforme pas non plus les indicateurs TC/ABS en
mesures validées. Les événements de coaching soutenus B4 restent hors périmètre.

## Régression de vitesse : option différée

Une régression est aussi un filtre. Elle pourrait suivre une décélération mieux qu'une
médiane traînante ; son avantage réel sur nos données reste une **hypothèse**.
Ne pas l'implémenter pour réparer d'abord la mesure fraîche, ni pour obtenir un gate
vert. Ne pas créer maintenant de champ public ou de dépendance supplémentaire.

Si un besoin d'affichage subsiste après les corrections et le gate, une étude séparée
comparera l'absence de lissage avec une régression locale robuste de faible degré.
En analyse hors ligne, des points avant/après peuvent être utilisés ; cette dépendance
au futur doit être annoncée, sans présenter l'estimation comme disponible en direct.

L'étude devra figer sur développement : fenêtre en secondes, nombre minimal de points,
limite de trou, degré, mécanisme robuste et traitement des bords. Elle devra :

- séparer les runs avant tout ajustement : HUD absent, valeurs invalides, frontières
  de tours, changements de contexte et trous excessifs ;
- s'abstenir aux bords sans support suffisant, sans extrapolation ni remplissage des
  trous ; publier provenance, support temporel, méthode et statut estimé ;
- comparer erreurs, décalage temporel, minima et dépassements, pas seulement l'aspect
  visuel ; ne pas choisir les réglages sur le holdout ;
- garder la série mesurée intacte. Validation A7, événements, comparaisons et odométrie
  ne basculent pas implicitement sur cette courbe. Tout usage analytique ultérieur
  exige son propre contrat et sa validation.

L'absence de régression reste une issue acceptable. Les seuils d'acceptation de cette
option ne sont pas encore définis ; aucune précision chiffrée n'est promise.

## Architecture, évaluation et limites

L'extraction lit une fois le champ. La validation/rejet et la normalisation conservent
valeur, texte brut, raisons et temps. Le pipeline partagé transmet le même signal aux
artefacts, à la CLI, au web et à la progression. Une éventuelle estimation se calcule
en aval dans une analyse pure et dispose d'un contrat distinct, sans dépendance de
`domain`/`normalization` vers OpenCV, Plotly ou FastAPI.

Changer la vitesse fournie à l'odométrie peut modifier la calibration et `s`. Ce risque
exige de rejouer les contrôles de progression avec de nouveaux artefacts et empreintes ;
les anciennes preuves ne deviennent pas compatibles par simple mise à jour du hash.

La correction de vitesse ne résout pas à elle seule l'OCR des tours historiques,
la validité HUD/vitesse ou les preuves de latence manquantes. Ces blocages restent
séparés dans A. Un comparatif OCR ne sera ouvert que si les lectures brutes de
**développement** le justifient ; aucun remplacement de moteur n'est décidé ici.

Les annotations A6, les revues distinctes d'A7, E16 et les exclusions temporelles
restent intactes. Les six repères permettent une dispersion de `s`, jamais une erreur
en mètres. Les seuils A7 ne changent pas. Le holdout run-008, déjà inspecté, est gelé :
il peut servir de régression historique après gel d'une correction, jamais de terrain
de réglage ni être présenté comme un nouveau test vierge. Une nouvelle preuve
indépendante exige une réservation avant inspection, compatible avec le nouveau code.
Tous les contrôles nécessaires doivent passer avant B ; une preuve absente reste
`not_evaluated`. Ce plan de documentation ne rouvre aucune validation humaine acquise.
