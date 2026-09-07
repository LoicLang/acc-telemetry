"""Consolidate scoped human approvals without broadening what was reviewed."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from acc_telemetry.analysis.validation import validate_annotations, corpus_readiness
from .session_artifacts import _json, _read_json, _publish, check_destination
from .validation_config import load_validation_settings


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def consolidate_approvals(paths, destination, *, settings=None):
    settings = settings or load_validation_settings()
    paths = list(dict.fromkeys(Path(p).resolve(strict=True) for p in paths))
    if not paths:
        raise ValueError('approval files required')
    destination = check_destination(destination, paths[0])
    groups = {}
    approvals = []
    for path in paths:
        approval = _read_json(path.read_text())
        if approval.get('schema_version') != 'scoped-review-approval-v1' or not approval.get('reviewer'):
            raise ValueError('unsupported or unreviewed approval')
        approvals.append((path, approval))
        for reading in approval['approved_readings']:
            if reading.get('reviewed') is not True:
                raise ValueError('unreviewed reading cannot be consolidated')
            image = Path(reading['image'])
            if _sha(image) != reading['image_sha256']:
                raise ValueError('approved image integrity mismatch')
            capture = _read_json((image.parent.parent / 'capture.json').read_text())
            source = reading['source_sha256']
            if source != capture['source']['sha256']:
                raise ValueError('approval source mismatch')
            metadata = approval.get('sources', {})
            matches = [entry for key,entry in metadata.items()
                       if key == source or entry.get('identity', {}).get('sha256') == source]
            if metadata and len(matches) != 1:
                raise ValueError('ambiguous or missing approved source metadata')
            source_meta = matches[0] if matches else {}
            role = source_meta.get('role', 'development')
            if role not in ('development', 'holdout'):
                raise ValueError('invalid approved source role')
            recording_id = source_meta.get('recording_id')
            group = groups.setdefault(source, dict(capture=capture, frames={}, events={}, context=[],
                                                    role=role, recording_id=recording_id))
            if group['role'] != role or group['recording_id'] != recording_id:
                raise ValueError('conflicting approved source role or lineage')
            if group['capture']['capture'] != capture['capture']:
                raise ValueError('inconsistent capture metadata')
            values = reading['proposed']
            visibility = {f: None for f in ('speed','gear','lap_number','throttle','brake','steering')}
            # Acceptance of an explicit visible value covers that field, not the rest of the frame.
            for field, key in [('speed','speed_text'),('gear','gear_text'),('lap_number','lap_text'),
                               ('throttle','throttle_pct'),('brake','brake_pct')]:
                if values.get(key) is not None:
                    visibility[field] = True
            supplied_visibility = reading.get('proposed_visibility', {})
            for field, visible in supplied_visibility.items():
                if field in visibility and type(visible) is bool:
                    visibility[field] = visible
            tolerance = values.get('pedal_tolerance_pct')
            if reading.get('tolerance_points'):
                tolerance = max(reading['tolerance_points'].values())
            degraded = reading.get('proposed_degraded')
            if degraded is not None and type(degraded) is not bool:
                raise ValueError('degradation review must be explicit boolean or unknown')
            row = dict(frame=reading['frame'], time_s=reading['time_s'],
                **{k: values.get(k) for k in ('speed_text','gear_text','lap_text','throttle_pct','brake_pct')},
                pedal_tolerance_pct=tolerance, visibility=visibility, degraded=degraded,
                review_scope='provided_fields_only', reviewed=True,
                approval_sources=[str(path)], image_sha256=reading['image_sha256'])
            previous = group['frames'].get(row['frame'])
            if previous is not None:
                if {k:v for k,v in previous.items() if k!='approval_sources'} != {k:v for k,v in row.items() if k!='approval_sources'}:
                    raise ValueError('conflicting approved readings require explicit resolution')
                previous['approval_sources'] = sorted(set(previous['approval_sources'] + [str(path)]))
            else:
                group['frames'][row['frame']] = row

    for path, approval in approvals:
        window_sources = {r['window_id']: r['source_sha256'] for r in approval['approved_readings']}
        for claim in approval.get('approved_event_claims', []):
            source = claim.get('source_sha256') or window_sources.get(claim.get('window_id'))
            if source not in groups:
                raise ValueError('event has no associated approved source')
            kind = claim.get('kind')
            pedal_fields = {'throttle_release': 'throttle', 'throttle_reapplication': 'throttle',
                            'brake_onset': 'brake', 'brake_release': 'brake'}
            if kind != 'reported_lap_start' and kind not in pedal_fields:
                groups[source]['context'].append(claim)
                continue
            frame = claim['frame']
            event = dict(id=f'{claim["window_id"]}-{kind}', frame_lo=max(0,frame-1), frame_hi=frame,
                kind='lap_boundary' if kind=='reported_lap_start' else 'pedal_event',
                event_type=kind, field=pedal_fields.get(kind),
                physical_landmark_reviewed=False, event_window_id=claim['window_id'],
                reviewed=True, approval_source=str(path), evidence_definition=claim.get('scope',kind))
            groups[source]['events'][event['id']] = event
        for claim in approval.get('approved_visual_followups', []):
            if 'first_visible_brake_frame' not in claim:
                continue
            if claim.get('reviewed') is not True:
                raise ValueError('unreviewed event follow-up')
            source = window_sources[claim['window_id']]
            event = dict(id=f'{claim["window_id"]}-first_visible_brake', kind='pedal_event', field='brake',
                frame_lo=claim['previous_frame'], frame_hi=claim['first_visible_brake_frame'],
                event_type='first_visible_brake', event_window_id=claim['window_id'],
                reviewed=True, approval_source=str(path))
            groups[source]['events'][event['id']] = event
        for claim in approval.get('semantic_context', []):
            source = window_sources.get(claim.get('window_id'))
            if source in groups:
                groups[source]['context'].append(claim)

    documents = []
    for source, group in sorted(groups.items()):
        document = dict(schema_version='capture-annotations-v1', source_sha256=source,
            role=group['role'], recording_id=group['recording_id'], annotator='user', reviewed=True,
            review_scope='provided_fields_only', frames=[group['frames'][f] for f in sorted(group['frames'])],
            windows=[], passages=list(group['events'].values()), visibility=[], context=group['context'])
        report = validate_annotations(document, group['capture']['capture'], source_sha256=source)
        documents.append((source, group['capture'], document, report))
    readiness = corpus_readiness([dict(document, review_report=report) for _,_,document,report in documents], settings)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{destination.name}-', dir=destination.parent))
    try:
        index = dict(schema_version='approved-corpus-index-v1', coaching_eligible=False,
            approval_files=[dict(path=str(p), sha256=_sha(p)) for p in paths], sources=[],
            approved_unique_frames=sum(len(doc['frames']) for _,_,doc,_ in documents), readiness=readiness)
        for source, capture, document, report in documents:
            folder = staging / source
            folder.mkdir()
            (folder/'labels.json').write_text(_json(document)+'\n')
            (folder/'capture.json').write_text(_json(capture)+'\n')
            (folder/'review-report.json').write_text(_json(report)+'\n')
            index['sources'].append(dict(source_sha256=source, labels=f'{source}/labels.json'))
        (staging/'index.json').write_text(_json(index)+'\n')
        _publish(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination
