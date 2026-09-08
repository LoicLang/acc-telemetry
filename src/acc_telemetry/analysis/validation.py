"""Independent annotation structure and corpus readiness, not extraction accuracy."""
import math
from collections import Counter
from acc_telemetry.domain.observations import VisibilitySpan, validate_visibility


def validate_windows(windows, frame_count):
    previous=-1
    for window in windows:
        lo,hi=window['frame_lo'],window['frame_hi']
        if type(lo) is not int or type(hi) is not int or not 0<=lo<=hi<frame_count or lo<=previous:
            raise ValueError('invalid or overlapping frame interval')
        previous=hi
    return windows


def _finite(value, low, high):
    return type(value) in (int,float) and math.isfinite(value) and low<=value<=high


def validate_annotations(labels, capture, *, source_sha256):
    if (labels.get('schema_version')!='capture-annotations-v1' or capture.get('status')!='pass'
            or labels.get('source_sha256')!=source_sha256 or len(source_sha256)!=64):
        raise ValueError('invalid annotation source/capture')
    if (labels.get('reviewed') is not True or not isinstance(labels.get('annotator'),str)
            or not labels['annotator'].strip() or labels.get('role') not in ('development','holdout')):
        raise ValueError('annotations must be reviewed by a named annotator with a source role')
    count=capture['frame_count']
    validate_windows(labels['windows'],count)
    readable=Counter(speed=0,brake=0,throttle=0)
    degraded=0
    seen=set()
    for row in labels['frames']:
        frame=row['frame']
        if type(frame) is not int or not 0<=frame<count or frame in seen or row.get('reviewed') is not True:
            raise ValueError('invalid, duplicate or unreviewed frame annotation')
        seen.add(frame)
        if not _finite(row['time_s'],0,capture['duration']) or abs(row['time_s']-capture['timestamps'][frame])>1e-6:
            raise ValueError('annotation frame/time mismatch')
        partial = row.get('review_scope') == 'provided_fields_only'
        if type(row['degraded']) is not bool and not (partial and row['degraded'] is None):
            raise ValueError('degradation must be reviewed')
        degraded+=row['degraded'] is True
        visibility=row['visibility']
        if set(visibility)!=set(('speed','gear','lap_number','throttle','brake','steering')) or any(type(v) is not bool and not (partial and v is None) for v in visibility.values()):
            raise ValueError('frame visibility must be reviewed per field')
        for key in ('speed_text','gear_text','lap_text'):
            value=row[key]
            if value is not None:
                field={'speed_text':'speed','gear_text':'gear','lap_text':'lap_number'}[key]
                if not isinstance(value,str) or not value.strip() or not visibility[field]:
                    raise ValueError('OCR annotation requires literal readable text and visibility')
                symbol=value.strip()
                if key in ('speed_text','lap_text') and not symbol.isdecimal():
                    raise ValueError('unreadable numeric label must be null')
                if key=='gear_text' and symbol not in ('1','2','3','4','5','6','N','R'):
                    raise ValueError('unsupported gear label')
        if visibility['speed'] and row['speed_text'] is not None:
            readable['speed']+=1
        for field in ('brake','throttle'):
            value=row[field+'_pct']
            if value is not None and (not _finite(value,0,100) or not visibility[field]):
                raise ValueError('invalid pedal label or missing visibility')
            if value is not None:
                if not _finite(row['pedal_tolerance_pct'],0,100):
                    raise ValueError('pedal label needs finite tolerance')
                readable[field]+=1
    identifiers=set()
    event_windows=set()
    for passage in labels['passages']:
        validate_windows([passage],count)
        if (passage.get('reviewed') is not True or not isinstance(passage.get('id'),str)
                or not passage['id'].strip() or passage['id'] in identifiers
                or passage.get('kind') not in ('landmark','lap_boundary','pedal_event')):
            raise ValueError('invalid or unreviewed passage')
        identifiers.add(passage['id'])
        if passage['kind']=='pedal_event':
            if passage.get('field') not in ('throttle','brake'):
                raise ValueError('pedal event needs field')
            event_windows.add(passage.get('event_window_id', passage['id']))
    spans=[]
    for row in labels['visibility']:
        if row.get('reviewed') is not True:
            raise ValueError('unreviewed visibility interval')
        spans.append(VisibilitySpan(row['field'],row['start_s'],row['end_s'],row.get('reviewer',labels['annotator'])))
    validate_visibility(spans,duration_s=capture['duration'])
    for span in spans:
        for row in labels['frames']:
            if span.start_s<=row['time_s']<span.end_s and not row['visibility'][span.field]:
                raise ValueError('visibility span contradicts reviewed frame occlusion')
    has_truth=bool(labels['frames'] or labels['passages'] or labels['visibility'])
    return dict(status='pass' if has_truth else 'not_evaluated', error=None,
        readable_frames=dict(readable),degraded_frames=degraded,event_windows=len(event_windows),
        passages=sum(p['kind'] in ('landmark','lap_boundary') and p.get('physical_landmark_reviewed', True) for p in labels['passages']),visibility=[dict(field=s.field,start_s=s.start_s,
            end_s=s.end_s,reviewer=s.reviewer) for s in spans])


