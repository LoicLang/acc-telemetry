---
summary: code-backed audit of video extraction and all 72 catalogue entries, with current outputs and missing capabilities
read_when:
  - deciding which driving data the current code can actually produce
  - starting the next video extraction or downstream metric increment
  - distinguishing implemented code, manual evidence and unobservable physical channels
---

# Audit du code — données issues de vidéo

**15 septembre 2026**, code examiné à partir de `989492a`. Audit en lecture du moteur,
de ses consommateurs et de leurs tests ; relecture des artefacts run-024 avec le lecteur
vérifiant leurs empreintes. Aucun nouvel OCR. Le catalogue décrit la cible ; ce document
établit les capacités présentes. Gate A: FAIL, `coaching_eligible=false`.

## Mise à jour — incrément épisodes run-029

L'audit initial ci-dessous reste la photographie avant implémentation. Depuis,
[les épisodes HUD](control-episodes.md) apparient les181 candidats pédales existants :
91 épisodes, durée si bornée, pic observé/temps au pic, queue dernier maximum→fin,
relations coupure/reprise et intersections frein/gaz. B03 passe de C à P (durée seulement),
B04/B06 et A01/A04 sont étendus, A03/A06 passent de C à P pour ces seuls descripteurs.
B07/intégrales, plein gaz calibré, modulation interne, distances et précision temporelle
continue restent non livrés/non qualifiés. Valeurs/raisons inchangées, aucune nouvelle
extraction. Les agrégats hérités ne sont pas utilisés et n'ont pas été modifiés.

## Ce que nous produisons déjà

| Sortie | Preuve dans le code | Portée réelle |
|---|---|---|
| Frame, temps et format natif/CFR | [video.py](../src/acc_telemetry/extraction/video.py), [pipeline.py](../src/acc_telemetry/application/pipeline.py) | Horloge vidéo, pas latence physique certifiée du HUD. |
| Vitesse fraîche et brut OCR | `LapDetector.observe_speed`, `SpeedAdmission` | Valeur admise ou null ; raisons et lecture rejetée conservées. |
| Frein et gaz (%) | `TelemetryExtractor.observe_frame_telemetry` | Barres HUD ; pas pression hydraulique, pas lissage temporel. |
| Rapport de boîte | `LapDetector.observe_gear` | Lecture fraîche ; erreurs/absences possibles. |
| Compteur confirmé et transitions | [lap_state.py](../src/acc_telemetry/application/lap_state.py) | Confirmation du HUD ; pas certification des tours légaux ou du franchissement physique. |
| Progression estimée | [progress.py](../src/acc_telemetry/application/progress.py), [odometry.py](../src/acc_telemetry/application/odometry.py) | `s`/`s_fused` normalisés0–1 ; `track_position` en %. Aucune trajectoire latérale. |
| Candidat de direction HUD | [controls.py](../src/acc_telemetry/extraction/controls.py) | Position d'un point clair dans une ROI, entre−1 et1. Ce n'est pas une mesure d'angle du volant/roues. |
| Débuts/fins candidats frein/gaz et changements de rapport | [analysis/perception.py](../src/acc_telemetry/analysis/perception.py) | Hystérésis5/2 %, persistance0,1 s, ruptures explicites ; pas d'épisodes de pilotage qualifiés. |
| Couverture et intervalles manquants | `missing_intervals`, `summarize_lap` | Par champ et plage ; distingue données fraîches et indisponibles. |
| Mesures aux repères et durées encadrées | [session_summary.py](../src/acc_telemetry/analysis/session_summary.py) | Repères/images/lectures fournis par une fiche de revue manuelle ; pas détection automatique des repères. |
| Moyennes et maxima globaux/par numéro de tour | `InteractiveTelemetryVisualizer.generate_summary` | Statistiques descriptives anciennes ; pas métriques par freinage ou référence qualifiée. |
| Rééchantillonnage et delta comparatif | [alignment.py](../src/acc_telemetry/analysis/alignment.py) | Diagnostic borné sur progression normalisée ; dépend des origines confirmées et de la qualité de `s`. |
| Erreurs et précision face aux annotations | [validation.py](../src/acc_telemetry/analysis/validation.py), [capture_validation.py](../src/acc_telemetry/application/capture_validation.py) | MAE/P95, couverture, événements/latence ; vérité externe requise, pas auto-validation. |
| Artefacts et preuves visuelles | [session_artifacts.py](../src/acc_telemetry/application/session_artifacts.py), [application/perception.py](../src/acc_telemetry/application/perception.py) | Données versionnées et images/clips liés aux frames. Pas reconnaissance automatique de la scène. |

