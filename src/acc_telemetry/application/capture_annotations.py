"""Prepare unlabelled, source-bound review material without any OCR inference."""
import json
import shutil
import tempfile
import uuid
from pathlib import Path

import cv2

from acc_telemetry.analysis.validation import validate_annotations, validate_windows
from acc_telemetry.extraction.video import preflight_capture, presentation_packets, validate_capture_probe
from .session_artifacts import source_identity, check_destination, _publish, _json, _read_json
from .validation_config import load_validation_settings


def _blank_frame(frame,time_s):
    return dict(frame=frame,time_s=time_s,speed_text=None,gear_text=None,lap_text=None,
        throttle_pct=None,brake_pct=None,pedal_tolerance_pct=None,
        visibility={k:None for k in ('speed','gear','lap_number','throttle','brake','steering')},
        degraded=None,reviewed=False)


def prepare_annotations(video,profile,output,*,settings=None,selection=None,role='development',progress=None,probe_evidence=None):
    settings=settings or load_validation_settings()
    if profile not in settings.resolutions or role not in ('development','holdout'):
        raise ValueError('unsupported profile or source role')
    video=Path(video)
    output=Path(output)
    source=source_identity(video)
    if selection is None:
        target=check_destination(output,video)
        if progress:
            progress('Reading FFprobe timestamps; no OCR is run')
        try:
            if probe_evidence is None:
                raw,capture=preflight_capture(video,expected_resolution=settings.resolutions[profile])
            else:
                cached=_read_json(Path(probe_evidence).read_text())
                if cached['source']!=source or cached['profile']!=profile:
                    raise ValueError('cached probe source/profile mismatch')
                raw=cached['ffprobe']
                raw['packets']=presentation_packets(video)
                capture=validate_capture_probe(raw,expected_resolution=settings.resolutions[profile])
        except ValueError as error:
            if hasattr(error,'raw_probe'):
                target.parent.mkdir(parents=True,exist_ok=True)
                failure=target.with_name(target.name+'-failed-'+uuid.uuid4().hex[:12]+'.json')
                with failure.open('x',encoding='utf-8') as handle:
                    handle.write(_json(dict(status='fail',reason=str(error),source=source,
                        profile=profile,ffprobe=error.raw_probe))+'\n')
                error.add_note(f'Preflight evidence: {failure}')
            raise
        manifest=dict(source=source,profile=profile,capture=capture)
        indices=[]
        next_time=0.
        for i,time in enumerate(capture['timestamps']):
            if time>=next_time:
                indices.append(i)
                next_time+=settings.selection_step_s
        windows=[]
    else:
        manifest=_read_json((output/'capture.json').read_text())
        raw=_read_json((output/'ffprobe.json').read_text())
        if manifest['source']!=source or manifest['profile']!=profile:
            raise ValueError('selection source/profile mismatch')
        capture=manifest['capture']
        parent_labels=_read_json((output/'labels.json').read_text())
        role=parent_labels['role']
        selected=_read_json(Path(selection).read_text())
        windows=validate_windows(selected['windows'],capture['frame_count'])
        if not windows:
            raise ValueError('select at least one frame window')
        indices=[i for w in windows for i in range(w['frame_lo'],w['frame_hi']+1)]
        target=check_destination(output/('frames-'+uuid.uuid4().hex[:12]),video)
    target.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.'+target.name+'-',dir=target.parent))
    cap=None
    try:
        (staging/'frames').mkdir()
        cap=cv2.VideoCapture(str(video))
        if not cap.isOpened():
            raise ValueError('incomplete_decode: OpenCV cannot open capture')
        entries=[]
        for n,i in enumerate(indices):
            if not cap.set(cv2.CAP_PROP_POS_FRAMES,i):
                raise ValueError('incomplete_decode: frame seek failed')
            ok,frame=cap.read()
            if not ok or int(cap.get(cv2.CAP_PROP_POS_FRAMES))!=i+1:
                raise ValueError('incomplete_decode: selected frame unavailable')
            if (frame.shape[1],frame.shape[0])!=tuple(settings.resolutions[profile]):
                raise ValueError('unsupported_resolution')
            image=frame if selection else cv2.resize(frame,(480,270))
            if not cv2.imwrite(str(staging/'frames'/f'{i:08d}.png'),image):
                raise ValueError('image export failed')
            entries.append(_blank_frame(i,capture['timestamps'][i]))
            if progress and n%20==0:
                progress(f'Prepared {n+1}/{len(indices)} images')
        labels=dict(schema_version='capture-annotations-v1',source_sha256=source['sha256'],
                    role=role,recording_id=None,annotator=None,reviewed=False,frames=entries,passages=[],
                    windows=windows,visibility=[])
        for name,data in (('capture.json',manifest),('ffprobe.json',raw),('labels.json',labels),
                          ('selection.json',{'windows':windows})):
            (staging/name).write_text(_json(data)+'\n',encoding='utf-8')
        board='<!doctype html><meta charset="utf-8"><title>Capture review selection</title>'
        board+='<style>body{font:16px system-ui;background:#181818;color:#eee}main{display:flex;flex-wrap:wrap}figure{margin:8px}img{width:480px;max-width:90vw}</style>'
        board+='<h1>Unreviewed selection — no inferred labels</h1><p>Frames and times below identify source evidence. Choose windows in selection.json. First pass images are thumbnails; second pass exports native frames.</p><main>'
        for row in entries:
            name=f"frames/{row['frame']:08d}.png"
            board+=f'<figure><a href="{name}"><img src="{name}" loading="lazy"></a><figcaption>Frame {row["frame"]} — {row["time_s"]:.6f} s</figcaption></figure>'
        (staging/'selection.html').write_text(board+'</main>',encoding='utf-8')
        (staging/'REVIEW.txt').write_text(
            'No labels are inferred. Select windows in selection.json, then call prepare with --selection.\n'
            'Second pass writes a NEW child folder containing native frames and its own labels.json.\n'
            'Review frame text/pedals/visibility and physical passage intervals; leave unreadable values null.\n'
            'Set row reviewed flags, annotator and top-level reviewed only after human review.\n'
            'Use one role per SOURCE, never neighboring frames split between development and holdout.\n'
            'Corpus minimum: 100 readable frames per speed/brake/throttle, 20 degraded frames,\n'
            '20 pedal-event windows, at least two sources and repeated physical passages.\n'
            'Previously inspected/tuned sources cannot establish an untouched holdout.\n')
        if source_identity(video)!=source:
            raise ValueError('source changed while preparing annotations')
        _publish(staging,target)
    finally:
        if cap is not None:
            cap.release()
        if staging.exists():
            shutil.rmtree(staging)
    return target


def validate_annotation_file(path):
    path=Path(path)
    labels=_read_json(path.read_text())
    manifest=_read_json((path.parent/'capture.json').read_text())
    report=validate_annotations(labels,manifest['capture'],source_sha256=manifest['source']['sha256'])
    if report['status']!='pass':
        return report
    output=path.parent/'visibility.json'
    check_destination(output,manifest['source']['path'])
    with output.open('x',encoding='utf-8') as handle:
        handle.write(_json(report['visibility'])+'\n')
    return report
