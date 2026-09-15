---
summary: single active plan - extract and qualify video driving data first, then expose a persistent session platform to AI agents
read_when:
  - choosing the next implementation increment or deciding whether platform work is premature
  - building video-derived measurements, trajectory or later agent navigation
---

# Plan actif — vidéo vers plateforme de données pour agents

**Décision du15 septembre2026 : l'objectif final est une plateforme facilement
navigable par un agent pour explorer les données de conduite. La priorité de réalisation
est d'abord de récupérer et qualifier les données depuis la vidéo.** Le PDF est un
ancien export, pas la cible produit. Le serveur MCP et les skills viennent ensuite.

Un agent doit pouvoir partir d'une synthèse de séance, comparer les passages et une
référence, trouver des récurrences et consulter les preuves nécessaires. Notre logiciel
fournit faits, calculs et inconnus ; l'IA discute causes et entraînement.

[Passation](../current-status.md) · [Audit du code](../video-data-audit.md) ·
[Catalogue des72 entrées](../driving-metrics.md) · [Architecture](../architecture.md).
Un seul plan actif ; les anciens jalons M1–M5 sont réorganisés ici, leurs preuves restent
consultables dans les runs et Git.

## 1. Acquisition vidéo — travail actif

### 1A. Consolider le socle et commencer par un calcul simple

- [x] Auditer le chemin CLI/web partagé et les72 entrées, avec les vrais artefacts.
- [x] Distinguer signaux présents, calculs manquants et grandeurs non observables.
- [x] À partir de run-024, apparier les candidats frein/gaz en épisodes temporels :
  début, confirmation, fin, troncature, lacunes et qualité. Réutiliser l'index existant.
- [x] Premier incrément durée, pic/temps au pic, queue dernier maximum→fin,
  reprise/coupure entre épisodes et chevauchement candidat livré en run-029.
  Pente moyenne en points HUD/s ; ni pression ni énergie physique.
- [ ] Qualifier la précision temporelle des épisodes : début réel du relâchement,
  paliers/modulations internes et plein gaz calibré restent hors du premier incrément.
- [ ] Corriger les agrégats hérités uniquement lorsqu'ils sont utilisés : absence de
  vitesse ne doit pas produire0 ; compteur de numéros ≠ nombre de tours complets.
- [x] Vérifier les résultats sur quelques fenêtres déjà annotées. Aucun replay OCR
  nécessaire pour les calculs aval ; pas de nouvelle campagne de seuils.

**Livraison run-029 :** [contrat, résultats et commande](../control-episodes.md).
91 épisodes candidats,89 bornés ; annotations ponctuelles réutilisées, aucune précision
temporelle continue démontrée. Agrégats hérités non utilisés, donc non modifiés.

**Sortie :** données structurées locales reproductibles, reliées aux frames. `null` et
raisons persistent, aucune visibilité inventée ni pédale lissée. Les positions de
freinage en mètres et la cause d'un incident restent inconnues à ce stade.

### 1B. Étendre les champs effectivement visibles

- [ ] Inventorier sur la capture cible les informations réellement affichées : régime,
  chrono, réglages aides, carburant, pressions, avertissements et contexte.
- [ ] Ajouter les lecteurs utiles avec unités, calendrier de rafraîchissement et
  calibration adaptés. Vérifier les changements/absences, pas seulement un chiffre fixe.
- [ ] Qualifier le candidat `steering` avant tout usage : un point dans le HUD ou
  l'animation cockpit ne constitue pas un angle physique des roues.
- [ ] Distinguer réglages TC/ABS et interventions. Les sorties actuelles restent
  indisponibles tant que leur signification n'est pas établie.

Ne pas promettre un champ parce qu'il existe dans un logger PC : la vidéo doit porter
l'information ou permettre une estimation testée. Traiter aussi les passages imparfaits,
les cas ordinaires et les anomalies ; ne pas apprendre uniquement sur de beaux tours.

### 1C. Construire la représentation spatiale

- [ ] Définir géométrie/bords de piste et point de voiture mesuré ; `s_norm` actuel
  entre0 et1 est distinct du futur `s_m` et de `d_m`.
- [ ] Évaluer une estimation de placement/orientation depuis images et séquences,
  avec précision et inconnus. La minimap seule ne constitue pas une trajectoire métrique.
- [ ] Préparer une courte capture PC vidéo+télémétrie synchronisées si nécessaire aux
  labels : position, orientation/vitesses, géométrie et temps réellement vérifiés.
- [ ] Définir l'erreur utile à distinguer avant l'entraînement ; séparer les sessions
  d'apprentissage/test. Évaluer explicitement le transfert PC→PS5.