## Vérification concrète sur les artefacts existants

Source run-024, 29 402 samples, de0 à490,016667 s. Valeurs non nulles :

| Champ | Disponibles /29 402 | Observation |
|---|---|---|
| Vitesse | 29 298 | Min0, max262 km/h ; disponibilité ne prouve pas l'exactitude continue. |
| Frein | 29 402 | Max95,425 % lu ; pas une mesure de pression. |
| Gaz | 29 402 | Max94,771 % lu ; un seuil fixé à100 % serait inexploitable. |
| Rapport | 28 913 | 1–6,489 absences. |
| Compteur confirmé | 29 398 | Numéros3–7 ; cinq numéros distincts ne signifient pas cinq tours complets. |
| Chrono `lap_time_s` | 0 | Non alimenté par le chemin moderne de ce run. |
| Progression `s` | 26 844 | Fraction estimée0–1, précision métrique non établie. |
| Candidat `steering` | 29 232 | Nombreuses valeurs, aucune qualification d'angle physique. |
| TC / ABS actifs | 0 /0 | Explicitement manquants : `indicator_semantics_unverified`. |

Quatre transitions confirmées ; trois tours bornés (HUD4,5,6), durées146,10 /148,45 /
177,85 s entre confirmations. Leurs limites restent celles du compteur.

Les fonctions M1 existantes, appliquées en mémoire à ces mêmes samples, donnent316
candidats :44 débuts/44 fins de frein,46 coupures/46 reprises de gaz,135 changements de
rapport et1 état initial gaz actifs. **Ce ne sont pas316 actions du pilote validées.**
Aucun nouvel extracteur n'a été utilisé, aucune sortie source modifiée.

## Correspondance avec les72 entrées du catalogue

Légende : **P** = partie implémentée/diagnostique, pas entrée complète qualifiée ;
**C** = calcul aval absent, accessible en principe depuis les signaux actuels après
admission des fenêtres ; **N** = entrée essentielle non mesurée/qualifiée ;
**E** = calcul déjà produit dans son périmètre explicite. Les catégories ne sont pas
un pourcentage de maturité. Un signal récupérable n'est pas un diagnostic implémenté.

