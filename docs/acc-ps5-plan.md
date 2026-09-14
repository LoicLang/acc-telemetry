---
summary: local session-perception objective with temporal coverage and PC-supervised spatial feasibility
read_when:
  - deciding priorities after the first export
  - distinguishing perception, AI coaching and spatial validation
---

# Direction active — construire les yeux de l'IA

Clarification du14 septembre2026 : notre logiciel fournit une représentation fidèle
et temporelle de la session entière. L'IA analyse les faiblesses globales et propose
l'entraînement. Le premier `session_coaching.md` run-026 est livré ; il est une brique,
pas la finalité. [Plan actif unique](plans/2026-09-13-first-gpt-export.md).

## Capacités à construire

1. Couverture de tous les tours/zones, avec actions neutres et contexte, sans choisir
   uniquement les erreurs supposées. Scène et commandes synchronisées.
2. Fenêtres temporelles adaptant leur granularité aux transitions à observer ; trois
   photos de placement ne suffisent pas à expliquer une action rapide.
3. Position latérale `d` et orientation, lorsque leur estimation est démontrée. Étudier
   explicitement vidéo PC+télémétrie synchronisées comme source de labels d'entraînement.
4. Dossier multimodal réellement lisible par l'IA, avec incertitudes et couverture déclarée.
5. Test de reconstruction factuelle par le modèle, avant évaluation de son coaching.

`d` n'est plus exclu comme simple raffinement. PC ne signifie pas que tous les labels
sont disponibles directement : position, géométrie, point de voiture, unités et horloges
sont à établir. L'entraînement et le transfert PC→PS5 demandent une preuve distincte.
Une ligne plausible n'est pas une position métrique vérifiée. Le `s` existant reste
une progression estimée ; `s_odometry`, `s_visual`, `s_fused` ne décrivent pas seuls
la trajectoire latérale. Le lecteur conserve qualité, trous et anomalies.

Les passages imparfaits apportent des observations utiles. Les cas normaux et réussis
doivent aussi être couverts pour donner au modèle une vue représentative. Une référence
professionnelle sert à expliquer une technique ; elle ne définit ni `d` ni les labels
PC et n'est pas nécessaire à la première preuve de perception temporelle.

## Frontière et exécution

Gate A reste FAIL, `coaching_eligible=false`. L'expérimentation ne certifie pas le moteur,
les nouveaux labels ou le coaching. Aucune ancienne preuve ne qualifie automatiquement
le modèle spatial. La validation requise dépend de la capacité annoncée.

Tout reste local ; pas de service web hébergé, d'achat ou d'appel API GPT implicite.
Le présent travail est la consolidation du plan, pas son implémentation. Commencer M1
sur la vidéo existante ; préparer M2 lorsque l'accès PC et les données sont confirmés.
[Current status](current-status.md) donne le point de reprise et les fichiers réels.
