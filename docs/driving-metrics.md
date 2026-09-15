---
summary: researched circuit-driving metric catalogue with definitions, data requirements, reference limits and priorities for AI session tools
read_when:
  - defining the shared video and PC telemetry contract or MCP query outputs
  - choosing driving metrics, recurring-loss comparisons or required sensors
  - distinguishing measured behaviour from a coaching hypothesis
---

# Métriques de conduite sur circuit — catalogue pour notre système

Recherche Internet du **14 septembre 2026**. Périmètre : ACC, conduite GT sur circuit,
progression d'un pilote amateur, puis compatibilité télémétrie PC. **72 entrées**
regroupées par usage ; certaines contiennent plusieurs composantes. Catalogue large,
pas inventaire universel de toute la dynamique automobile ni prescription de tout coder.

Les sources primaires sont des documentations de fabricants, formations de leurs auteurs
et travaux de recherche. Les liens sont placés avec les thèmes qu'ils étayent. **Les
identifiants, définitions opérationnelles, agrégations et priorités ci-dessous sont notre
proposition de contrat**, pas une norme empruntée à un fournisseur. Aucun seuil de
bonne conduite ni indicateur de compétence universel n'est adopté.

## Utilisation actuelle du catalogue

Depuis le15 septembre, la priorité est l'extraction des données depuis la vidéo ; la
plateforme navigable par agent reste la destination, à construire ensuite. Voir
[l'audit des72 entrées face au code](video-data-audit.md). Une métrique recherchée n'est
pas une fonctionnalité existante ni une garantie d'observabilité depuis les pixels.

## Conclusion de la recherche

Le socle utile combine **temps perdu + trajectoire + commandes + réponse de la voiture
+ répétition + contexte**. On localise les écarts temporels, puis on les explique en
croisant les autres champs. La référence personnelle ne révèle pas nécessairement une
erreur répétée dans tous les tours. La qualité du comparateur est décisive.
[HPA — analyse du pilote](https://www.hpacademy.com/courses/data-analysis-fundamentals/hpa-6-step-analysis-process-analyse-driver-performance).

La trajectoire est centrale pour condenser le placement, mais elle ne suffit pas : une
étude sur simulateur de plus de 1 200 tours distingue trajectoire et exploitation dynamique
de l'adhérence. Dans son échantillon de sept professionnels et deux amateurs, le déficit
vient surtout du second aspect. Ce résultat ne s'étend pas automatiquement à notre pilote
ou à ACC ; il justifie de conserver les commandes et la dynamique avec la ligne.
[von Schleinitz et al., 2022 — résumé de l'étude](https://arxiv.org/abs/2201.12939).

## Conventions et données requises

- `t` : temps monotone de session en s, lié à la vidéo par une transformation documentée.
- `s` : convention cible en m (`s_m`) sur un **repère de piste commun**. Le code
  actuel utilise `s`/`s_fused` normalisés0–1 (`s_norm`), sans conversion métrique
  garantie ; ne pas renommer les anciens artefacts implicitement. `l` : distance réellement
  parcourue par la voiture. Elles ne sont pas interchangeables.
- `d` : écart latéral signé à ce repère ; convention proposée positif à gauche.
- `psi` : orientation du châssis ; `e_psi` : angle châssis/tangente de piste.
- `chi` : direction de déplacement ; `beta` : angle entre déplacement et châssis.
  **Orientation dans la piste, angle de volant et dérive ne sont pas la même mesure.**
- `u_b`, `u_a` : commandes frein et gaz normalisées, avec calibration et origine.
  **Un pourcentage de pédale n'est pas une pression hydraulique en bar.**
- `delta_sw` : angle du volant ; `delta_rw` : angle de braquage des roues. Conversion
  seulement si la cinématique/rapport de direction est connue et applicable.
- `a_x`, `a_y` : accélérations dans un repère déclaré ; `r` : vitesse de lacet.

Le repère de Frenet formalise progression, écart transversal et courbure ; il impose une
référence géométrique définie. Une approximation plane ne résout pas à elle seule les
pentes, dévers, projections ambiguës ou excursions de Spa.
[MathWorks — referencePathFrenet](https://www.mathworks.com/help/nav/ref/referencepathfrenet.html).

| Code d'entrée | Données | Situation actuelle du projet |
|---|---|---|
| T | Horloge, frames, bornes de tour/zone | Horloge et compteur disponibles ; zones multi-tours et repères physiques à qualifier. |
| V | Vitesse | Lecture vidéo disponible avec trous et raisons ; vérifications ponctuelles seulement. |
| B/A/G | Frein / gaz / rapport | Lectures présentes ; biais pédales, blips, erreurs possibles. Aucun lissage. |
| P | Position, `s`, `d`, bords et géométrie | `s` existant estimé ; `d` et trajectoire métrique non livrés. |
| O | Orientation et vecteur vitesse | Non qualifiés depuis la vidéo ; piste PC à tester. |
| S | Braquage physique | Animation/ancien champ `steering` insuffisants pour revendiquer un angle réel. |
| D | Accélérations, lacet, dynamique | Non qualifiés actuellement ; dériver une vitesse OCR n'en fait pas une mesure fiable. |
| W | Roues, pressions, charges, glissements, interventions | Non acquis/qualifiés actuellement. |
| E | Régime moteur, moteur/boîte | Rapport partiel disponible ; autres canaux à acquérir. |
| C | Pneus, carburant, météo, setup, trafic, état de piste | Contexte partiel ; collecte explicite requise. |
| R | Référence comparable, provenance et variabilité | Référence expérimentée non disponible actuellement. |
| Q | Qualité, couverture, précision, synchronisation | Raisons déjà préservées ; erreur spatiale/dynamique non établie. |

« Donnée disponible » ne signifie ni métrique implémentée ni exactitude qualifiée.
Dans toutes les tables, une entrée nécessaire absente rend la métrique indisponible,
ou limitée à un proxy explicitement différent. Gate A reste FAIL.

## 1. Temps et conséquences — où se perd la performance ?

L'usage du delta temporel et des comparaisons par portion de piste est documenté par
[VBOX — Circuit Tools](https://vboxmotorsport.co.uk/index.php/en/circuit-tools).
L'alignement par distance roulée peut se décaler lorsque les lignes diffèrent :
[VBOX — limites de l'alignement et position](https://vboxmotorsport.co.uk/us/predictive-lap-timing).
Nous n'importons pas les promesses de précision du matériel VBOX dans nos estimations.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| T01 | Temps du tour / passage : `t_fin - t_début` (s) | T,Q | Bornes communes ; complet, valide, partiel et perturbé restent distincts. |
| T02 | Profil de vitesse `v(s)` et écart `v(s)-v_ref(s)` (km/h) | V,P,R | Localise différences ; vitesse supérieure n'est pas forcément avantageuse ensuite. |
| T03 | Delta cumulé `Delta(s)=t_pilote(s)-t_ref(s)` (s), même origine | T,P,R | Positif = retard ; nécessite progression comparable, sans raccord sur excursion. |
| T04 | Écart créé dans une zone : `Delta(s_fin)-Delta(s_début)` (s) | T,P,R | Sépare retard hérité et retard accumulé ; ne donne pas la cause. |
| T05 | Vitesses à l'entrée, au minimum et à la sortie, avec leurs positions | V,T,P | Repères distincts ; minimum de vitesse ≠ apex géométrique. Trou susceptible de cacher l'extrême. |
| T06 | Conséquence à un repère aval : écart de vitesse et temps jusqu'au freinage suivant | V,T,P,R | Une sortie lente prolonge l'écart ; éviter de compter deux fois la même portion. |
| T07 | Potentiel théorique par meilleurs secteurs + écart au tour reproductible | T,R,C | Indication secondaire ; secteurs optimaux parfois incompatibles. Jamais cible novice par défaut. |

Le « tour optimal » est aussi une construction proposée par certains produits ; son
existence n'en fait pas une vérité physique ou un passage reproductible pour le pilote.
[Garmin — principe du True Optimal Lap](https://www.garmin.com/es-US/p/690726/pn/010-02345-00/).

## 2. Trajectoire et placement — comment la voiture parcourt la piste ?

Les comparaisons de lignes et leur combinaison avec les commandes sont documentées par
[SRT — analyse des trajectoires](https://docs.simracingtelemetry.com/kb/how-to-analyze-racing-lines).
Les métriques géométriques suivantes opérationnalisent cette représentation ; aucune
ligne universellement idéale n'est présumée.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| P01 | Trajectoire spatio-temporelle `(t,s,d)` et points monde si disponibles | T,P,Q | Objet central persisté, avec intervalles d'incertitude et trous. |
| P02 | Écart à la référence `d(s)-d_ref(s)` ; biais signé et erreur absolue | P,R | Décrit différence de ligne, pas faute par sa seule amplitude. |
| P03 | Placement à l'entrée, au point de corde géométrique et à la sortie | P,T | Compare préparation/exécution ; règles d'identification versionnées, plusieurs cordes possibles. |
| P04 | Marge aux bords gauche/droit (m) et excursions | P,O,dimensions | Un point caméra/centre n'indique pas où sont les quatre roues. |
| P05 | Largeur utilisée et enveloppe latérale dans la zone (m) | P | À interpréter avec virages suivants, vibreurs, trafic et dévers. |
| P06 | Courbure du trajet `kappa=dchi/dl` (1/m), rayon `1/abs(kappa)` | P,O | Sensible au bruit ; rayon infini en ligne droite, pas division artificielle par zéro. |
| P07 | Orientation relative `e_psi=wrap(psi-psi_piste(s))` (rad/deg) | P,O | Décrit direction du châssis ; ne mesure pas seule le sous-virage ou la dérive. |
| P08 | Longueur réellement parcourue `l` et écart à la référence (m) | P,R | Une ligne plus longue peut permettre un meilleur temps ; ne pas minimiser isolément. |

## 3. Freinage — lieu, montée, maintien et relâchement

Les points de freinage, amplitudes et formes temporelles se lisent ensemble :
[HPA — Braking Markers](https://www.hpacademy.com/courses/professional-motorsport-data-analysis/braking-performance-braking-markers/),
[HPA — analyse des données de freinage](https://www.hpacademy.com/previous-webinars/286-how-to-analyse-braking-data/?vvst=0).
Ces méthodes physiques ne rendent pas nos pourcentages HUD équivalents aux capteurs de pression.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| B01 | Début du freinage `(t,s,v)` ; écart de position au comparateur | B,T,V,P,R | Plus tard n'est meilleur que si l'ensemble du passage en bénéficie. |
| B02 | Fin du freinage `(t,s)` | B,T,P | Conditionne la transition ; résidu de lecture ≠ frein réellement maintenu. |
| B03 | Durée et distance de l'épisode (s, m) | B,T,P | Publier les deux ; entrée différente ou trou rend la comparaison ambiguë. |
| B04 | Pic, niveau soutenu, temps pour atteindre le pic | B,T | Pression ou commande explicitement distinguées ; pic court sensible à l'échantillonnage. |
| B05 | Montée initiale : variation / durée, ou temps entre niveaux calibrés | B,T,Q | Pas un score de confiance ; dérivée du HUD très sensible au bruit. |
| B06 | Relâchement : début, durée, pente, paliers et réapplications | B,T | Décrit dégressivité et interruptions ; conserver le profil, pas uniquement une pente moyenne. |
| B07 | Aire de commande `integrale u_b dt` (%·s) ; aire de pression si vraie pression | B,T | Descripteur comparable avec calibration ; ni énergie dissipée ni travail des freins. |
| B08 | Décélération atteinte et profil de décélération pendant freinage | D,B,T,V | Réponse réelle ; pente, aéro, moteur, pneus et freinage modifient la relation à la commande. |
| B09 | Frein pendant la rotation : durée et profil conjoint frein/braquage ou courbure | B,S ou P,D,T | Candidat de trail braking ; pas « bon » par sa simple présence. |
| B10 | Blocages / interventions ABS : fréquence, durée, roue/essieu | W,T,B | Réglage ABS ≠ intervention ; ABS actif n'est pas automatiquement une erreur en GT3. |

## 4. Gaz et transitions entre commandes

AiM décrit des états frein/gaz/roue libre et des agrégats de temps/distance, utiles pour
une synthèse. Nous retenons les descripteurs, pas les interprétations automatiques de
peur ou d'inefficacité. [AiM — états et canaux d'analyse](https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html).
L'enseignement sur les gaz rappelle aussi l'importance de la progressivité selon le
rapport et la situation. [Almeida Racing Academy — Throttle Applications](https://almeidaracingacademy.com/sim-racing/learn/lessons/throttle-applications).

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| A01 | Première reprise des gaz `(t,s)` et reprise durable distincte | A,T,P | Une impulsion ou un blip ne constitue pas nécessairement une accélération volontaire. |
| A02 | Position/temps d'atteinte du plein gaz calibré et maintien | A,T,P,Q | Pas de seuil universel à 100 % : notre plein gaz est souvent lu à94,12 %. |
| A03 | Rampe de gaz : délai entre niveaux, pente et profil | A,T | À croiser avec rapport, rotation et grip ; montée rapide pas systématiquement meilleure. |
| A04 | Relâchements/réapplications après reprise : nombre, amplitude, durée | A,T | Signature de modulation ; trafic, corrections, TC ou blips possibles. |
| A05 | Temps/distance sans commande frein ni gaz mesurable | A,B,T,P | Décrit phase neutre ; moteur, pente et adhérence restent actifs. Pas une faute universelle. |
| A06 | Chevauchement frein/gaz et délai signé entre fin frein et reprise gaz | A,B,T,Q | Latence intercanaux critique ; coordination ou automatisme à distinguer. |
| A07 | Répartition temporelle plein gaz / partiel / coupé, par phase et zone | A,T,Q | Résumer sous un dénominateur observable ; un pourcentage global masque les lieux et causes. |

## 5. Volant et coordination — comment la voiture est mise en rotation ?

Une trace de volant doit être interprétée avec vitesse, réponse latérale et contexte.
Une entrée précoce peut exiger davantage de braquage sans établir un sous-virage physique.
[HPA — Steering Data & Balance](https://www.hpacademy.com/courses/professional-motorsport-data-analysis/cornering-performance-steering-data-and-balance/).

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| S01 | Début du braquage et délai avant réponse en lacet/courbure | S,D ou P,T | Séparer action du pilote et mouvement ; animation cockpit non calibrée exclue. |
| S02 | Angle maximal/soutenu et durée du braquage | S,T | Dépend du rayon, vitesse, rapport de direction et setup. |
| S03 | Vitesse de braquage `d(delta)/dt` et transitions brusques | S,T,Q | Événement à contextualiser, pas objectif « le plus lent possible ». |
| S04 | Corrections : inversions, amplitude et variation totale `somme abs(delta_i-delta_i-1)` | S,T,Q | Définir bruit/cadence ; ne pas compter le droite-gauche prévu comme correction. |
| S05 | Débraquage et relation temporelle à la reprise des gaz | S,A,T | Descripteur de coordination entrée/sortie, sans règle universelle d'exclusivité. |
| S06 | Effort de braquage intégré `integrale abs(delta) dt`, par phase | S,T | Comparaison à vitesse/ligne proches ; une valeur faible seule ne prouve pas la maîtrise. |

## 6. Réponse dynamique et adhérence — ce que produit la commande

Le diagramme longitudinal/latéral est utile mais son enveloppe dépend de la vitesse,
du dévers et de l'aérodynamique. [HPA — diagrammes et affichages](https://www.hpacademy.com/courses/professional-motorsport-data-analysis/supporting-concepts-displays/).
Vitesses locales, lacet et glissements sont des grandeurs distinctes dans les modèles
physiques : [MathWorks — modèle de dynamique véhicule](https://www.mathworks.com/help/ident/ug/modeling-a-vehicle-dynamics-system.html).

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| D01 | Profils `a_x`, `a_y` et nuage G-G, séparés par phase/vitesse | D,T,V | Capacité utilisée observée ; maxima seuls ne décrivent pas l'adhérence disponible. |
| D02 | Accélération combinée `sqrt(a_x²+a_y²)` ; écart à enveloppe comparable | D,V,C,R | Ne pas appeler ce ratio « % de grip » sans modèle/enveloppe validés. |
| D03 | Vitesse de lacet `r`, réponse au volant et évolution en entrée/sortie | D,S,T | Vitesse de rotation, différente de l'orientation et du rayon parcouru. |
| D04 | Dérive châssis `beta=atan2(v_y_local,v_x_local)` | O,T | Exclure quasi-arrêt ; angles de dérive des pneus avant/arrière différents. |
| D05 | Glissement longitudinal de chaque roue | W,V,S,O | Exiger définition du canal, rayon roulant et vitesse roue-sol pertinente ; virage ≠ patinage. |
| D06 | Résidu de réponse : braquage vs lacet/accélération, modèle contextualisé | S,D,V,C | Hypothèse de déséquilibre avant/arrière ; pas verdict depuis le seul volant. |
| D07 | Transitoires / jerk / oscillations, associés aux commandes et surfaces | D,T,C | Dérivées bruitées ; vibreur ou bosse n'est pas brutalité du pilote. |

## 7. Boîte et exploitation du moteur

Régime et rapport par endroit du circuit font partie des vues usuelles de comparaison.
[HPA — Track Reports](https://www.hpacademy.com/courses/data-analysis-fundamentals/the-data-analysis-tool-box-track-reports/).

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| G01 | Rapport choisi à l'entrée, au minimum, à la sortie ; séquence | G,T,P | Comparer même voiture/transmission ; aucun rapport idéal universel. |
| G02 | Régime au changement et temps au limiteur | G,E,T | Limite valide de cette voiture ; vitesse seule insuffisante. |
| G03 | Coupure de poussée lors d'un changement : durée/réponse | G,A,D,T | Logique de boîte automatique/séquentielle à prendre en compte. |
| G04 | Rétrogradages synchronisés avec variations frein, lacet et roues | G,B,D,W,T | Cherche associations d'instabilité ; le changement seul n'en établit pas la cause. |

## 8. Régularité, récurrences et progression — l'échelle séance

MAD et IQR résistent mieux aux valeurs extrêmes qu'une seule étendue max-min ; ils ne
remplacent ni l'effectif ni l'examen des incidents. [NIST — mesures de dispersion](https://itl.nist.gov/div898/handbook/eda/section3/eda356.htm).
Les agrégations suivantes sont notre proposition pour passer d'une lecture de tour à
une description des difficultés répétées, sans transformer la dispersion en faute.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| R01 | Allure habituelle : médiane et distribution des temps comparables | T,C,Q | Séparer tours propres et perturbés ; garder tous les effectifs. |
| R02 | Répétabilité : MAD/IQR des temps, repères de commandes et placements | T,P,B,A,S | Comparer par zone/type ; mélange de zones ou conditions trompeur. |
| R03 | Fréquence d'une signature : occurrences / passages observables et éligibles | Métriques,C,Q | Inclure contre-exemples et exclus ; 60 samples ne sont pas60 essais indépendants. |
| R04 | Biais récurrent face à référence : médiane des écarts signés + dispersion | Métriques,R,C | Une erreur constante a peu de dispersion ; la référence est indispensable. |
| R05 | Importance temporelle : médiane/pire cas/somme des écarts de zones disjointes | T,P,R,Q | Bilan descriptif d'écarts, pas somme de gains causaux récupérables. |
| R06 | Évolution sur le relais / entre séances comparables | Métriques,C,T | Pneus, carburant, piste et apprentissage se confondent sans contexte. |
| R07 | Effet d'un exercice : avant/après, répétabilité et transfert à d'autres zones | Métriques,C | Modifier un facteur à la fois autant que possible ; pas causalité depuis un seul essai réussi. |

## 9. Incidents et conduite en présence d'autres voitures

Ces entrées sont une extension de contrat utile pour conserver les conséquences et le
contexte. Leur détection automatique n'est pas livrée ; elles ne doivent pas produire
un jugement de responsabilité depuis une caméra ou un indicateur isolé.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| I01 | Excursions/invalidations : nombre, durée, zone, marge et reprise | P,T,C,Q | Séparer confirmation jeu, quatre roues mesurées et simple observation visuelle. |
| I02 | Incident : rotation, contact, temps de récupération et conséquence | P,O,D,T,C | Contact prouvé séparément ; vitesse OCR peut manquer au choc. |
| I03 | Trafic/bataille : exposition, écarts aux autres voitures, temps perturbé | Positions adverses,T,C | Une ligne défensive ne se juge pas comme tour libre ; pas faute déduite du seul contact. |

## 10. Contexte, pneus et endurance — expliquer les différences

Les journaux de setup, pneus, carburant et conditions accompagnent les analyses de
pilotage. [HPA — Driver Analysis Basics](https://www.hpacademy.com/previous-webinars/275-driver-analysis-basics/?vvst=0),
[HPA — fiche de collecte et d'analyse](https://www.hpacademy.com/assets/Course-Content/Professional-Data-Course/093abdd6ca/HPA_Data-Analysis-Checklist-v2.pdf).
Ces indicateurs servent d'abord à rendre les comparaisons honnêtes, pas à inventer une
cause mécanique à chaque perte de temps.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| C01 | Carburant utilisé par tour et masse/charge initiale | C,T | Consommation et comparabilité ; frein moteur/lift-and-coast parfois volontaires. |
| C02 | Pressions pneus par roue : niveau et évolution | W,C,T | Unité/température associées ; aucune cible universelle ni ancienne cible ACC reprise. |
| C03 | Températures pneus : carcasse/surface, intérieur/milieu/extérieur | W,C,T | Canaux distincts ; cambrure, glisse, charge et conduite se mélangent. |
| C04 | Âge/usure/salissure des pneus et évolution des performances | W,C,T | Vérifier que le canal varie réellement ; une constante peut signifier indisponible. |
| C05 | Températures freins et répartition : réglage vs pressions mesurées | W,B,C | Distinguer consigne de bias et répartition effective. |
| C06 | Réglages et interventions TC/ABS, aides/boîte et changements | W,C,T | Stocker réglage ET activité ; aucune règle « jamais de TC/ABS ». |
| C07 | Température piste/air, pluie, grip, vent, setup, version jeu/voiture | C,T | Métadonnées de comparabilité ; valeurs manquantes explicitement inconnues. |
| C08 | Suspension, charges roues, hauteur de caisse, talonnage | W,C,T | Extension avancée si un problème de châssis est suspecté ; inutile comme score initial du pilote. |

## 11. Qualité de l'observation — peut-on croire la comparaison ?

Ce sont des métriques du système, pas du pilote. Elles prolongent notre
[contrat de signaux](signal-treatment.md) et doivent accompagner toutes les réponses.

| ID | Métrique et définition proposée | Entrées | Utilité / limite |
|---|---|---|---|
| Q01 | Couverture valide par champ/zone, plus longue lacune et fraîcheur | Q,T | Un taux global élevé peut cacher une absence au moment décisif. |
| Q02 | Offset/dérive/incertitude de synchronisation entre champs et médias | Q,T | Conditionne ordre d'actions et chevauchements ; 60 fps ne signifie pas précision physique 16,7 ms. |
| Q03 | Erreur mesurée du signal et précision des événements | Annotations,Q | Biais, erreur absolue, percentiles, faux positifs/omissions ; contrôle ponctuel ≠ continu. |
| Q04 | Erreur spatiale, projection, bords et couverture de confiance | P,référence,Q | Conditionne d, sortie de piste et classement des trajectoires. |
| Q05 | Complétude du contexte, comparabilité et taille d'échantillon | C,R,Q | Afficher limites/exclusions ; pas de score de confiance arbitraire agrégeant tout. |

## Référence : ce qu'il faut conserver

**Deux objets distincts :** une géométrie de piste pour mesurer ; des passages de
référence pour comparer la performance. La référence de conduite devrait être une série
reproductible d'un pilote expérimenté, avec véhicule/version, pneus, carburant, setup,
aides, état de piste et trafic documentés. Une série personnelle stable reste utile pour
l'irrégularité, avec un plafond pédagogique annoncé.

Proposition : stocker les passages réels et leurs distributions par zone ; sélectionner
un passage représentatif identifiable pour illustrer. Une ligne « médiane » et des gaz
« médians » calculés indépendamment peuvent former un passage qui n'a jamais existé.
Leur enveloppe statistique est descriptive, jamais une trajectoire optimale garantie.
Une référence inconnue ou trop différente reste utilisable pour expliquer une technique,
mais ne qualifie pas un écart chiffré de secondes récupérables.

## Définitions minimales pour éviter des chiffres trompeurs

Ces règles sont notre contrat de calcul proposé, à spécifier avant implémentation.

- Une **zone** possède un repère géométrique ou des bornes visuelles qualifiées ; une
  séquence de plusieurs virages reste analysable ensemble pour inclure la conséquence.
- Un **événement** conserve instant candidat, confirmation, intervalle d'incertitude,
  seuils/configuration, qualité et lien source. Les seuils5/2 % et0,1 s existants
  servent à l'index M1 ; ils ne définissent pas une technique correcte.
- Un **minimum/maximum** n'est qualifié que si la fenêtre pertinente l'est. Sinon
  publier « minimum observé » avec lacune, sans le comparer comme véritable minimum.
- Les **dérivées** sur vitesse OCR ou position bruitée restent non qualifiées. Les
  sources proposent parfois du filtrage ; cela n'autorise pas à lisser nos pédales.
  Conserver les bruts et différer le calcul fragile plutôt que fabriquer une courbe.
- Une **projection spatiale** respecte direction et continuité ; quasi-arrêt, marche
  arrière, croisement de segments ou excursion peuvent la rendre ambiguë. Ne pas
  transformer une récupération d'incident en progression normale par interpolation.
- Ne pas masquer les écarts de temps par un alignement qui déforme le temps pour faire
  coïncider les actions. Comparer aux mêmes lieux/repères ; garder les temps natifs.
- **Toutes les distributions** indiquent effectif observable, exclusions et période.
  Une répétition s'évalue sur les passages/séances, pas sur le nombre de frames.
- **Association ≠ cause** : un point de frein plus tardif accompagné d'une sortie large
  peut soutenir une hypothèse, pas identifier seul la cause ou le gain d'une correction.

## Ce que nous ne retiendrons pas comme verdict automatique

- « Plus de plein gaz = meilleur », « moins de roue libre = meilleur », « plus tard
  au frein = meilleur », « moins de volant = meilleur » sans contexte et référence.
- Position minimale au vibreur, vitesse minimale et pic de volant traités comme un même apex.
- Réglage ABS/TC interprété comme activation ; pédale % renommée pression ; animation
  cockpit renommée angle des roues ; `d` assimilé à dérive.
- Somme d'accélérations divisée par somme de pédales présentée comme efficacité du grip :
  dénominateur nul possible, calibration arbitraire et limites physiques non représentées.
- Score unique de pilotage fondé sur moyennes de tour ou entropie. L'entropie de volant
  a notamment été étudiée pour la charge de travail, pas comme verdict universel de
  vitesse ou compétence. [SAE — Steering Entropy, 1999](https://saemobilus.sae.org/papers/development-a-steering-entropy-method-evaluating-driver-workload-1999-01-0892).
- Fatigue, confiance, regard, intention et peur déduits automatiquement des commandes.
  Recueillir le ressenti ; eye-tracking et physiologie seraient des entrées séparées.

## Ce que PC change réellement

L'annexe du guide AiM pour ACC décrit vitesse/commandes, orientation, lacet,
accélérations et des canaux avancés de position monde, vitesses locales et roues.
C'est une piste documentée pour l'acquisition, **pas la preuve que notre futur logger
fournira chaque champ correctement**. Le guide comporte même une ambiguïté explicite
sur ABS. Ne pas confondre cette acquisition avec le contenu d'un simple export MoTeC.
[AiM — guide ACC, annexe pp.4–6 imprimées](https://www.aimtechnologies.com/aim-support/docs/AssettoCorsaCompetizione_100_eng.pdf).

SRT documente une collecte ACC via mémoire partagée sous Windows ; l'accès depuis Mac
peut passer par un collecteur Windows. Son outil ne conserve que les tours complets
chronométrés : cette politique ne conviendrait pas telle quelle à notre besoin de
conserver incidents et bords de séance. Nous n'avons choisi ni acheté aucun collecteur.
[SRT — acquisition ACC](https://www.simracingtelemetry.com/games/ACC/).

Le test PC doit vérifier champs réellement non nuls/variables, unités/axes, centre de
référence, horloges et alignement vidéo. Il faut une géométrie de piste pour calculer
`d` et des données adaptées avant toute affirmation de dérive ou charge d'adhérence.
L'interface normalisée conservera la provenance `video_reading`, `pc_direct` ou
`derived_estimate` ; ce sont des catégories proposées, pas un schéma déjà implémenté.

## Priorités pour la première base de séances

Les questions de coaching se traitent par rapprochement, jamais par un chiffre seul :

| Question à examiner | Preuves à rapprocher, proposition de méthode |
|---|---|
| Freinage régulièrement trop tardif ? | B01 face à référence, vitesse/placement d'entrée, T04/T06 et occurrences R03/R04. |
| Relâchement qui perturbe l'entrée ? | B06, réponse en lacet, corrections et ligne ; séparer réapplication du pilote et bruit. |
| Mauvaise préparation du virage suivant ? | P03/P07 avant ce virage, commandes dans le précédent et conséquence aval T06. |
| Reprise de gaz qui compromet la sortie ? | A01/A03/A04 avec braquage, dérive/roues si disponibles, puis P04 et T06. |
| Mauvais choix de rapport ? | G01/G02 avec accélération, vitesse de sortie et référence de même transmission. |
| Difficulté globale ou accident isolé ? | R03/R04, plusieurs zones comparables, contre-exemples, état pneus/piste et I01/I02. |

**Socle de mesure :** T/P/Q et métadonnées de référence. Sans eux, les comparaisons
peuvent être fausses même avec de très beaux graphes. La trajectoire garde sa priorité
M2/M3 ; le catalogue ne prétend pas la remplacer par des moyennes de pédales.

**Premier ensemble utile pour l'IA :** T01–T06, P01–P04/P07, B01–B06/B09,
A01–A06, S01/S04/S05, R01–R05, I01/I02 et Q01–Q05, activés seulement avec les entrées
qualifiées. Chaque zone reçoit ces descripteurs et leurs distributions, pas toutes
les images. Les données dynamiques D03–D06 apportent ensuite les moyens de discuter
la cause physique ; les champs de contexte C doivent être conservés dès l'acquisition.

**Sortie compacte d'une récurrence, proposition :**

```text
signature_id ; définition/configuration
zones et phases concernées ; passages réellement comparables
occurrences / passages observables ; exclusions et contre-exemples
écarts de temps observés + référence + dispersion (ou indisponible)
descripteurs associés : placement, orientation, frein, gaz, volant, dynamique
qualité et inconnus ; identifiants des preuves consultables
```

Le serveur classe d'abord les écarts établis et les incidents récurrents en conservant
fréquence et sévérité distinctes. Un produit « fréquence × perte médiane » peut devenir
une aide de tri documentée, mais n'est ni une perte causale ni une prescription. Ne pas
additionner des fenêtres chevauchantes et ne pas supprimer un incident rare mais grave
au seul motif qu'il est peu fréquent. Le diagnostic appartient à l'IA.

## Conséquence pour les outils MCP envisagés — phase ultérieure

- `get_session_summary` : couverture, contexte, zones, distribution des performances,
  références disponibles et récurrences ; budgets et sélection annoncés.
- `compare_passages` : descripteurs aux repères communs, trajectoires et commandes,
  écarts signés et limites de comparabilité.
- `find_recurrences` : recherche d'une signature avec effectifs et contre-exemples,
  sans transformer une hypothèse de l'IA en fait du système.
- `get_metric_definition` : formule, unité, prérequis, version, paramètres et limites.
- `get_evidence` : valeurs natives ou quelques images/extrait ciblé, liés au calcul.

Noms et contrats indicatifs ; aucun serveur ni calcul nouveau n'est livré par cette
recherche. La prochaine action est l'extraction de données et les premiers épisodes
frein/gaz depuis les artefacts existants. Le contrat de navigation/MCP attend le socle
de mesures défini dans le plan ; l'audit distingue code présent et calculs à ajouter.

## Portée des sources et vérification

Sources consultées via pages primaires, transcriptions et PDF publics. Les cours
illustrent des situations et parfois des heuristiques : nous n'en importons ni les
seuils ni les conclusions automatiques. Le travail de 2022 est utilisé depuis son
résumé, avec sa portée annoncée. Certaines pistes récentes (entropie/LLM, prédiction
de performance) étaient seulement indexées ou inaccessibles en texte intégral ; elles
ne fondent pas nos formules ou seuils. Aucun résultat scientifique n'est une
qualification ACC PS5, d'un modèle de trajectoire ou de notre extraction actuelle.

Cette recherche modifie uniquement la documentation. Aucun replay OCR, entraînement,
seuil changé, collecte PC ou test logiciel. [Plan actif](plans/video-to-agent-platform.md)
et [passation](current-status.md) restent les points de conduite du travail.