| ID | État | Ce que le code fait ; ce qui manque |
|---|---|---|
| T01 | P | Bornes compteur, durée de segment et intervalles manuels ; secteurs/tours légaux non reconnus. |
| T02 | P | Courbes vitesse vs `s_norm`, alignement diagnostique ; pas `s_m` qualifié/référence générale. |
| T03 | P | `common_time_delta` existe ; précision spatiale et référence comparable non garanties. |
| T04 | C | Différence de delta aux bornes à construire ; admission des zones/référence requise. |
| T05 | P | Vitesses aux frames manuellement revues ; pas détection automatique entrée/corde/sortie/minimum fiable. |
| T06 | C | Analyse de conséquence aval absente ; nécessite bornes comparables et référence. |
| T07 | N | Aucun tour théorique/reproductible ni gestion de référence. |
| P01 | P | Progression normalisée seulement ; pas `(s_m,d_m)` ni position monde mesurée. |
| P02 | N | `d` et référence de ligne absents. |
| P03 | N | Repères de scène manuels ; aucun placement métrique aux points de virage. |
| P04 | N | Bords physiques, dimensions/projection des roues et marges absents. |
| P05 | N | Largeur de piste effectivement utilisée non mesurée. |
| P06 | N | Courbure du trajet réel non mesurée ; la centerline de minimap n'est pas ce trajet. |
| P07 | N | Orientation du châssis par rapport à la piste absente. |
| P08 | P | Intégration vitesse×temps et longueur effective internes ; pas longueur d'une trajectoire monde mesurée. |
| B01 | P | Début candidat daté ; vitesse joignable, point en mètres/référence non qualifiés. |
| B02 | P | Fin candidate datée ; pas position physique qualifiée. |
| B03 | C | Débuts/fins disponibles ; appariement en épisodes, troncatures et distances non implémentés. |
| B04 | P | Max/moyenne du frein global/par numéro de tour ; pas par épisode ni temps au pic. |
| B05 | C | Profil brut disponible ; montée/calibration et erreur de pente à définir. |
| B06 | P | Courbe et candidats de fin ; pas segmentation du relâchement/paliers/réapplications. |
| B07 | C | Intégrale de commande non calculée ; aucune pression physique disponible. |
| B08 | N | Décélération physique absente ; différencier l'OCR sans validation serait fragile. |
| B09 | N | Frein présent, rotation/braquage physique non qualifiés. |
| B10 | N | Indicateurs modernes TC/ABS forcés à missing ; roues/blocages inconnus. |
| A01 | P | Reprise candidate persistante ; pas distinction sémantique blip/reprise volontaire durable. |
| A02 | C | Pas de détection du plein gaz calibrée ; lecture maximale actuelle inférieure à100 %. |
| A03 | C | Rampe/délais entre niveaux à calculer sans lisser la source. |
| A04 | P | Transitions candidates ; amplitudes/durées/groupement en réapplications absents. |
| A05 | C | Intersections frein/gaz inactifs non calculées ; absences/résidus à distinguer. |
| A06 | C | Chevauchement et délai signé non calculés ; synchronisation physique non qualifiée. |
| A07 | P | Moyenne/max gaz existants ; pas répartition d'états par phase/zone. |
| S01 | N | Candidat de point HUD ; ni angle réel ni réponse physique. |
| S02 | N | Anciennes statistiques de `steering` ne mesurent pas un angle calibré. |
| S03 | N | Pas de vitesse de braquage physique. |
| S04 | N | Pas de corrections reconnues ; le signal candidat ne suffit pas. |
| S05 | N | Débraquage physique non mesuré. |
| S06 | N | Moyenne absolue du candidat présente, intégrale angulaire qualifiée absente. |
| D01 | N | Accélérations physiques / G-G absents. |
| D02 | N | Accélération combinée/enveloppe d'adhérence absentes. |
| D03 | N | Lacet et réponse au volant absents. |
| D04 | N | Vitesses locales et dérive absentes. |
| D05 | N | Vitesses/glissements de roues absents. |
| D06 | N | Modèle de réponse et entrées physiques absents. |
| D07 | N | Jerk/oscillations dynamiques non qualifiés. |
| G01 | P | Rapport et transitions ; attribution aux phases dépend de repères encore manuels. |
| G02 | N | Régime et limiteur non extraits. |
| G03 | N | Commandes/rapport présents, réponse en poussée non mesurée. |
| G04 | N | Ni lacet ni roues pour établir les associations d'instabilité. |
| R01 | P | Moyennes par numéro de tour ; pas allure médiane de passages propres comparables. |
| R02 | P | Dispersion circulaire de `s` aux repères de validation ; pas régularité de conduite/trajectoire. |
| R03 | C | Candidats disponibles ; signatures/occurrences comparables/contre-exemples non regroupés. |
| R04 | N | Référence générale et biais récurrents non gérés. |
| R05 | N | Pas classement de pertes qualifiées sur zones disjointes. |
| R06 | N | Pas suivi contextualisé entre relais/séances. |
| R07 | N | Pas mesure d'effet des exercices. |
| I01 | N | Descriptions manuelles seulement ; pas détection automatique d'excursion/invalidation. |
| I02 | N | Descriptions d'incidents manuelles seulement ; pas détecteur/reconstruction automatique. |
| I03 | N | Pas trajectoires adverses ni classification du trafic. |
| C01 | N | Carburant non extrait. |
| C02 | N | Pressions pneus non extraites. |
| C03 | N | Températures pneus non extraites. |
| C04 | N | Usure/salissure non extraites. |
| C05 | N | Températures/pressions freins et bias non extraits. |
| C06 | N | Réglages aides non extraits ; interventions non qualifiées. |
| C07 | P | Contexte dans la fiche manuelle ; aucune reconnaissance générale voiture/piste/setup/météo. |
| C08 | N | Charges/suspension/hauteur de caisse non mesurées. |
| Q01 | P | Couverture et intervalles manquants calculés ; synthèse qualité multi-zones à assembler. |
| Q02 | P | CFR/frames/temps contrôlés ; pas mesure complète de latence HUD ou vidéo/télémétrie PC. |
| Q03 | E | MAE/P95/couverture et correspondances d'événements face aux annotations ; portée de revue explicite. |
| Q04 | P | Incertitude interne et dispersion de progression ; aucune erreur métrique de d/trajectoire. |
| Q05 | P | Counts, raisons, fiche/contexte et gates ; pas moteur général de comparabilité des passages. |

