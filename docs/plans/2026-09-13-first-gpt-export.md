---
summary: single evolving plan from the delivered first export to complete temporal perception and PC-supervised lateral placement for AI analysis
read_when:
  - deciding the next milestone after the first session_coaching.md
  - preparing full-session temporal evidence or the PC-supervised d feasibility test
---

# Plan actif — construire les yeux de l'IA

**Direction clarifiée le 14 septembre 2026.** Ce même plan prolonge le premier export.
La première tranche M1 est implémentée le 14 septembre dans run-027 ; M2–M5 restent
à exécuter selon leurs prérequis.
[État réel](../current-status.md) ; [contrat du premier export déjà implémenté](../specs/2026-09-13-session-coaching-report.md).

## Finalité et séparation des responsabilités

Notre logiciel rend la session observable : scène, commandes, temps, placement,
contexte et qualité. **L'IA identifie les difficultés, discute les causes et propose
l'entraînement.** Le générateur ne sélectionne pas uniquement des erreurs supposées,
ne produit pas de diagnostic de conduite ni de programme d'entraînement.

Le fichier texte run-026 est une brique déjà livrée : trois passages,22 vitesses revues,
descriptions et limites. Il ne remplit pas la finalité : un seul enchaînement, pas de
vision du tour entier, séquences visuelles trop espacées pour certaines actions,
aucune position latérale `d`. L'export et les données run-024 restent réutilisables.

Le travail reste local et expérimental. Gate A reste FAIL, `coaching_eligible=false`.
Les anciens reports/tests ne deviennent pas une validation de nouvelles estimations.
La présence de `d` dans ce plan remplace son exclusion comme simple raffinement :
sa faisabilité doit être évaluée, sans prétendre qu'un modèle fiable existe déjà.
Pas d'achat/cloud payant, de dataset massif ou de reverse engineering implicite.

## Livrable cible

Un **dossier de perception de session**, contenant :

- vue d'ensemble de tous les tours et zones, avec les périodes non observables ;
- chronologie des mesures et événements neutres, liée aux frames et à la scène ;
- fenêtres temporelles comprenant approche, action et conséquence, réussies ou ratées ;
- placements/orientations/trajectoires estimés avec leur validité, lorsque démontrés ;
- contexte pilote/voiture/caméra et éventuelles références pédagogiques distinctes ;
- une entrée réellement consommable par l'IA, sans lui supposer l'accès à nos chemins locaux.

Pour nous : lecteur local avec vidéo/chronologie/courbes synchronisées. Pour le modèle :
texte d'index + données structurées compactes + preuves visuelles temporelles compatibles
avec le mode d'utilisation retenu. Tester réellement ce mode : des PNG chronologiques
ne sont pas un flux60fps, une vidéo non lue n'est pas une preuve consultée. Le paquet
indique ce qui est couvert, ce qui est résumé et comment obtenir un détail manquant.
Aucun seul CSV brut, photo isolée ou graphe de vitesse ne représente toute la conduite.

## M1 — Couverture du tour entier et perception temporelle

Première tranche livrée : [paquet M1](../perception-package.md), un tour8766 frames,
14 zones,95 candidats neutres, lecteur synchronisé et séquence dense. Pas encore
une couverture multimodale de tous les tours ou un essai dans une IA sans historique.

**Entrée :** source et artefacts run-024, export/revues run-026. Pas de nouvel OCR.

- [x] Sur un premier tour complet, définir toutes les zones à observer, pas seulement
  Les Combes ou les incidents. Conserver succès, passages ordinaires et perturbations.
  Le découpage initial peut être revu manuellement puis réutilisé sur les autres tours.
- [x] Indexer les événements factuels : attaque/relâchement frein, reprise/coupure gaz,
  changement de rapport. Le code produit des candidats avec seuils,
  persistance, temps et qualité explicites ; jamais « freinage trop tardif ».
- [ ] Ajouter les passages de repères physiques avec leurs preuves temporelles ; les
  bornes grossières de navigation du prototype ne constituent pas ces repères.
- [x] Produire la chronologie complète et les fenêtres liées aux zones/actions, avec
  contexte avant/après. Aucun freinage ne fait disparaître les virages parcourus à
  gaz constants : le découpage des zones complète la détection d'événements.
