---
summary: approved experimental single-file session report contract and fact-level evidence limits
read_when:
  - implementing or reviewing the first session_coaching.md exporter
  - deciding whether a fact or passage is usable in the experimental report
---

# Premier fichier pour GPT — contrat actif

Décision du propriétaire,13 septembre2026 : produire localement **un seul fichier
`session_coaching.md`** à partir d'une vraie session. L'export technique existe ; le
fichier autonome destiné à GPT est livré dans run-026. Le plan d'exécution est
[le plan en quatre lots](../plans/2026-09-13-first-gpt-export.md).

## Statut et frontière de confiance

Le rapport porte le statut **expérimental, portée limitée**. Gate A reste en échec,
les seuils restent inchangés et `coaching_eligible=false` n'est jamais forcé à vrai.
Ce premier export est explicitement autorisé avant la qualification générale :
sa validité dépend des faits qu'il utilise et de leurs limites, pas d'une certification
inventée de toute la session. Les capacités de coaching validé restent bloquées.

Une lecture `observed` est fraîche, pas forcément correcte ou visuellement vérifiée.
Les raisons de qualité accompagnent chaque choix d'utilisation. Une annotation
ponctuelle qualifie son point ; elle ne prouve pas toute une courbe. Un calcul de durée
ou d'épisode nécessite une revue de l'intervalle pertinent. Les observations visuelles
textuelles doivent être revues, datées et attribuées ; sinon elles restent inconnues.
Ne pas modifier rétroactivement les annotations ou statuts des artefacts sources.

## Contenu obligatoire du fichier

1. **Contexte.** ACC/PS5, circuit/zone, voiture et variante, conditions, matériel,
   objectif et ressenti si disponibles. Inconnu reste inconnu ; ne pas importer les
   informations d'une autre capture. Le statut expérimental apparaît dès le début.
2. **Session entière.** Durée traitée, tours/transitions, couverture des signaux,
   zones contrôlées, exclusions et raisons. Ne pas appeler couverture « exactitude ».
3. **Passages.** Deux ou trois passages d'une zone clairement nommée, avec des repères
   physiques communs revus. Conserver l'approche d'un incident et distinguer cet
   incident des passages utilisés pour une comparaison. Un tour invalide ne disqualifie
   pas automatiquement toutes ses portions.
4. **Faits et mesures.** Tableau compact avec valeur/unité, temps source, identifiant
   de preuve, méthode, champ requis, qualité, incertitude et limite. Quelques séquences
   numériques pertinentes sont possibles ; pas de copie de la session entière à 60 Hz.
5. **Descriptions visuelles vérifiées.** Ce qui a été vu, à quel moment, par qui et
   avec quelles limites. Un chemin local n'est pas une image accessible à GPT. Ce
   fichier texte ne permet pas au modèle de vérifier visuellement la trajectoire.
6. **Questions et consigne à GPT.** Une priorité de travail, deux exercices
   complémentaires si les faits les permettent et une séance structurée, avec critères
   de réussite. Demander de distinguer observation, hypothèse, cause alternative et
   information manquante. Le générateur ne rédige pas le coaching lui-même.

Le texte doit suffire sans dépôt, localhost, ancien chat ou image externe indispensable.
Les noms/hashes/temps peuvent identifier les preuves ; aucun chemin absolu personnel
n'est une dépendance de lecture. Les données brutes et médias restent disponibles
localement pour l'audit, sans obligation d'envoi. Le périmètre d'une seule zone est
annoncé ; ne pas prétendre diagnostiquer tous les virages ou la conduite générale.

## Calculs admissibles pour la première livraison

Commencer par les temps entre repères communs et les vitesses à ces repères lorsqu'ils
sont contrôlés. Ajouter freinage/relâchement/reprise seulement si ces faits répondent
à une question précise et si leurs bornes/intervalle sont revus. Pas d'obligation
d'implémenter sept métriques ou un moteur général d'événements.