## Points trompeurs mis au jour

1. **Unité de `s`.** `ProgressEstimate` borne `s_fused/s_visual/s_odometry` entre0 et1.
   Le domaine `TelemetrySample.s` reçoit cette fraction. Le catalogue utilise `s` en
   mètres comme convention future : nommer `s_norm` / `s_m` explicitement dans le
   prochain contrat, sans renommer silencieusement les artefacts telemetry-v2.
2. **Minimap ≠ trajectoire.** La centerline est une courbe en pixels de la petite carte.
   Le point projeté fournit une progression longitudinale ; aucun `d` de voiture sur
   la chaussée n'est calculé. `distance_m` interne vient d'intégration, pas d'un GPS.
3. **Chrono HUD absent du chemin moderne.** Une méthode legacy
   `extract_last_lap_time()` existe, avec maintien possible de l'ancien texte, mais
   run-024 conserve `lap_time_s=null`. Ne pas annoncer cette extraction comme livrée.
4. **TC/ABS : ancien code présent, résultat moderne absent.** Les détecteurs de couleur
   legacy existent ; `observe_frame_telemetry()` publie explicitement missing pour ces
   champs. Leur présence dans les sources ne signifie pas une capacité active.
5. **Moyennes anciennes.** `generate_summary()` ne filtre pas tous les champs par
   qualité et ne classe pas les tours complets/propres. Son `total_laps=5` compte ici
   cinq numéros, avec seulement trois tours bornés. Si toutes les vitesses sont absentes,
   il produit encore `avg_speed=max_speed=0.0` : comportement reproduit en mémoire sur
   deux lignes, à corriger avant d'utiliser ces agrégats dans les nouvelles métriques.
6. **Interpolation de comparaison.** `resample_records()` interpole sur des portions
   bornées et indique la qualité. Ce consommateur diagnostic ne modifie pas les
   pédales sources ; ses valeurs interpolées ne deviennent pas des lectures nouvelles.
7. **Revue de scène externe.** L'IA a pu lire le PDF et formuler une hypothèse ; le
   pipeline n'a pas lui-même extrait les faits spatiaux mentionnés dans cette réponse.

## Ce qui est raisonnablement accessible depuis la vidéo

**Déjà présent :** signaux HUD principaux, compteur, temps/qualité et progression estimée.
**Prochain incrément simple :** épisodes temporels frein/gaz et descripteurs B03–B07,
A01–A07 sur plages admissibles ; garder position métrique et diagnostic inconnus.
**Puis :** champs HUD supplémentaires réellement visibles (régime, aides réglées,
carburant, pressions affichées, avertissements), avec ROI/calibration/sémantique vérifiées.
**Chantier central :** trajectoire, bords, orientation et repères physiques. Données PC
appariées possibles pour labels/validation ; elles servent d'abord l'extraction vidéo.

Tout n'est pas identifiable à partir des pixels : pression hydraulique, charges pneus,
forces, glissements individuels et états mécaniques cachés ne deviennent pas des vérités
par estimation. Une méthode peut fournir un proxy évalué ; sinon le champ reste
`unavailable` avec sa raison. Documenter ce plafond physique fait partie de « récupérer
les données », plutôt que promettre les72 entrées depuis toute caméra.

La plateforme, le serveur MCP et les skills de navigation sont la destination future.
Ils attendent ce socle de données ; le format telemetry-v2 existant suffit aux prochains
incréments locaux. Voir le [plan unique](plans/video-to-agent-platform.md).

## Vérification et reproductibilité de l'audit

Fonctions existantes exécutées en mémoire : `read_session_artifacts`, `control_events`,
`gear_events`, `generate_summary`. Les fichiers sources et artefacts n'ont pas changé.
Tests de comportement existants consultés, non relancés pour cette cartographie. Le
nettoyage documentaire est vérifié par les tests de routage/structure adaptés, sans
suite OCR ni vidéo complète. Les chiffres sont des sorties automatiques, pas une
campagne de nouvelle vérité. [Catalogue complet](driving-metrics.md).
