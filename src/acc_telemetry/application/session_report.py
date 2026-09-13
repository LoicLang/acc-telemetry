"""Assemble a standalone French evidence report without OCR or a model call."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from acc_telemetry.analysis.session_summary import summarize
from acc_telemetry.application.session_artifacts import check_destination, read_session_artifacts


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def render_report(session, case, summary, *, case_sha256, manifest_sha256):
    m = session.manifest
    by_frame = {s.frame: s for s in session.samples}
    origin = m['clip_origin']['start_s']
    def time(f):
        return by_frame[f].time_s + origin
    def span(frames):
        if frames is None:
            return 'indisponible'
        return f'{time(frames[0]):.3f}–{time(frames[1]):.3f} s (frames {frames[0]}–{frames[1]})'
    lines = [
        '# Session coaching — faits pour GPT', '',
        '**Export expérimental, portée limitée. Gate A : FAIL. `coaching_eligible=false`.**',
        'Autorisé avant qualification générale ; aucune validation du coaching automatique. '
        'Les seuils et les artefacts sources restent inchangés.', '',
        '## 1. Contexte', '', case['context'], '',
        f"Source : `{Path(m['source']['path']).name}`, {m['source']['size_bytes']} octets. "
        f"SHA-256 : `{m['source']['sha256']}`.",
        'Tous les temps ci-dessous désignent cette source vidéo, pas une origine supposée '
        'dans un enregistrement plus long. Frames indexées à partir de zéro.', '',
        f"Question documentée : {case['question']}", '',
        '## 2. Session entière et limites de couverture', '',
        f"{len(session.samples)} échantillons relus avec vérification des hashes/enveloppes telemetry-v2. "
        f"Premier/dernier instant : {time(session.samples[0].frame):.3f} / "
        f"{time(session.samples[-1].frame):.3f} s ; étendue entre instants "
        f"{session.samples[-1].time_s-session.samples[0].time_s:.3f} s.",
        f"Format attesté dans le manifeste : {m['video_info']['width']}×{m['video_info']['height']}, "
        f"{m['timebase']['fps']:g} fps CFR ; contrôle temporel `{m['timebase']['status']}`. "
        'La durée de conteneur peut inclure une queue sans frame présentée ; elle ne sert pas aux calculs.', '',
        '| Champ | Valeurs disponibles | Portée |', '| --- | --- | --- |']
    for field, count in summary['coverage'].items():
        lines.append(f'| {field} | {count}/{len(session.samples)} ({100*count/len(session.samples):.2f} %) '
                     '| Disponibilité, pas exactitude ni visibilité validée |')
    transitions = m['lap_transitions']
    lines += ['', f'{len(transitions)} transitions du compteur HUD : ' + '; '.join(
        f"{t['from_lap']}→{t['to_lap']} à {t['time']+origin:.3f} s (confirmation)" for t in transitions) + '.',
        'Ce sont des transitions du compteur, pas des franchissements physiques certifiés ; '
        'les bords du clip sont des portions de tours. Aucun meilleur tour ni tour légal n’est déduit.', '',
        case['session_evidence'], '', case['exclusions'], '',
        '## 3. Passages et repères physiques communs', '',
        f"**A — entrée :** {case['landmarks']['entry']}", '',
        f"**B — sortie :** {case['landmarks']['exit']}", '', case['landmark_limits'], '',
        '| Passage | Fenêtre conservée, approche incluse | Repère A | Repère B | Issue et comparabilité |',
        '| --- | --- | --- | --- | --- |']
    for p in case['passages']:
        bounds = [span(p[key]) if p[key] is not None else
                  'indisponible : ' + p[key + '_missing_reason'] for key in ('entry', 'exit')]
        lines.append('| ' + ' | '.join(map(_cell, [p['id'], span(p['window_frames']), *bounds,
            p['outcome'] + ' ' + p['comparison_limit']])) + ' |')
    lines += ['', '## 4. Faits calculés et lectures ponctuelles', '',
        '| Preuve | Temps A→B, s | Méthode, champs requis, qualité et limite |', '| --- | --- | --- |']
    for p, duration in zip(case['passages'], summary['durations']):
        value = duration['range_s']
        label = 'indisponible' if value is None else f'{value[0]:.3f}–{value[1]:.3f}'
        lines.append(f"| D-{p['id']} | {label} | Différence des bornes temporelles revues "
                     '(B bas − A haut ; B haut − A bas), frames/temps + scène. '
                     'Fenêtres visuelles approximatives, pas chrono de secteur homologué. '
                     'Aucune mesure de pédale requise. |')
    lines += ['', 'Ces intervalles décrivent le temps écoulé entre deux repères visibles, '
        'y compris les perturbations du trajet. Ne pas les transformer en gain accessible, '
        'en distance, en classement de technique ou en statistique de passages propres.', '',
        '| Preuve / situation | Temps source / frame | Vitesse admise, km/h | Extraction / qualité / raisons conservées | Revue locale et limite |',
        '| --- | --- | --- | --- | --- |']
    for s in summary['speeds']:
        admitted = 'indisponible' if s['admitted_kmh'] is None else f"{s['admitted_kmh']:g}"
        extracted = 'null' if s['extracted_kmh'] is None else f"{s['extracted_kmh']:g}"
        manual = 'non renseigné' if s['hud_kmh'] is None else f"{s['hud_kmh']:g} km/h"
        lines.append('| ' + ' | '.join(map(_cell, [s['id'] + ' — ' + s['context'],
            f"{s['time_s']:.3f} s / {s['frame']}", admitted,
            f"{extracted} / {s['quality']} / {', '.join(s['reasons']) or 'aucune'}",
            f"HUD lu : {manual}. {s['reason']}"])) + ' |')
    lines += ['', 'Une valeur n’est admise ici que si elle est fraîche (`observed`) et identique '
        'à la lecture visuelle locale. `null`, discordance ou valeur tenue restent indisponibles. '
        'Les raisons originales restent visibles ; cette revue ponctuelle ne qualifie aucune courbe. '
        'Résolution de l’affichage : 1 km/h ; erreur physique du jeu non évaluée. '
        'Les lectures aux bornes ne sont ni les extrema de la fenêtre, ni une vitesse exacte '
        'au franchissement. Aucun minimum continu ou durée de frein/gaz n’est calculé.', '',
        '## 5. Descriptions visuelles revues', '',
        f"Revue du {case['review']['date']} par {case['review']['author']} "
        f"({case['review']['type']}). {case['review']['limits']}", '']
    for p in case['passages']:
        frames = p['reviewed_frames']
        lines.append(f"- {p['id']} : {len(frames)} images examinées de {time(frames[0]):.3f} "
                     f"à {time(frames[-1]):.3f} s ; espacement maximal déclaré entre A et B : "
                     f"{p['max_review_gap_s']:g} s.")
    lines.append('')
    for v in case['visuals']:
        times = ', '.join(f'{time(f):.3f}' for f in v['frames'])
        lines.append(f"- **{v['id']}**, {times} s : {v['text']}")
    lines += ['', 'Ces descriptions sont les observations du relecteur, pas des images que GPT '
        'pourrait examiner dans ce fichier. Elles ne permettent pas de vérifier les quatre roues, '
        'une trajectoire idéale, l’angle de braquage réel, les interventions TC/ABS ou une causalité.', '',
        '## 6. Demande à GPT', '',
        'À partir de ce fichier seul, propose une priorité de travail limitée à cette zone, '
        'deux exercices complémentaires si les faits les justifient, puis une séance structurée '
        'avec critères de réussite observables. Cite les IDs des faits et descriptions utilisés. '
        'Sépare observation, hypothèse, cause alternative et information manquante. '
        'N’invente aucun réglage, repère, pourcentage de commande idéal, vitesse cible ou visibilité. '
        'Les critères numériques d’un exercice que tu proposes doivent être présentés comme un '
        'protocole à tester, jamais comme des seuils déduits de cette session. '
        'Une comparaison personnelle ne représente pas une référence professionnelle. '
        'Si une cause ne peut être départagée, indique quelle observation ciblée le permettrait.', '',
        'Provenance reproductible (aucun fichier externe nécessaire à la lecture) :', '',
        f'- Fiche de sélection SHA-256 : `{case_sha256}`.',
        f'- Manifeste relu SHA-256 : `{manifest_sha256}`.',
        *[f'- {name} SHA-256 : `{digest}`.' for name, digest in m['files'].items()],
        '- Export sans OCR et sans appel GPT. La vérification dans une nouvelle conversation '
        'GPT n’est pas réalisée par ce générateur.', '']
    return '\n'.join(lines)


def write_report(session_path, case_path, output):
    session_path, case_path = Path(session_path), Path(case_path)
    session = read_session_artifacts(session_path)
    if session.manifest.get('schema_version') != 'telemetry-v2':
        raise ValueError('report requires telemetry-v2 artifacts')
    m = session.manifest
    if (m['timebase']['status'] != 'pass' or m['timebase']['fps'] != 60
            or (m['video_info']['width'], m['video_info']['height']) != (1920, 1080)):
        raise ValueError('report requires existing native 1920x1080 / 60 fps CFR proof')
    target = check_destination(output, session.manifest['source']['path'])
    # Protect evidence directories too, even for a new filename inside one.
    if target.is_relative_to(session_path.resolve()):
        raise ValueError('report cannot be written inside session artifacts')
    case_bytes = case_path.read_bytes()
    case = json.loads(case_bytes)
    manifest_sha256 = sha256(session_path / 'manifest.json')
    if case['manifest_sha256'] != manifest_sha256:
        raise ValueError('case does not match session manifest')
    summary = summarize(session.samples, session.manifest, case)
    # Bind all reviewed frames to durable image evidence; do not silently trust a
    # sheet from another source or an edited set of local screenshots.
    frames = {f for p in case['passages'] for f in p['reviewed_frames']}
    if set(case['frame_evidence']) != {str(f) for f in frames}:
        raise ValueError('image evidence must cover exactly the reviewed frames')
    for evidence in case['frame_evidence'].values():
        path = case_path.parent / evidence['path']
        if sha256(path) != evidence['sha256']:
            raise ValueError(f'image evidence integrity mismatch: {evidence["path"]}')
    for evidence in case['supporting_evidence'].values():
        if sha256(case_path.parent / evidence['path']) != evidence['sha256']:
            raise ValueError(f'supporting evidence integrity mismatch: {evidence["path"]}')
    report = render_report(session, case, summary,
        case_sha256=hashlib.sha256(case_bytes).hexdigest(),
        manifest_sha256=manifest_sha256)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Prepare the complete file beside its destination, then atomically link with
    # no replacement. A concurrent writer cannot be clobbered.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                         prefix='.session-report-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(report)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