- [ ] Conserver qualité et abstentions sur excursions, ambiguïtés ou caméra différente.
  Ne pas dessiner une ligne précise lorsque les données ne la soutiennent pas.

L'environnement ACC sur Mac et sa durée disponible restent inconnus. Ne pas consommer
un créneau limité pour découvrir le logger. Aucune collecte PC ni entraînement lancé.
Cette collecte sert d'abord la perception vidéo ; l'acquisition directe PC future
pourra réutiliser nos contrats normalisés.

### 1D. Compléter les métriques et les références

- [ ] Fixer zones/repères comparables entre tours ; les14 zones de run-027 sont des
  fenêtres de navigation manuelles pour un seul tour, pas un découpage automatique général.
- [ ] Calculer les métriques du catalogue quand leurs entrées deviennent admissibles,
  avec version, sources, unités, incertitude et statut de disponibilité par champ.
- [ ] Acquérir une référence de conduite documentée et reproductible, distincte de la
  géométrie de piste. Le meilleur tour personnel isolé n'est pas la cible par défaut.
- [ ] Conserver difficulté répétée, variabilité et écarts à la référence séparément.
  Sans comparateur adéquat, ne pas annoncer des secondes récupérables.

**Condition de fin de la phase données :** l'inventaire du périmètre vidéo retenu
indique pour chaque donnée utile une extraction mesurée, une estimation évaluée ou
une impossibilité documentée. Les métriques choisies sont reproductibles et leurs
limites connues. Les grandeurs cachées (forces, charges, pression réelle, etc.) peuvent
exiger un autre capteur : elles ne doivent ni être inventées ni bloquer indéfiniment
la plateforme sous la promesse impossible de72 métriques parfaites depuis des pixels.

## 2. Plateforme de séances — phase suivante

Cette architecture guide le stockage actuel, mais sa construction n'est pas le prochain
chantier. Réutiliser telemetry-v2 et des dérivés locaux pendant la phase1.

- Stockage indépendant du protocole : sources immuables, mesures, trajectoires,
  passages, références et résultats dérivés versionnés, liens aux preuves.
- Contrat commun pour vidéo et futur PC, avec provenance `lecture`, `direct` ou
  `estimation`, unités/horloges/qualité explicites ; aucune promotion rétroactive des données.
- Couche applicative commune : comparaison, récurrences, qualité et accès borné aux
  preuves. Interfaces humaines et MCP délèguent aux mêmes services.
- MCP prévu : résumer une séance, comparer des passages, rechercher des récurrences,
  expliquer une métrique et récupérer une preuve. Skills éventuels pour guider
  l'investigation et la recherche de contre-exemples, séparés des données factuelles.
- Aucun SDK, base de données, interface web ou hébergement à développer maintenant.
  La vidéo est une entrée du pipeline et une preuve ciblée, pas un flux à lire en entier
  par le modèle de coaching.

## 3. Navigation et analyse par l'agent — après le socle

L'agent doit identifier les difficultés récurrentes de toute la séance avec un coût
borné, puis approfondir. Synthèse globale de toutes les zones, quelques cas dominants,
occurrences et contre-exemples ; pas une sélection limitée aux incidents spectaculaires.

Le budget initial de4 000 tokens, six graphes et24 images pour environ20 min est une
hypothèse de produit à mesurer, pas un contrat matériel acquis. Les requêtes d'un agent
peuvent approfondir sous un budget global annoncé. Ne pas rendre le visionnage de toute
la vidéo nécessaire pour compenser une synthèse insuffisante.

**Acceptation future :** retrouver les récurrences, citer les preuves réellement lues,
reconnaître les inconnus, comparer équitablement et ne pas compter deux fois les pertes.
Évaluer les omissions et le coût de lecture ; puis l'utilité réelle du coaching sur
plusieurs séances. La scène, le geste et la conséquence restent reliés.

## Preuves déjà obtenues et limites persistantes

- run-024 : extraction automatique complète native1080p60 et artefacts réutilisables.
- run-026 : export expérimental `session_coaching.md` sur trois passages revus.
- run-027 : lecteur d'un tour complet, index candidat et détail temporel.
- run-028 : PDF17 pages/18 s et retour externe cohérent localement ; ne prouve pas la
  condensation globale. Ajouter un clip n'est plus la prochaine action.
- Gate A reste FAIL, `coaching_eligible=false` ; aucune qualification spatiale ou
  causale générale. Vérités compteur run-021/run-022 réutilisées, pas de revue exhaustive.

**Prochaine action exacte : préparer une petite vérité temporelle définie sur B2 et
une fenêtre gaz existante pour qualifier les descripteurs run-029. Distinguer mouvement
visible et franchissement des seuils ; pas de campagne de seuils. La plateforme et la
navigation de l'agent viennent après les données.**
