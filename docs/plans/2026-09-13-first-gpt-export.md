---
summary: sole active four-lot execution plan for a real experimental session_coaching.md from existing run-024 artifacts
read_when:
  - resuming implementation of the first GPT export
  - checking what must be delivered and when to stop
---

# Premier export GPT — quatre lots

**Plan adopté le 13 septembre2026**, d'après l'analyse externe
`PLAN_PREMIER_EXPORT_GPT.md` fournie par le propriétaire. Cette version dans le dépôt
fait autorité ; aucune copie dans Downloads ou ancien chat n'est nécessaire pour agir.
Spécification : [contrat du fichier](../specs/2026-09-13-session-coaching-report.md).
État/chemins vérifiés : [current-status](../current-status.md).

## Décision de périmètre, déjà actée

Livrer un fichier autonome **`session_coaching.md` d'une vraie session existante**.
Le rapport prépare des faits ; GPT produit les hypothèses, exercices et séance.
Le propriétaire autorise ce premier export expérimental sans attendre tout Gate A.
C'est un changement explicite par rapport aux anciens plans supprimés, pas leur
exécution inchangée. Gate A reste FAIL, les seuils et `coaching_eligible=false` restent
intacts. La qualification générale et le coaching certifié ne sont pas déclarés réussis.

Aucune nouvelle phase de planification ni référence professionnelle obligatoire.
Tout est local, sans API GPT, site ou développement web. Aucun sous-agent, nouvelle
revue exhaustive du compteur ou recherche générale de seuils. L’implémentation est
livrée dans run-026 le 13 septembre : lots 1–3 terminés, relecture locale du lot 4 faite.
L’essai dans une nouvelle conversation GPT reste distinct et non réalisé.

## Lot 1 — Figer l'entrée, le contexte et les passages

- [x] Recharger `data/lab/coaching-reliability/run-024/processed/crash-session/` avec
  `read_session_artifacts()`. Vérifier les hashes/enveloppes et 29402 samples ; conserver
  une preuve d'intégrité dans un nouveau dossier local. Si une entrée manque, indiquer
  le fichier exact ; ne pas inventer un chemin ni relancer l'OCR par défaut.
- [x] Utiliser la source du manifeste. Confirmer uniquement ce que les pièces permettent :
  famille McLaren 720S GT3, zone candidate fin des Combes/Malmedy. Variante, matériel,
  conditions et repères non confirmés restent inconnus. Ne pas substituer BMW/Bruxelles.
- [x] Sélectionner deux ou trois passages complets d'une même zone ; revoir les mêmes
  repères d'entrée/sortie depuis la scène, pas depuis les pics ou un `s` supposé exact.
  Conserver l'incident avec son approche, en réutilisant le complément run-025.
- [x] Écrire une fiche locale source-bound : ID/hash source, contexte, IDs de passages,
  bornes frame/temps, définition illustrable des repères, auteur/type de revue,
  incertitude, portions valides et exclusions. Une sélection manuelle suffit.
  Ne pas rejeter tout un tour parce qu'une autre portion est invalide.

**Sortie :** entrée figée + fiche de sélection vérifiée. Si aucun comparateur pertinent
n'existe, nommer la pièce qui manque au lieu de fabriquer un cas ou d'ouvrir une campagne.

## Lot 2 — Calculer seulement les faits nécessaires

- [x] Définir la question soutenue par la comparaison : régularité, vitesse à un repère,
  ordre d'actions ou récupération après incident. Un sujet étayé suffit au premier fichier.
- [x] Calculer les temps entre repères communs et vitesses à ces repères, lorsque les
  observations requises sont effectivement contrôlées. Garder unités, source/temps,
  méthode, incertitude et identifiants de preuve.
- [x] Ajouter freinage/relâchement/reprise seulement si utile et localement vérifié.
  Revoir l'intervalle d'une durée/épisode ; deux points exacts ne suffisent pas.
  Un minimum possiblement caché par un trou ou un événement ambigu reste indisponible.
- [x] Préserver les mesures, les nulls et leurs raisons. Les éventuelles nouvelles
  bornes revues sont des annotations séparées, sans changer les anciens ledgers.
  `observed` avec `hud_visibility_unverified` ne devient pas automatiquement vérifié.
- [x] Rédiger les observations visuelles textuelles réellement examinées, avec temps,
  auteur/type de revue et limites. Ne pas demander à GPT de voir une vidéo par son chemin.

**Sortie :** faits locaux reproductibles et au moins un sujet d'entraînement fondé,
ou la pièce précise qui manque. Pas de sept métriques imposées, diagnostic causal
certain, trajectoire idéale, `d` en mètres, TC/ABS ou angle volant déduits.

## Lot 3 — Assembler le fichier réel avec une commande locale

- [x] Créer le minimum de calcul/assemblage/adaptation nécessaire. Découpage implémenté :

| Module sous `src/acc_telemetry/` | Responsabilité |
| --- | --- |
| `analysis/session_summary.py` | Faits, exclusions et comparaisons retenus ; fonctions pures |
| `application/session_report.py` | Lire artefacts/fiche et assembler le texte sans OCR |
| `adapters/session_report.py` | Arguments locaux entrée/sortie et erreurs compréhensibles |

Ces fichiers sont implémentés. Réutiliser `application/session_artifacts.py` et
`domain/telemetry.py`. Ne pas refondre l'architecture ; les adaptateurs ne portent
pas de logique métier et l'assembleur n'appelle pas `TelemetryPipeline` ou GPT.

