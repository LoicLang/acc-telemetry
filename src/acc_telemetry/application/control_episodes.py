"""Publish downstream HUD episodes from verified frozen artifacts; no video/OCR IO."""
import json
from pathlib import Path
import shutil
import tempfile

import yaml

from acc_telemetry.analysis.control_episodes import FIELDS, _valid, build_control_episodes
from acc_telemetry.analysis.perception import EventSettings
from acc_telemetry.domain.telemetry import QualityFlag as Q
from acc_telemetry.application.session_artifacts import (
    _publish, _sha, check_destination, read_session_artifacts,
)

ROOT = Path(__file__).resolve().parents[3]
LIMITS = [
    'HUD percentage readings, not physical pressure; no smoothing, rescaling or imputation.',
    'Full throttle may read about 94%; residuals and automatic downshift blips are not driver faults.',
    'Duration uses candidate onset/off times, not confirmation times; persistence is not measured accuracy.',
    'Observed peaks are not calibrated true maxima. Timing resolution does not establish physical latency.',
    'Terminal tail starts at the last exact observed maximum; it is not a qualified release onset or monotonic phase.',
    'Resumptions count successive confirmed threshold episodes only; internal modulation remains in the raw profile.',
    'Overlap intersects hysteresis states, including brief unconfirmed dips; physical simultaneity is not qualified.',
    'Every missing/invalid sample or absent frame splits evidence; truncated durations remain null.',
    's in source artifacts is a fraction, not metres; steering is an unqualified HUD candidate. Neither is used.',
]


def compare_annotations(payload, samples, labels):
    """Reuse provided point truth and visibility; never promote either to dense timing truth."""
    by_frame = {r.frame: r for r in samples}
    points = []
    for label in labels.get('frames', []):
        if not label.get('reviewed') or label['frame'] not in by_frame:
            continue
        row = by_frame[label['frame']]
        for field in FIELDS:
            expected = label.get(field)
            if expected is None:
                continue
            actual = getattr(row, field) if _valid(row, field) else None
            points.append(dict(frame=row.frame, time_s=row.time_s, field=field,
                               reference_pct=expected, observed_pct=actual,
                               error_pct=None if actual is None else actual - expected,
                               image_sha256=label.get('image_sha256'),
                               annotation_tolerance_pct=label.get('pedal_tolerance_pct')))
    comparisons = []
    event_types = {'first_visible_brake': 'brake_on', 'throttle_release': 'throttle_off'}
    for label in labels.get('passages', []):
        kind = event_types.get(label.get('event_type'))
        if not kind or not label.get('reviewed'):
            continue
        windows = [w for w in labels.get('evaluation_segments', [])
                   if w['frame_lo'] <= label['frame_lo'] <= label['frame_hi'] <= w['frame_hi']]
        candidates = [e for e in payload['events'] if e['type'] == kind and
                      any(w['frame_lo'] <= e['frame'] <= w['frame_hi'] for w in windows)]
        event = candidates[0] if len(candidates) == 1 else None
        comparisons.append(dict(annotation_id=label['id'], annotation_frames=[label['frame_lo'], label['frame_hi']],
                                window_ids=[w['id'] for w in windows], candidate=event,
                                candidate_minus_annotation_s=None if event is None else
                                [(event['frame'] - label['frame_hi']) / payload['fps'],
                                 (event['frame'] - label['frame_lo']) / payload['fps']],
                                status='unique_candidate_in_existing_window' if event else 'absent_or_ambiguous',
                                limitation='first visible/reported release and threshold crossing have different definitions'))
    for episode in payload['episodes']:
        lo, hi = episode['raw_profile']['start_frame'], episode['raw_profile']['end_frame_inclusive']
        episode['annotation_evidence'] = dict(
            numeric_frames=[p['frame'] for p in points if p['field'] == episode['field'] and lo <= p['frame'] <= hi],
            visibility_intersections=[dict(review_id=v.get('review_id'),
                                           start_time_s=max(v['start_s'], episode['observed_start']['time_s']),
                                           end_time_s=min(v['end_s'], episode['observed_end']['time_s']))
                                      for v in labels.get('visibility', []) if v.get('reviewed') and
                                      v['field'] == episode['field'].removesuffix('_pct') and
                                      max(v['start_s'], episode['observed_start']['time_s']) <
                                      min(v['end_s'], episode['observed_end']['time_s'])],
            duration_accuracy_s=None, peak_timing_accuracy_s=None, release_accuracy_s=None,
            limitation='sparse numeric points and visibility only; no complete episode timing ground truth')
    metrics = {}
    for field in FIELDS:
        selected = [p for p in points if p['field'] == field]
        errors = [abs(p['error_pct']) for p in selected if p['error_pct'] is not None]
        metrics[field] = dict(annotated_points=len(selected), available=len(errors),
                              mae_pct=sum(errors) / len(errors) if errors else None,
                              max_error_pct=max(errors) if errors else None)
    return dict(points=points, point_metrics=metrics, event_comparisons=comparisons,
                context=labels.get('context', []),
                scope='existing annotations reused; no new review, dense numerical truth or general qualification')


