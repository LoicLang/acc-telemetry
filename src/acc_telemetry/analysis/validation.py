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
        if type(row['degraded']) is not bool:
            raise ValueError('degradation must be reviewed')
        degraded+=row['degraded']
        visibility=row['visibility']
        if set(visibility)!=set(('speed','gear','lap_number','throttle','brake','steering')) or any(type(v) is not bool for v in visibility.values()):
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
    event_windows=0
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
            event_windows+=1
    spans=[]
    for row in labels['visibility']:
        if row.get('reviewed') is not True:
            raise ValueError('unreviewed visibility interval')
        spans.append(VisibilitySpan(row['field'],row['start_s'],row['end_s'],labels['annotator']))
    validate_visibility(spans,duration_s=capture['duration'])
    for span in spans:
        for row in labels['frames']:
            if span.start_s<=row['time_s']<span.end_s and not row['visibility'][span.field]:
                raise ValueError('visibility span contradicts reviewed frame occlusion')
    has_truth=bool(labels['frames'] or labels['passages'] or labels['visibility'])
    return dict(status='pass' if has_truth else 'not_evaluated', error=None,
        readable_frames=dict(readable),degraded_frames=degraded,event_windows=event_windows,
        passages=sum(p['kind'] in ('landmark','lap_boundary') for p in labels['passages']),visibility=[dict(field=s.field,start_s=s.start_s,
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