- [x] Synchroniser vitesse/frein/gaz/rapport avec les images. Garder les samples60fps
  disponibles, sans lisser ; précision réelle limitée par rafraîchissement HUD/lecteur.
- [x] Adapter le détail temporel à l'action : vue d'approche, séquence resserrée autour
  de la transition (par exemple0,1s, davantage si nécessaire), puis conséquence.
  Le pas de revue n'est pas une borne d'erreur garantie ; conserver les trous.
- [x] Tester une première entrée IA avec ces pièces, en annonçant les éléments qu'elle
  peut réellement lire. Une demande de détail doit pouvoir désigner zone/tour/temps.
  Préparation livrée dans run-028 : PDF autonome du passage 334–352 s, images intégrées,
  courbes et transitions, détail à 0,1 s. Le pilote le soumet lui-même à une IA externe.
  Retour reçu et comparé à la référence figée : reconstruction locale favorable,
  placement avant virage confirmé sur les images ; cause et coaching non validés.
  Accès visuel déclaré et étayé par le contenu, sans journal d'outils externe.

**Sortie :** prototype consultable d'un tour entier, avec au moins une séquence dynamique
suffisamment détaillée pour suivre l'ordre des commandes et mouvements. Pas de nouveau
bilan de compétences inventé. Étendre ensuite à tous les tours sans exclure les cas normaux.
**Acceptation :** retrouver la scène/les valeurs à un instant, examiner l'avant/après,
comparer une zone entre tours et identifier les intervalles réellement inconnus.

### Reprise du14 septembre au soir — première livraison M1

