"""Neutral temporal indexing of existing measurements; no driving diagnosis."""
from dataclasses import dataclass
import math
import re

from acc_telemetry.domain.telemetry import QualityFlag as Q


@dataclass(frozen=True)
class EventSettings:
    on_pct: float = 5.0
    off_pct: float = 2.0
    persistence_s: float = 0.10
    max_gap_s: float = 0.05

    def __post_init__(self):
        values=(self.on_pct,self.off_pct,self.persistence_s,self.max_gap_s)
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
            raise ValueError('event settings must be finite numbers')
        if not 0 <= self.off_pct < self.on_pct <= 100 or self.persistence_s <= 0 or self.max_gap_s <= 0:
            raise ValueError('invalid event thresholds, persistence or gap')


def _fresh(sample, field):
    value=getattr(sample,field)
    return (sample.field_quality.get(field)==Q.OBSERVED and value is not None
            and not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value))


def _event(kind, field, start, confirmed, previous=None):
    return dict(id=f'{kind}-{start.frame}',type=kind,field=field,frame=start.frame,
        time_s=start.time_s,confirmed_frame=confirmed.frame,confirmed_at_s=confirmed.time_s,
        previous_evidence_time_s=None if previous is None else previous.time_s,
        value=getattr(start,field),status='candidate',
        reasons=list(start.field_reasons.get(field,())),
        meaning='Neutral decoder event; not a verified driver intention or driving error')


def control_events(samples, field, settings):
    """Hysteresis/persistence index; never smooth samples or bridge missing evidence."""
    if field not in ('brake_pct','throttle_pct'):
        raise ValueError('unsupported control field')
    name='brake' if field=='brake_pct' else 'throttle'
    events=[];state=None;pending=None;previous=None
    for row in samples:
        fresh=_fresh(row,field) and 0 <= getattr(row,field) <= 100
        connected=previous is not None and 0 < row.time_s-previous.time_s <= settings.max_gap_s+1e-12
        if not fresh:
            state=None;pending=None;previous=None
            continue
        if not connected:
            state=None;pending=None
        value=getattr(row,field)
        if state is None:
            if value>=settings.on_pct:
                state=True
                events.append(_event(name+'_active_unbounded',field,row,row))
            elif value<=settings.off_pct:
                state=False
        else:
            crossed=value<=settings.off_pct if state else value>=settings.on_pct
            if not crossed:
                pending=None
            else:
                if pending is None:
                    pending=(row,previous)
                start,before=pending
                if row.time_s-start.time_s+1e-12>=settings.persistence_s:
                    events.append(_event(name+('_off' if state else '_on'),field,start,row,before))
                    state=not state;pending=None
        previous=row
    return events


def gear_events(samples, settings):
    result=[];previous=None
    for row in samples:
        if not _fresh(row,'gear'):
            previous=None
            continue
        if previous is not None and 0<row.time_s-previous.time_s<=settings.max_gap_s+1e-12 and row.gear!=previous.gear:
            event=_event('gear_change','gear',row,row,previous)
            event.update(from_value=previous.gear,to_value=row.gear)
            result.append(event)
        previous=row
    return result


def missing_intervals(samples, field, fps):
    if not math.isfinite(fps) or fps<=0:
        raise ValueError('invalid frame rate')
    result=[];start=None
    for i,row in enumerate(samples):
        missing=not _fresh(row,field)
        if missing and start is None:start=i
        if start is not None and (not missing or i==len(samples)-1):
            end=i if not missing else i+1
            first,last=samples[start],samples[end-1]
            result.append(dict(field=field,start_frame=first.frame,end_frame_exclusive=last.frame+1,
                start_time_s=first.time_s,end_time_s=last.time_s+1/fps,frames=end-start))
            start=None
    return result


def select_lap(manifest, lap_number):
    transitions=manifest['lap_transitions']
    indices=[i for i,t in enumerate(transitions) if t['to_lap']==lap_number]
    if len(indices)!=1 or indices[0]+1>=len(transitions):
        raise ValueError('lap requires two unambiguous confirmed boundaries')
    start,end=transitions[indices[0]:indices[0]+2]
    if end['to_lap']!=lap_number+1 or end['frame']<=start['frame']:
        raise ValueError('lap boundaries are not successive increments')
    return dict(number=lap_number,start_frame=start['frame'],end_frame=end['frame'],
        start_time_s=start['confirmed_at_s'],end_time_s=end['confirmed_at_s'],
        boundary_basis='confirmed HUD counter, not a certified physical crossing')


def validate_zones(zones, start_frame, end_frame):
    cursor=start_frame;ids=set()
    if not isinstance(zones,list) or not zones:raise ValueError('zones must be a nonempty partition')
    for zone in zones:
        if (not isinstance(zone.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]+',zone['id'])
                or zone['id'] in ids or not isinstance(zone.get('label'),str) or not zone['label'].strip()):
            raise ValueError('invalid or duplicate zone identifier/label')
        lo,hi=zone.get('start_frame'),zone.get('end_frame')
        if type(lo) is not int or type(hi) is not int or lo!=cursor or not lo<hi<=end_frame:
            raise ValueError('zones must cover each lap frame exactly once in order')
        ids.add(zone['id']);cursor=hi
    if cursor!=end_frame:raise ValueError('zones do not cover the whole lap')


def summarize_lap(samples, lap, zones, settings, fps):
    selected=[s for s in samples if lap['start_frame']<=s.frame<lap['end_frame']]
    if len(selected)!=lap['end_frame']-lap['start_frame']:
        raise ValueError('lap sample coverage is incomplete')
    for i,s in enumerate(selected):
        if s.frame!=lap['start_frame']+i or not math.isclose(s.time_s,lap['start_time_s']+i/fps,abs_tol=1e-8):
            raise ValueError('lap frame/time alignment is inconsistent')
    validate_zones(zones,lap['start_frame'],lap['end_frame'])
    events=control_events(selected,'brake_pct',settings)+control_events(selected,'throttle_pct',settings)+gear_events(selected,settings)
    events.sort(key=lambda e:(e['time_s'],e['type']))
    for event in events:
        event['zone_id']=next(z['id'] for z in zones if z['start_frame']<=event['frame']<z['end_frame'])
    missing=[r for f in ('speed_kmh','brake_pct','throttle_pct','gear') for r in missing_intervals(selected,f,fps)]
    coverage={f:sum(_fresh(s,f) for s in selected) for f in ('speed_kmh','brake_pct','throttle_pct','gear')}
    return selected,dict(events=events,missing=missing,available=coverage,frames=len(selected))
