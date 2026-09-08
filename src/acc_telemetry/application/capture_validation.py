"""Read-only independent measurements over telemetry-v2; never invokes extraction."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json

from acc_telemetry.analysis.validation import (
    field_errors, landmark_dispersion, match_events, validate_annotations, validate_windows,
)
from acc_telemetry.application.session_artifacts import read_session_artifacts, _sha, _json
from acc_telemetry.application.validation_config import load_validation_settings
from acc_telemetry.domain.telemetry import QualityFlag

FIELDS = {'speed': 'speed_kmh', 'brake': 'brake_pct', 'throttle': 'throttle_pct'}
PEDAL_TYPES = {'brake_onset': ('brake', 'onset'), 'brake_release': ('brake', 'release'),
               'throttle_reapplication': ('throttle', 'onset'),
               'throttle_release': ('throttle', 'release')}
CHECKS = ('software_regressions', 'lap_events', 'field_accuracy', 'field_coverage', 'timebase', 'holdout')


def evidence(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=_sha(path), size_bytes=path.stat().st_size)


def combine_status(statuses):
    statuses = list(statuses)
    if 'fail' in statuses:
        return 'fail'
    return 'pass' if statuses and all(s == 'pass' for s in statuses) else 'not_evaluated'


def gate_report(checks, fingerprint):
    if set(checks)-set(CHECKS):
        raise ValueError('unknown gate check')
    result={key: checks.get(key, dict(status='not_evaluated', evidence=[], reason='missing_evidence'))
            for key in CHECKS}
    if any(c['status'] not in ('pass','fail','not_evaluated') for c in result.values()):
        raise ValueError('invalid gate status')
    if any(c['status']=='pass' and not c.get('evidence') for c in result.values()):
        raise ValueError('passing checks require evidence')
    status=combine_status(c['status'] for c in result.values())
    compatible=fingerprint.get('compatible_with_current_extractor') is True and bool(fingerprint.get('sha256'))
    if status=='pass' and not compatible:
        status='not_evaluated'
    return dict(schema_version='gate-a-v1', status=status, coaching_eligible=status=='pass',
                checks=result, measurement_fingerprint=fingerprint,
                unsupported=['tc_active','abs_active','steering_accuracy','metric_spatial_accuracy'])


def measurement_fingerprint(manifest, settings):
    """Ignore Git-only/docs changes; extraction and measurement changes invalidate."""
    root=Path(__file__).resolve().parents[3]
    prefixes=('src/acc_telemetry/extraction/', 'src/acc_telemetry/normalization/',
              'src/acc_telemetry/domain/')
    application=('pipeline','progress','lap_state','odometry','session_artifacts','components','config')
    names=[str(p.relative_to(root)) for p in (root/'src/acc_telemetry').rglob('*.py')
           if str(p.relative_to(root)).startswith(prefixes)
           or p in [root/f'src/acc_telemetry/application/{name}.py' for name in application]]
    current={name:_sha(root/name) for name in sorted(names)}
    recorded=manifest.get('code',{}).get('module_sha256',{})
    compatibility=all(recorded.get(name)==sha for name,sha in current.items())
    validator={name:_sha(root/name) for name in (
        'src/acc_telemetry/analysis/validation.py',
        'src/acc_telemetry/application/capture_validation.py',
        'src/acc_telemetry/application/validation_config.py')}
    payload=dict(extraction_modules={name:recorded.get(name) for name in current},
                 resolved_configuration=manifest.get('config'), profile=manifest.get('profile'),
                 validation_settings=json.loads(_json(settings)), validator_modules=validator)
    return dict(sha256=hashlib.sha256(_json(payload).encode()).hexdigest(), components=payload,
                compatible_with_current_extractor=compatibility,
                extraction_git=manifest.get('code',{}).get('git_commit'))


def pedal_truth(passages, timestamps):
    included=[]; excluded=[]
    for row in passages:
        if row['kind'] != 'pedal_event':
            continue
        event_type=row.get('event_type')
        if event_type not in PEDAL_TYPES or row.get('eligible_for_5pct_crossing_latency') is False:
            excluded.append(dict(id=row['id'],event_type=event_type,
                reason=row.get('exclusion_reason','no_reviewed_applicable_crossing_semantics')))
            continue
        field,direction=PEDAL_TYPES[event_type]
        included.append(dict(row, field=field, direction=direction,
            lo_s=timestamps[row['frame_lo']], hi_s=timestamps[row['frame_hi']]))
    return included,excluded


def fresh_crossings(observations, field, *, threshold, max_gap_s):
    previous=None; result=[]
    for row in observations:
        obs=row.observations.get(field)
        if obs is None or obs.quality != QualityFlag.OBSERVED or obs.value is None:
            previous=None
            continue
        if previous is not None:
            before, value=previous
            if row.frame == before.frame+1 and 0 < row.time_s-before.time_s <= max_gap_s:
                direction=('onset' if value<=threshold<obs.value else
                           'release' if value>threshold>=obs.value else None)
                if direction:
                    result.append(dict(id=f'{field}-{row.frame}', time_s=row.time_s,
                                       direction=direction, previous_time_s=before.time_s))
        previous=row,obs.value
    return result


def _fresh(sample, observation, field):
    obs=observation.observations.get(field) if observation else None
    if (sample is None or obs is None or obs.quality != QualityFlag.OBSERVED
            or sample.field_quality.get(field) != QualityFlag.OBSERVED):
        return None
    return getattr(sample,field)


def lap_status(report, *, complete_review, max_error_s):
    if not report['truth_count']:
        return 'not_evaluated'
    if report['missed_ids'] or (report['p95_error_s'] is not None and report['p95_error_s'] > max_error_s):
        return 'fail'
    if not complete_review:
        return 'not_evaluated'
    return 'fail' if report['unmatched_prediction_count'] else 'pass'


def latency_status(report, *, observable_truth_count, max_error_s):
    if report['p95_error_s'] is not None and report['p95_error_s'] > max_error_s:
        return 'fail'
    if not report['truth_count'] or observable_truth_count < report['truth_count']:
        return 'not_evaluated'
    return 'fail' if report['missed_ids'] or report['unmatched_prediction_count'] else 'pass'


def evaluate_session(artifacts, annotations, capture_path, *, settings=None):
    settings=settings or load_validation_settings()
    labels=json.loads(Path(annotations).read_text())
    capture_manifest=json.loads(Path(capture_path).read_text())
    capture=capture_manifest['capture']
    review=validate_annotations(labels,capture,source_sha256=capture_manifest['source']['sha256'])
    session=read_session_artifacts(artifacts)
    manifest=session.manifest
    # Exact input identity is mandatory. A parent clip requires its own accepted labels.
    if (manifest['source']['sha256'] != labels['source_sha256']
            or manifest['profile'] != capture_manifest['profile']):
        raise ValueError('artifact/annotation source or profile mismatch')
    timestamps=capture['timestamps']
    target_segments=validate_windows(labels.get('evaluation_segments',[]),capture['frame_count'])
    sample_by={s.frame:s for s in session.samples}
    obs_by={o.frame:o for o in session.observations}
    frames=[s.frame for s in session.samples]
    aligned=(frames==list(range(capture['frame_count'])) and
             all(abs(s.time_s-timestamps[s.frame])<=1e-6 for s in session.samples))
    timebase=combine_status([capture['status'],manifest['timebase']['status'],
                            'pass' if aligned else 'fail'])
    fields={}
    for name,field in FIELDS.items():
        label_name='speed_text' if name=='speed' else field
        truth_rows=[r for r in labels['frames'] if r['visibility'][name] is True and r[label_name] is not None]
        values=[float(r[label_name]) for r in truth_rows]
        predictions=[_fresh(sample_by.get(r['frame']),obs_by.get(r['frame']),field) for r in truth_rows]
        report=field_errors(values,predictions)
        report['readings']=[dict(frame=r['frame'],time_s=r['time_s'],truth=value,
            measured=prediction,absolute_error=abs(value-prediction) if prediction is not None else None)
            for r,value,prediction in zip(truth_rows,values,predictions)]
        target=settings.speed_mae_kmh if name=='speed' else settings.pedal_mae_pct
        report['accuracy_status']=('not_evaluated' if report['mae'] is None else
            'pass' if report['mae']<=target and (name!='speed' or report['p95']<=settings.speed_p95_kmh) else 'fail')
        report['point_coverage_status']=('not_evaluated' if not values else
            'pass' if report['coverage']>=settings.min_coverage else 'fail')
        report['annotation_tolerances']=[dict(frame=r['frame'], tolerance_pct=r.get('pedal_tolerance_pct'))
            for r in truth_rows] if name!='speed' else []
        report['excluded_label_count']=len(labels['frames'])-len(truth_rows)
        report['excluded_or_missing_readings']=[dict(frame=r['frame'],reason='not_fresh_or_absent')
            for r,v in zip(truth_rows,predictions) if v is None]
        report['false_observed_on_reviewed_absence']=[r['frame'] for r in labels['frames']
            if r['visibility'][name] is False and
            _fresh(sample_by.get(r['frame']),obs_by.get(r['frame']),field) is not None]
        if report['false_observed_on_reviewed_absence']:
            report['accuracy_status']='fail'
        spans=[s for s in labels['visibility'] if s['field']==name]
        # Continuous review covers only the explicitly reviewed frame cells, not whole source.
        eligible=([i for w in target_segments for i in range(w['frame_lo'],w['frame_hi']+1)]
                  if target_segments else
                  [i for i,t in enumerate(timestamps) if any(s['start_s']<=t<s['end_s'] for s in spans)])
        measured=sum(_fresh(sample_by.get(i),obs_by.get(i),field) is not None for i in eligible)
        report['continuous_coverage']=dict(status=('not_evaluated' if not eligible else
            'pass' if measured/len(eligible)>=settings.min_coverage else 'fail'),
            denominator_frames=len(eligible), observed_frames=measured,
            ratio=measured/len(eligible) if eligible else None,
            reviewed_spans=spans, evaluation_segments=target_segments,
            scope='fresh output availability on explicit target segments, or reviewed spans only; no inferred visibility')
        fields[name]=report
    truth,excluded=pedal_truth(labels['passages'],timestamps)
    pedal_results={}
    for event_type,(name,direction) in PEDAL_TYPES.items():
        subtype=[r for r in truth if r['event_type']==event_type]
        candidates=fresh_crossings(session.observations,FIELDS[name],threshold=settings.pedal_crossing_pct,
                                    max_gap_s=settings.fresh_crossing_max_gap_s)
        # Truth is sparse, so out-of-scope detections are diagnostic, not false positives.
        inside=[r for r in candidates if r['direction']==direction and any(
            abs(r['time_s']-(t['lo_s']+t['hi_s'])/2)<=settings.event_matching_window_s for t in subtype)]
        report=match_events(subtype,inside,max_window_s=settings.event_matching_window_s)
        report['outside_review_scope_count']=sum(r['direction']==direction for r in candidates)-len(inside)
        observable=0
        for event in subtype:
            midpoint=(event['lo_s']+event['hi_s'])/2
            window=[i for i,t in enumerate(timestamps)
                    if abs(t-midpoint)<=settings.event_matching_window_s]
            if len(window)>=2 and all(_fresh(sample_by.get(i),obs_by.get(i),FIELDS[name])
                                      is not None for i in window):
                observable+=1
        report['observable_truth_count']=observable
        report['latency_status']=latency_status(report,observable_truth_count=observable,
                                                max_error_s=settings.event_p95_s)
        pedal_results[event_type]=report
    lap_truth=[dict(r,lo_s=timestamps[r['frame_lo']],hi_s=timestamps[r['frame_hi']])
               for r in labels['passages'] if r['kind']=='lap_boundary']
    lap_predictions=[dict(id=f"boundary-{i}",time_s=r['first_candidate_time_s'],
                         confirmed_at_s=r.get('confirmed_at_s'))
                     for i,r in enumerate(manifest['lap_transitions']) if r.get('first_candidate_time_s') is not None]
    laps=match_events(lap_truth,lap_predictions,max_window_s=settings.event_matching_window_s)
    complete=labels.get('lap_review',{})
    lap_complete=(complete.get('reviewed') is True and complete.get('complete_real_and_suspect_transitions') is True
                  and complete.get('frame_lo')==0 and complete.get('frame_hi')==capture['frame_count']-1)
    laps['complete_capture_review']=lap_complete
    laps['unmatched_scope']='missed approved truth counts; unmatched predictions are false only with complete review'
    laps['prediction_time_definition']='first fresh candidate; confirmation delay reported separately'
    laps['gate_status']=lap_status(laps,complete_review=lap_complete,max_error_s=settings.event_p95_s)
    landmarks=defaultdict(list)
    for row in labels['passages']:
        if row['kind']!='landmark':
            continue
        lo,hi=row['frame_lo'],row['frame_hi']; frame=(lo+hi)//2
        sample=sample_by.get(frame)
        value=sample.s if sample and sample.field_quality.get('s') not in (
            QualityFlag.MISSING,QualityFlag.HELD,QualityFlag.ANOMALOUS) else None
        interval_values=[sample_by[i].s for i in range(lo,hi+1)
            if i in sample_by and sample_by[i].s is not None
            and sample_by[i].field_quality.get('s') not in (QualityFlag.MISSING,QualityFlag.HELD,QualityFlag.ANOMALOUS)]
        landmarks[row['landmark_id']].append(dict(id=row['id'],s=value,frame=frame,
            s_quality=sample.field_quality.get('s').value if sample and sample.field_quality.get('s') else None,
            s_reasons=list(sample.s_reasons) if sample else ['missing_sample'],
            interval_measured_frames=len(interval_values),interval_total_frames=hi-lo+1,
            interval_s_values=interval_values,
            annotation_half_width_s=(timestamps[hi]-timestamps[lo])/2,
            selection_offset_from_midpoint_s=timestamps[frame]-(timestamps[lo]+timestamps[hi])/2,
            s_uncertainty=sample.s_uncertainty if sample else None,
            reference=row.get('reference'), definition=row.get('definition')))
    fingerprint=measurement_fingerprint(manifest,settings)
    return dict(schema_version='capture-validation-v1', source_sha256=labels['source_sha256'],
        recording_id=labels.get('recording_id'),role=labels['role'],
        evidence=[evidence(annotations),evidence(capture_path),evidence(Path(artifacts)/'manifest.json')],
        annotation_review=review, fields=fields, pedal_events=pedal_results,
        pedal_exclusions=excluded, pedal_event_denominator=len(truth),
        pedal_window_denominator=len({r.get('event_window_id',r['id']) for r in truth}),
        pedal_metric_definition='first fresh 5% crossing versus reviewed onset/release midpoint; not B4',
        lap_events=laps, landmarks={key:landmark_dispersion(rows) for key,rows in landmarks.items()},
        timebase=dict(status=timebase, expected_frames=capture['frame_count'], artifact_frames=len(frames),
                      exact_frame_and_timestamp_alignment=aligned),
        measurement_fingerprint=fingerprint, coaching_eligible=False)