**Point de départ choisi : tour HUD4 de run-024**, entre les confirmations des
compteurs3→4 et4→5 : intervalle source **[0,316667 ;146,416667[ s**, frames19 à8784
incluses. Le manifeste confirme les bornes19 et8785. Ce sont des bornes du compteur
confirmé, pas une certification du franchissement physique ou de la légalité du tour.

Entrées déjà disponibles et vérifiées présentes lors de cette préparation :

- `data/lab/coaching-reliability/run-024/processed/crash-session/` ;
- vidéo indiquée dans ce manifeste : `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov` ;
- fiche et images revues : `run-026/interim/case.json` ;
- ancien export : `run-026/reports/session_coaching.md`, comme contexte/audit uniquement.

Commencer par relire les artefacts et réutiliser les preuves d'intégrité encore
applicables. Ne pas relancer l'extracteur pour découper la chronologie ou afficher
les données existantes. Pour de nouvelles images, respecter le contrôle1080p60CFR.

**Résultat concret attendu pour cette première tranche :**

1. Une vue de l'intégralité du tour choisi, avec temps, vitesse/frein/gaz/rapport,
   bornes de zones et données manquantes. Les zones non identifiées sont explicitement
   marquées, pas omises pour ne garder que les événements intéressants.
2. Un premier index source-bound des zones/actions neutres. La détection ne doit pas
   nommer une erreur de conduite. Les normales/réussites restent aussi accessibles.
3. Une fenêtre détaillée scène+commandes synchronisées, avec approche/action/sortie.
   Les Combes peut servir au premier raccord grâce aux médias existants ; cette fiche
   ne remplace pas la couverture du tour. Resserrement temporel si0,5s masque une action.
4. Un contrôle simple : choisir un temps, retrouver la frame/les valeurs, vérifier
   l'ordre d'une transition et constater que les absences restent visibles.

Sorties dans un nouveau dossier local ignoré, par exemple `run-027/` si toujours libre
(il l'était lors de cette préparation). L'agent choisit les détails de représentation
et les vérifications proportionnées. Aucun nouveau cadre web, bilan de faiblesses,
plan d'entraînement ou répétition de revue du compteur pour cette tranche.

**Préparation M2 sans bloquer M1 :** confirmer l'accès à un PC Windows avec ACC,
la possibilité d'enregistrer localement vidéo+télémétrie simultanées, les champs de
position/orientation et la source de géométrie. Variante McLaren, caméra/FOV et matériel
restent à préciser. Tant que ces entrées ne sont pas disponibles, noter le besoin exact
et poursuivre M1 ; ne pas lancer un entraînement ni acheter une solution.

Cette préparation a été exécutée pour le premier tour : run-027 contient le paquet
réel. La revue navigateur et45 tests ciblés sont faits. Les cases ne qualifient pas
les données ou le modèle globalement ; aucune exécution M2–M5 n’est impliquée.

## M2 — Construire et prouver les labels spatiaux sur PC

Ce volet peut se préparer pendant M1. **Dépendance : accès à ACC Windows et à une
capture locale simultanée vidéo+télémétrie**, à confirmer. Un fichier replay seul ne
prouve pas la disponibilité de tous les champs physiques.

- [ ] Commencer par environ30–60s de capture live PC native1080p60CFR et un logger
  des données disponibles : temps, identité voiture, position3D, orientation,
  vitesse/commandes, configuration caméra/FOV. Choisir le lecteur après vérification
  des champs réellement exposés, de leurs unités et de leur horloge.
- [ ] Mesurer la correspondance temps vidéo/télémétrie : offset, dérive, latence de
  rendu, pauses/doublons. Les samples proches ne suffisent pas à supposer une synchro.
- [ ] Obtenir une géométrie de piste de référence avec unités/axes et provenance.
  Définir quel point de voiture est mesuré. La ligne d'un pilote n'est pas la centerline.
- [ ] Calculer `d`, décalage signé dans le repère local de la route, et l'orientation
  relative à sa tangente si les données la permettent. Les bords servent à exprimer
  les marges/positions sur la largeur. Ni le d brut ni la géométrie ne sont présumés
  disponibles directement dans un fichier MoTeC ou un replay.
- [ ] Vérifier sur les images quelques positions volontairement différentes et des
  transitions ; publier erreurs/limites de labels et de synchronisation. Définir le
  budget de précision utile avant toute évaluation d'un modèle.

**Sortie :** une courte vidéo PC et ses labels spatiaux réellement synchronisés, avec
un repère géométrique démontré. **Acceptation :** on peut expliquer et vérifier chaque
label dans l'extrait. Si position, géométrie ou horloge manquent, nommer le composant
à obtenir : pas de grand entraînement sur des labels approximatifs non assumés.

## M3 — Tester un modèle visuel/ temporel et son transfert PS5

**Dépendance : M2 concluant.** Données d'entraînement et test distinctes.

- [ ] Collecter ensuite plusieurs passages variés : intérieur/centre/extérieur,
  vitesses/angles différents, corrections et excursions. Ne pas entraîner uniquement
  sur des tours optimaux qui incitent à mémoriser une trajectoire habituelle.
- [ ] Première portée : une voiture, une caméra, Spa. Conserver des sessions entières
  hors entraînement ; ne pas séparer aléatoirement des frames voisines entre train/test.
- [ ] Comparer une baseline simple, une prédiction depuis une image et une courte
  séquence. Le contexte avant/après est permis hors ligne et doit être annoncé.
  Aucun nom d'architecture ou coût de calcul n'est figé avant examen des données.
- [ ] Mesurer erreur médiane/P95, biais par zone, continuité, échecs/hors piste et
  abstentions. Si `s` aide le modèle, tester avec le `s` imparfait disponible sur PS5,
  pas uniquement le `s` vrai PC. Vérifier que l'image apporte plus qu'une ligne mémorisée.
- [ ] Éprouver caméra/FOV, rendu et compression proches de PS5, puis le vrai domaine
  PS5. La précision PC ne prouve pas celle sur console. Prévoir une référence spatiale
  indépendante/positions contrôlées pour prétendre à une erreur PS5 en mètres ; une
  simple inspection de trajectoire plausible n'est qu'un contrôle qualitatif.

**Sortie :** prototype d'estimation `d` et éventuellement orientation, accompagné de
son erreur mesurée et de ses limites. **Acceptation :** gain démontré face à la baseline
et précision compatible avec le placement à distinguer. Sans preuve métrique PS5,
la sortie reste une estimation à précision non établie ; ne pas dessiner une ligne exacte.

## M4 — Assembler la perception globale et spatiale

- [ ] Étendre M1 à la session entière : même index de zones/tours, actions et qualité.
  Le pilote peut fournir une nouvelle séance naturelle d'environ20min pour disposer
  de situations plus représentatives ; elle n'est pas requise pour commencer M1.
- [ ] Relier chaque mesure et estimation spatiale à son temps, source et domaine de
  validité. Une direction HUD non qualifiée n'est pas un angle réel des roues.
- [ ] Afficher la trajectoire estimée seulement là où M3 la soutient, avec incertitude,
  trous et source géométrique. Ailleurs, garder les images et l'inconnu ; ne pas boucher
  le parcours pour produire un dessin continu. Le lecteur doit voir les limitations.
- [ ] Présenter globalement toutes les zones et fournir les détails temporels associés.
  Une sélection réduite pour le modèle est annoncée ; elle ne vaut pas vision exhaustive.
- [ ] Garder distinctes : données PC qui servent de labels, passages personnels qui
  décrivent le pilote, référence expérimentée qui explique une technique. Cette dernière
  peut être ajoutée pour l'analyse par GPT ; elle n'est ni la définition de `d`, ni
  une nécessité pour constituer des labels PC de positions variées.

**Sortie :** dossier multimodal de perception complet dans son périmètre déclaré,
réutilisant l'exporteur existant. Pas d'outil web hébergé ni d'appel API GPT implicite.
Si M3 échoue, M1 reste un livrable temporel partiel : ne pas annoncer que la capacité
spatiale demandée est livrée ou la remettre indéfiniment hors périmètre sans décision.

## M5 — Tester les yeux de l'IA avant de juger le coaching

- [ ] Fournir les seules pièces du dossier au modèle et contrôler ce qu'il a pu lire.
- [ ] Lui demander d'abord des reconstructions factuelles : ordre des actions avant
  une excursion, placement et évolution dans une zone, différences entre passages,
  situations similaires ailleurs et inconnues. Vérifier les réponses sur la source.
- [ ] S'il manque une transition ou une zone, améliorer couverture, granularité ou
  représentation ; ne pas remplacer le défaut perceptif par un meilleur prompt de conseil.
- [ ] Une fois cette lecture fidèle, laisser l'IA analyser les habitudes globales et
  proposer l'entraînement. Examiner les erreurs de raisonnement séparément des erreurs
  de perception. Aucun modèle n'est censé rendre une cause physique certaine avec des
  observations insuffisantes.

**Acceptation :** le modèle reconstruit correctement les situations examinées, cite
les preuves, compare les cas pertinents et reconnaît ses inconnues. La séance d'entraînement
ultérieure évalue l'utilité du coaching, pas la fidélité des données à elle seule.

## Discipline et état

- [x] Extraction automatique complète et premier export local livrés (run-024/run-026).
- [x] Clarification du rôle perceptif, couverture temporelle et intérêt de `d`.
- [x] M1 : prototype temporel à l’échelle d’un tour complet livré dans run-027.
- [ ] M1 suite : complément vidéo du test externe, extension à d’autres tours et fenêtres.
- [ ] M2 : échantillon PC vidéo+télémétrie avec vérité spatiale démontrée.
- [ ] M3 : prototype modèle et évaluation de transfert.
- [ ] M4 : dossier global multimodal avec placement qualifié.
- [ ] M5 : essai réel de lecture factuelle, puis analyse par l'IA.

Les modules M1 sont livrés et testés. Aucun dataset PC ou modèle spatial n’est
encore développé. Tests/lectures proportionnés selon AGENTS.md. Sources privées, anciens labels,
configurations et sorties préservés ; pas de replay OCR pour une retouche de rapport.
Le premier export demeure reproductible via son contrat, sans le confondre avec la finalité.

**Prochaine action : compléter le cas run-028 par le clip source342–351 s avec audio,
puis comparer les confirmations/corrections de l'IA à son premier retour conservé.
Étendre ensuite la couverture à plusieurs passages avant de parler d'habitudes. Pour M2,
confirmer logiciel/service ACC sur Mac et durée du créneau avant de préparer le
logger adapté ; ne pas consommer le créneau pour découvrir ces contraintes.**