- Garder les nulls, unités, qualités, raisons et ordre temporel.
- Un trou pouvant cacher un minimum empêche de publier ce minimum comme comparable.
- Un début d'événement absent/ambigu reste indéterminé ; aucune borne inventée.
- Ne pas aligner les pics de frein ou les vitesses minimales : utiliser les repères physiques.
- Ne pas supposer `s` exact, convertir un délai en mètres ou inférer une trajectoire idéale.
- Le plein gaz proche de 94% et les résidus ne deviennent pas des erreurs du pilote.
- Ne pas attribuer automatiquement les blips au pilote ; ne pas inférer TC/ABS,
  angle volant ou causalité certaine à partir des seules pédales.

Une comparaison personnelle peut soutenir un exercice de régularité comme hypothèse
de travail. Elle ne définit pas une technique optimale. La référence professionnelle,
les images appariées et un diagnostic plus fin seront ajoutés ultérieurement si la
question de coaching l'exige ; ils ne bloquent pas ce premier export expérimental.

## Architecture et acceptation

L'assembleur relit `telemetry-v2` via `read_session_artifacts()` et une fiche locale
de passages avec source, repères, bornes, auteur de revue et exclusions. Il ne relance
pas `TelemetryPipeline`, ne crée pas un nouveau format brut et n'appelle pas GPT.
La sélection peut être manuelle dans cette première version.

Le livrable est **le fichier réel et la commande qui le reproduit**, pas un schéma,
un faux exemple ou un script non exécuté. Sortie nouvelle, sans écrasement et sans
modification du moteur sauf défaut démontré affectant une donnée nécessaire.

Pour la livraison autorisée le 13 septembre, une relecture limitée au fichier et le
contrôle des nombres/preuves/incertitudes sont effectués. L’essai dans une nouvelle
conversation sans historique est explicitement distingué : il reste à réaliser par le
pilote. Une réponse séduisante mais non étayée échoue. Compléter seulement la pièce qui manque puis réessayer. La séance
suivante et le gain de performance ne sont pas des conditions rétroactives de livraison.

## Fiche locale implémentée

`--case` lit un JSON `session-coaching-case-v1`, sans créer de nouvelles observations
brutes. La fiche personnelle de run-026 est l’entrée reproductible livrée localement.

- `source_sha256`, `source_size_bytes`, `manifest_sha256`, `artifact_files` lient la
  sélection aux artefacts exacts ; `gate_a=FAIL`, `coaching_eligible=false` sont requis.
- `review` contient date ISO, auteur, type et limites ; `context`, `question`,
  `session_evidence`, `exclusions`, `landmark_limits` sont du texte revu, pas inféré.
- `landmarks.entry/exit` définissent les objets communs. Chaque élément de `passages`
  porte ID, `window_frames`, bornes `entry/exit`, `reviewed_frames` ordonnées,
  `max_review_gap_s` positif validé, issue et limite de comparaison. Une borne absente
  exige `entry_missing_reason` ou `exit_missing_reason` et interdit sa durée.
- `speed_reviews` porte ID, frame, `hud_kmh` (nullable), contexte et raison ; seuls
  les points `observed` égaux à cette lecture sont admis. `visuals` porte ID, frames,
  description. Le code vérifie la portée déclarée, pas la véracité du jugement visuel.
- `frame_evidence` associe chaque frame revue à un fichier image et son SHA-256 ;
  `supporting_evidence` fait de même pour les validations réutilisées. Les chemins se
  résolvent depuis la fiche. Ces médias servent à l’audit local, pas à la lecture GPT.

L’export refuse une sortie existante, la source, `raw/` et le dossier d’artefacts.
Les images doivent rester disponibles pour reproduire le fichier ; aucun décodage
ni OCR n’a lieu dans l’exporteur. Une nouvelle sélection nécessite une vraie revue,
pas simplement l’ajout d’IDs ou de drapeaux dans le JSON.