def corpus_readiness(entries, settings):
    """Source-level roles prevent neighboring-frame leakage; missing labels are pending."""
    roles={}
    source_hashes=set()
    for entry in entries:
        source,role=entry.get('recording_id') or entry['source_sha256'],entry['role']
        if source in roles or entry['source_sha256'] in source_hashes:
            raise ValueError('a source must occur once and cannot mix development/holdout')
        if role not in ('development','holdout'):
            raise ValueError('invalid corpus role')
        roles[source]=role
        source_hashes.add(entry['source_sha256'])
    reports=[entry.get('review_report',{}) for entry in entries]
    readable={f:sum(r.get('readable_frames',{}).get(f,0) for r in reports) for f in ('speed','brake','throttle')}
    degraded=sum(r.get('degraded_frames',0) for r in reports)
    events=sum(r.get('event_windows',0) for r in reports)
    checks=dict(sources=len(roles)>=settings.min_sources,
        recording_lineage=all(isinstance(e.get('recording_id'),str) and bool(e['recording_id'].strip()) for e in entries),
        repeated_passages=bool(reports) and all(r.get('passages',0)>=settings.min_passages_per_source for r in reports),
        roles=set(roles.values())=={'development','holdout'},
        readable=all(v>=settings.min_readable_frames for v in readable.values()),
        degraded=degraded>=settings.min_degraded_frames,events=events>=settings.min_event_windows,
        reviewed=bool(reports) and all(r.get('status')=='pass' for r in reports))
    return dict(status='pass' if all(checks.values()) else 'not_evaluated',checks=checks,
                readable_frames=readable,degraded_frames=degraded,event_windows=events)


def percentile(values, fraction=.95):
    """Linear quantile, including its interpolation convention in callers' reports."""
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lo = int(index)
    return ordered[lo] + (ordered[min(lo + 1, len(ordered)-1)] - ordered[lo]) * (index-lo)


def field_errors(truth, predictions):
    """Raw absolute errors, without subtracting annotation tolerance or abstentions."""
    if len(truth) != len(predictions):
        raise ValueError('unpaired field evidence')
    if any(not _finite(v, -math.inf, math.inf) for v in truth):
        raise ValueError('nonfinite truth')
    if any(v is not None and not _finite(v, -math.inf, math.inf) for v in predictions):
        raise ValueError('nonfinite prediction')
    errors = [abs(a-b) for a,b in zip(truth, predictions) if b is not None]
    return dict(status='available' if errors else 'not_evaluated', denominator=len(truth),
                measured_count=len(errors), abstentions=len(truth)-len(errors),
                coverage=len(errors)/len(truth) if truth else None,
                mae=sum(errors)/len(errors) if errors else None, p95=percentile(errors),
                quantile_method='linear', absolute_errors=errors)


