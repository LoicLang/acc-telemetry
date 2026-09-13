"""Small, pure summaries from source-bound manual reviews; never grants coaching eligibility."""
import math
from datetime import date

from acc_telemetry.domain.telemetry import QualityFlag


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_case(samples, manifest, case):
    """Check review scope and provenance, not the truth of the reviewer's statements."""
    if case['schema_version'] != 'session-coaching-case-v1':
        raise ValueError('unsupported case schema')
    if (case['source_sha256'] != manifest['source']['sha256']
            or case['source_size_bytes'] != manifest['source']['size_bytes']
            or case['artifact_files'] != manifest['files']):
        raise ValueError('case does not match session source/payloads')
    review = case['review']
    date.fromisoformat(review['date'])
    for text in (review['author'], review['type'], review['limits'], case['context'],
                 case['question'], case['exclusions']):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('missing review/context/limits')
    if case['gate_a'] != 'FAIL' or case['coaching_eligible'] is not False:
        raise ValueError('this experimental exporter requires Gate A FAIL and ineligible case')
    if not 2 <= len(case['passages']) <= 3:
        raise ValueError('select two or three passages')
    by_frame = {s.frame: s for s in samples}
    if len(by_frame) != len(samples) or any(b.time_s <= a.time_s for a, b in zip(samples, samples[1:])):
        raise ValueError('non-unique frames or non-monotonic sample time')
    markers = case['landmarks']
    if set(markers) != {'entry', 'exit'} or not all(markers.values()):
        raise ValueError('shared entry/exit landmarks required')
    ids = set()
    for passage in case['passages']:
        if not passage['id'] or passage['id'] in ids:
            raise ValueError('duplicate/empty passage id')
        ids.add(passage['id'])
        window = passage['window_frames']
        if len(window) != 2 or window[0] >= window[1]:
            raise ValueError('invalid passage window')
        reviewed = passage['reviewed_frames']
        if not reviewed or reviewed != sorted(set(reviewed)):
            raise ValueError('reviewed frames must be nonempty, sorted and unique')
        for f in [*window, *reviewed]:
            if type(f) is not int or f not in by_frame or not window[0] <= f <= window[1]:
                raise ValueError('review frame outside session/window')
        if not passage['outcome'] or not passage['comparison_limit']:
            raise ValueError('passage outcome and limits required')
        previous = window[0]
        for key in ('entry', 'exit'):
            mark = passage[key]
            if mark is None:
                if not passage.get(key + '_missing_reason'):
                    raise ValueError('missing landmark requires a reason')
                continue
            if (len(mark) != 2 or any(type(f) is not int or f not in reviewed for f in mark)
                    or not previous <= mark[0] <= mark[1] <= window[1]):
                raise ValueError('landmark bounds missing, reversed or unreviewed')
            previous = mark[1]
        if passage['entry'] is not None and passage['exit'] is not None:
            gap = passage['max_review_gap_s']
            if not _number(gap) or gap <= 0:
                raise ValueError('invalid interval review gap')
            frames = [f for f in reviewed if passage['entry'][0] <= f <= passage['exit'][1]]
            if any(by_frame[b].time_s - by_frame[a].time_s > gap + 1e-9
                   for a, b in zip(frames, frames[1:])):
                raise ValueError('duration interval exceeds declared visual review spacing')
    all_reviewed = {f for p in case['passages'] for f in p['reviewed_frames']}
    speed_ids = set()
    for point in case['speed_reviews']:
        if not point['id'] or point['id'] in speed_ids:
            raise ValueError('duplicate/empty speed evidence id')
        speed_ids.add(point['id'])
        if point['frame'] not in all_reviewed or not point['context']:
            raise ValueError('speed review is outside reviewed scene')
        value = point['hud_kmh']
        if value is not None and (not _number(value) or value < 0):
            raise ValueError('invalid manual HUD reading')
        if not point['reason']:
            raise ValueError('speed review reason required')
    for visual in case['visuals']:
        if (not visual['text'] or not visual['id'] or not visual['frames']
                or not set(visual['frames']) <= all_reviewed):
            raise ValueError('visual statement must reference reviewed frames')
    return by_frame


def summarize(samples, manifest, case):
    by_frame = validate_case(samples, manifest, case)
    coverage = {field: sum(getattr(s, field) is not None for s in samples)
                for field in ('speed_kmh', 'brake_pct', 'throttle_pct', 's')}
    durations = []
    for p in case['passages']:
        if p['entry'] is None or p['exit'] is None:
            durations.append({'id': p['id'], 'range_s': None})
            continue
        a, b = ([by_frame[f].time_s for f in p[key]] for key in ('entry', 'exit'))
        durations.append({'id': p['id'], 'range_s': (b[0] - a[1], b[1] - a[0])})
    speeds = []
    for point in case['speed_reviews']:
        s = by_frame[point['frame']]
        value = s.speed_kmh
        quality = s.field_quality.get('speed_kmh', QualityFlag.MISSING).value
        # A separate visual point review can support an observed value despite the
        # old unreviewed-visibility reason. Never repair missing or held values.
        admitted = value is not None and quality == 'observed' and value == point['hud_kmh']
        speeds.append(dict(point, extracted_kmh=value, admitted_kmh=value if admitted else None,
                           quality=quality, reasons=list(s.field_reasons.get('speed_kmh', ())),
                           time_s=manifest['clip_origin']['start_s'] + s.time_s))
    return {'coverage': coverage, 'durations': durations, 'speeds': speeds}