def write_control_episodes(session_path, output, *, annotations_path=None, settings_path=None):
    session_path = Path(session_path).resolve()
    settings_path = Path(settings_path or ROOT / 'config/perception.yaml').resolve()
    config = yaml.safe_load(settings_path.read_text())
    if not isinstance(config, dict) or set(config) != {'events'} or not isinstance(config['events'], dict):
        raise ValueError('expected events configuration')
    settings = EventSettings(**config['events'])
    inputs = {str(session_path / 'manifest.json'): _sha(session_path / 'manifest.json'),
              str(settings_path): _sha(settings_path)}
    session = read_session_artifacts(session_path)
    m = session.manifest
    if (m['timebase']['status'] != 'pass' or m['timebase']['fps'] != 60 or
            (m['video_info']['width'], m['video_info']['height']) != (1920, 1080)):
        raise ValueError('requires existing native 1920x1080 exactly 60 fps CFR artifacts')
    inputs.update({str(session_path / name): digest for name, digest in m['files'].items()})
    target = check_destination(output, m['source']['path'])
    if target.is_relative_to(session_path):
        raise ValueError('output cannot be inside source artifacts')
    payload = build_control_episodes(session.samples, settings)
    payload.update(source=m['source'], source_artifacts=str(session_path), clip_origin=m['clip_origin'],
                   limitations=LIMITS, raw_samples_file='pedal-samples.jsonl',
                   source_format_evidence=m['timebase'],
                   frame_mapping='frame IDs and time_s are native artifact coordinates; source_time_s=time_s+clip_origin.start_s',
                   code_sha256={str(p.relative_to(ROOT)): _sha(p) for p in
                                [Path(__file__), ROOT / 'src/acc_telemetry/analysis/control_episodes.py',
                                 ROOT / 'src/acc_telemetry/analysis/perception.py']})
    validation = None
    if annotations_path:
        annotations_path = Path(annotations_path).resolve()
        inputs[str(annotations_path)] = _sha(annotations_path)
        labels = json.loads(annotations_path.read_text())
        if labels.get('source_sha256') != m['source']['sha256'] or m['clip_origin']['start_s'] != 0:
            raise ValueError('annotation source/clock mismatch')
        validation = compare_annotations(payload, session.samples, labels)
        payload['annotations_path'] = str(annotations_path)
    payload['input_sha256'] = inputs
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.control-episodes-', dir=target.parent))
    try:
        def write(name, value):
            (staging / name).write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n')
        write('episodes.json', payload)
        if validation is not None:
            write('annotation-checks.json', validation)
        with (staging / 'pedal-samples.jsonl').open('w') as stream:
            for row in session.samples:
                record = dict(frame=row.frame, time_s=row.time_s, source_time_s=row.time_s + m['clip_origin']['start_s'],
                              **{field: getattr(row, field) for field in FIELDS},
                              quality={field: row.field_quality.get(field, Q.MISSING).value for field in FIELDS},
                              reasons={field: list(row.field_reasons.get(field, ())) for field in FIELDS})
                stream.write(json.dumps(record, allow_nan=False) + '\n')
        for path, digest in inputs.items():
            if _sha(Path(path)) != digest:
                raise ValueError(f'input changed: {path}')
        write('integrity.json', dict(inputs_unchanged=True, source_video_opened=False,
                                     files={p.name: _sha(p) for p in staging.iterdir()}))
        _publish(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target