- [x] Générer les six sections du contrat : contexte, session entière, passages,
  faits/mesures, descriptions visuelles revues, questions/consigne GPT.
- [x] Annoncer l'expérimentation, le périmètre et les limites dès le début. Distinguer
  couverture extraite et portions examinées, contrôle d'OCR et référence de conduite.
- [x] Refuser source/raw/sortie existante ; préserver les données et publier un fichier
  complet. Aucun chemin local absolu ne doit être nécessaire à la lecture par GPT.
- [x] Exécuter la commande sur les vrais artefacts et livrer le fichier, pas seulement
  le code ou un exemple fictif. Conserver la commande exacte et les empreintes localement.

Commande **implémentée et exécutée** (sortie nouvelle à chaque lancement) :

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.session_report \
  --session data/lab/coaching-reliability/run-024/processed/crash-session \
  --case data/lab/coaching-reliability/run-026/interim/case.json \
  --output data/lab/coaching-reliability/run-026/reports/reproduction-02/session_coaching.md
```

**Sortie :** `session_coaching.md` réel, autonome et reproductible.

## Lot 4 — Tester la lecture utile puis arrêter ce jalon

- [x] Relire le fichier en se limitant à son contenu ; contrôler les nombres, unités,
  preuves, inconnues et descriptions. Même assistant/tâche, pas une lecture aveugle.
- [ ] Le pilote le transmet à GPT dans une nouvelle conversation. Demander une priorité,
  deux exercices complémentaires si étayés et une séance structurée, avec critères
  de réussite. Le générateur ne rédige pas ces exercices et n'envoie rien automatiquement.
- [ ] Vérifier que la réponse s'appuie sur des faits identifiables, distingue hypothèses
  et causes alternatives et n'invente pas les informations manquantes. Une réponse
  générique ou seulement convaincante ne suffit pas.
- [x] Relecture locale : pas de pièce manquante bloquant un exercice de reproductibilité.
  Le transit A→B ne suffit pas : l’issue après B est incluse. Diagnostic causal non résolu.
- [x] Livrer le fichier et un verdict de revue. L'efficacité à la séance suivante,
  la référence professionnelle et la qualification indépendante générale viennent après.

**Arrêt :** un vrai fichier autonome permet un exercice étayé dans une conversation
sans historique. Tant que l'essai réel n'a pas eu lieu, consigner ce qui est testé et
ce qui ne l'est pas ; ne pas prétendre avoir obtenu une réponse indépendante.

## Protections et discipline d'exécution

- Vérifications proportionnées selon `AGENTS.md` : tests ciblés pour les calculs,
  absences/ambiguïtés, unités/raisons et non-écrasement réellement affectés. Ajouter
  une régression utile ; suite complète si l'impact transversal ou le risque le justifie,
  pas systématiquement avant chaque commit. Une simple retouche de texte se relit.
- Réutiliser les annotations du compteur et les preuves run-024. Nouveau décodage seulement
  pour une revue locale nécessaire, après contrôle du 1080p60 CFR. Nouveau replay/OCR seulement
  si une correction démontrée du lecteur affecte les données utiles au fichier.
- Ne pas interpréter94% comme défaut de plein gaz ni les résidus comme action volontaire.
  Les blips peuvent être automatiques. Aucun lissage, visibilité inventée ou nouvelle
  cible de fiabilité pour rendre le rapport plus séduisant.
- Tout passage imparfait n'est pas inutile ; exclure précisément les faits non soutenus.
  Une référence personnelle permet d'étudier la régularité, pas une technique optimale.
- Conserver les sources/anciens résultats. Sorties personnelles ignorées sous
  `interim/`, `processed/` ou `reports/`. Mettre à jour cases et `current-status.md`,
  choisir les vérifications utiles, commit cohérent et push de la branche, sans merge.

## Résultat et décisions de livraison — 13 septembre

- Run-026 : 91 images revues, dont huit images d’approche run-025 réutilisées ; aucune
  nouvelle extraction OCR. Source, CFR et 29 402 samples contrôlés en réutilisant les
  preuves temporelles inchangées.
- Trois passages de la fin du premier droit à la fin du dernier droit ; approches et
  conséquences conservées. A/B sont des disparitions de vibreurs physiques encadrées
  par vues espacées de 0,5 s, avec erreur de perspective non quantifiée.
- D-P1 et D-P3 : 5,5–6,5 s ; D-P2 : 8–9 s. P2 reste un passage perturbé, P3 finit dans
  les graviers après B. Aucun classement de passages propres ni gain cible n’est déduit.
- 22 vitesses ponctuelles concordantes. Pédales et métriques continues exclues : elles
  n’ajoutent pas de fait localement suffisamment qualifié pour ce premier fichier.
- Générateur et commande livrés ; revue locale dans `run-026/reports/relecture.md`.
  La demande de livraison distingue cette revue du test GPT neuf : ce dernier n’est
  pas revendiqué et ne bloque pas la remise du fichier. Les deux cases restantes du
  lot 4 décrivent cet essai futur, pas un travail d’implémentation oublié.

**Prochaine action unique : le pilote joint le fichier run-026 `session_coaching.md`
à une nouvelle conversation GPT et demande la priorité, les exercices et la séance
selon la section 6 ; vérifier ensuite les preuves citées et les causes laissées ouvertes.**