def match_events(truth, predictions, *, max_window_s):
    """Maximum-cardinality monotone matching, then minimum total midpoint distance.

    Caller supplies one source and one event subtype. Matching tolerance is not the
    acceptance error threshold. Unmatched predictions near truth are duplicates;
    those without a candidate in the matching window are reported separately.
    """
    if not _finite(max_window_s, 0, math.inf) or max_window_s == 0:
        raise ValueError('invalid matching window')
    for rows in (truth, predictions):
        if len({r['id'] for r in rows}) != len(rows):
            raise ValueError('duplicate event identity')
    for row in truth:
        if not (_finite(row['lo_s'], 0, math.inf) and _finite(row['hi_s'], row['lo_s'], math.inf)):
            raise ValueError('invalid truth interval')
    for row in predictions:
        if not _finite(row['time_s'], 0, math.inf):
            raise ValueError('invalid event time')
        if row.get('confirmed_at_s') is not None and not _finite(row['confirmed_at_s'], row['time_s'], math.inf):
            raise ValueError('invalid confirmation time')
    t = sorted(truth, key=lambda r: (r['lo_s']+r['hi_s'])/2)
    p = sorted(predictions, key=lambda r: r['time_s'])
    mid = [(r['lo_s']+r['hi_s'])/2 for r in t]
    # Scores use negative cardinality so ordinary tuple ordering expresses policy.
    scores = [[(0, 0.0) for _ in range(len(p)+1)] for _ in range(len(t)+1)]
    back = {}
    for i in range(1,len(t)+1):
        for j in range(1,len(p)+1):
            choices = [(scores[i-1][j], 'truth'), (scores[i][j-1], 'prediction')]
            distance = abs(mid[i-1]-p[j-1]['time_s'])
            if distance <= max_window_s:
                n,cost = scores[i-1][j-1]
                choices.append(((n-1, cost+distance), 'match'))
            scores[i][j], back[i,j] = min(choices, key=lambda x:x[0])
    i,j = len(t),len(p)
    pairs = []
    while i and j:
        action=back[i,j]
        if action=='match':
            pairs.append((i-1,j-1)); i-=1; j-=1
        elif action=='truth':
            i-=1
        else:
            j-=1
    pairs.reverse()
    matched_t={i for i,j in pairs}; matched_p={j for i,j in pairs}
    matches=[]
    for i,j in pairs:
        signed=p[j]['time_s']-mid[i]
        matches.append(dict(truth_id=t[i]['id'], prediction_id=p[j]['id'],
            signed_error_s=signed, absolute_error_s=abs(signed), annotation_midpoint_s=mid[i],
            annotation_half_width_s=(t[i]['hi_s']-t[i]['lo_s'])/2,
            time_uncertainty_s=t[i].get('time_uncertainty_s'),
            confirmation_delay_s=(p[j]['confirmed_at_s']-p[j]['time_s'])
                if p[j].get('confirmed_at_s') is not None else None))
    unmatched=[j for j in range(len(p)) if j not in matched_p]
    duplicate=[j for j in unmatched if any(abs(p[j]['time_s']-m)<=max_window_s for m in mid)]
    errors=[r['absolute_error_s'] for r in matches]
    return dict(status='available' if truth else 'not_evaluated', truth_count=len(t),
        prediction_count=len(p), matched_count=len(matches), matches=matches,
        missed_ids=[r['id'] for i,r in enumerate(t) if i not in matched_t],
        duplicate_ids=[p[j]['id'] for j in duplicate],
        outside_window_ids=[p[j]['id'] for j in unmatched if j not in duplicate],
        unmatched_prediction_count=len(unmatched),
        precision=len(matches)/len(p) if p and truth else None,
        recall=len(matches)/len(t) if t else None,
        median_error_s=percentile(errors,.5), p95_error_s=percentile(errors),
        max_matching_window_s=max_window_s, quantile_method='linear')


def landmark_dispersion(passages):
    """Circular range of normalized progress; never an absolute spatial error."""
    values=[r['s'] for r in passages if r.get('s') is not None]
    if any(not _finite(v,0,1) for v in values):
        raise ValueError('invalid normalized progress')
    ordered=sorted(v%1 for v in values)
    gaps=[b-a for a,b in zip(ordered,ordered[1:])]
    if ordered:
        gaps.append(ordered[0]+1-ordered[-1])
    return dict(status='available' if len(values)>=2 else 'not_evaluated',
        denominator=len(passages), measured_count=len(values),
        range_s=1-max(gaps) if len(values)>=2 else None,
        range_definition='shortest circular covering arc in normalized s',
        metric_accuracy='not_evaluated', passages=passages)
