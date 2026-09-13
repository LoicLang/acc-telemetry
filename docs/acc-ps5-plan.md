---
summary: current product priority and explicit boundary between the first experimental export and general reliability qualification
read_when:
  - deciding product priorities or prerequisite gates
  - assessing whether proposed work belongs to the first GPT export
---

# Road to Verstappen — direction active

Décision du 13 septembre2026 : livrer **`session_coaching.md`**, fichier autonome issu
d'une vraie session locale, permettant à GPT de proposer une priorité et des exercices
fondés sur les faits disponibles. Suivre [le seul plan actif](plans/2026-09-13-first-gpt-export.md)
et [son contrat](specs/2026-09-13-session-coaching-report.md).

## Ce qui existe et ce qui manque

L'extraction automatique run-024 est réalisée :29 402 images en 1080p60 CFR,99,65% de
vitesses disponibles, pédales extraites sur toutes les images.21 points contrôlés ne
prouvent pas la qualité globale ; biais de pédales, trous et anomalies restent connus.
Les artefacts et leur intégrité permettent de travailler sans relancer la vidéo.

Livrés dans run-026 : sélection source-bound de trois passages, repères A/B revus,
22 lectures ponctuelles concordantes, trois temps de transit approximatifs et le vrai
`session_coaching.md` produit par l’assembleur local. Relecture utile par le même assistant
effectuée ; essai dans une nouvelle conversation GPT et entraînement réel non réalisés.
Pas de nouvelle application web ou pipeline de coaching complet.

## Changement explicite de périmètre

**Gate A reste FAIL ; `coaching_eligible=false`.** Ses six contrôles, ses seuils et les
preuves historiques ne changent pas. La qualification indépendante générale et le
coaching automatique validé restent **blocked**.

En revanche, le propriétaire autorise le **rapport expérimental limité avant Gate A**.
L'ancienne interdiction de tout export avant qualification, référence professionnelle
et dossier à sept métriques est remplacée pour ce jalon uniquement. La qualité est
traitée au niveau des faits utilisés : valeur/intervalle contrôlé, raison, incertitude,
exclusion précise. Aucun passage non vérifié ne devient fiable par simple étiquette.

## Ordre de travail

1. Réutiliser run-024, confirmer le contexte et sélectionner deux/trois passages.
2. Contrôler et calculer les faits nécessaires, sans métriques imposées.
3. Produire localement le fichier autonome avec une commande reproductible.
4. Vérifier sa lecture utile par GPT ; compléter les seules pièces manquantes et livrer.

Les **passages imparfaits** sont conservés avec leurs limites ; un tour invalide ne
supprime pas toutes ses portions utiles. Une référence personnelle sert à la régularité,
pas à définir une trajectoire idéale. Le `s` estimé aide au repérage, sans alignement
spatial supposé exact ni conversion en mètres. `d` latéral reste hors périmètre.

## Après le premier fichier

Selon les limites réellement rencontrées : ajouter une référence professionnelle
expliquée, des preuves visuelles jointes et des métriques supplémentaires ; poursuivre
la qualification indépendante et tester l'effet d'un exercice à la séance suivante.
Ces étapes ne sont pas des conditions rétroactives pour livrer le premier fichier.
Ne pas relancer les anciennes campagnes de compteur ou la recherche replays.

Les résultats et décisions passés sont dans [l'archive](archive/README.md), hors
instructions actives. [Current status](current-status.md) porte les chemins vérifiés,
les blocages concrets et une seule prochaine action.
