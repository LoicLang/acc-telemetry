"""Build a local full-lap perception package from frozen telemetry, without OCR."""
from dataclasses import asdict
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile

import cv2
from PIL import Image, ImageDraw
import yaml

from acc_telemetry.analysis.perception import EventSettings, select_lap, summarize_lap
from acc_telemetry.domain.telemetry import QualityFlag as Q
from acc_telemetry.application.session_artifacts import (
    check_destination, read_session_artifacts, source_identity, _publish,
)
from acc_telemetry.application.session_report import sha256
from acc_telemetry.extraction.video import probe_supported_capture


DEFAULT_SETTINGS=Path(__file__).resolve().parents[3]/'config/perception.yaml'


def load_event_settings(path=None):
    data=yaml.safe_load(Path(path or DEFAULT_SETTINGS).read_text())
    if not isinstance(data,dict) or set(data)!={'events'} or not isinstance(data['events'],dict):
        raise ValueError('perception configuration must contain events')
    try:return EventSettings(**data['events'])
    except TypeError as exc:raise ValueError('unknown event configuration key') from exc


def frame_sequence(start_s,end_s,step_s,fps,lo,hi):
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in (start_s,end_s,step_s,fps)):
        raise ValueError('nonfinite frame selection')
    if fps<=0 or step_s<1/fps or not lo/fps<=start_s<=end_s<hi/fps:
        raise ValueError('detail sequence must stay within the selected lap at native cadence')
    first=math.ceil(start_s*fps-1e-9);last=math.floor(end_s*fps+1e-9)
    frames=list(range(first,last+1,max(1,round(step_s*fps))))
    if not frames:raise ValueError('selection contains no native frame')
    return frames



def window_frames(start_s,end_s,fps,lo,hi):
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (start_s,end_s)):
        raise ValueError('nonfinite detail window')
    first=math.ceil(start_s*fps-1e-9);end=math.ceil(end_s*fps-1e-9)
    if not lo<=first<end<=hi:
        raise ValueError('detail window must contain native frames inside the lap')
    return first,end


def render_lap_video(source,target,lo,hi,fps):
    audio=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0',
        '-show_entries','stream=index','-of','json',str(source)],text=True))['streams']
    cmd=['ffmpeg','-nostdin','-n','-v','error','-i',str(source),'-map','0:v:0',
        '-vf',f'trim=start_frame={lo}:end_frame={hi},setpts=PTS-STARTPTS',
        '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p']
    if audio:
        cmd+=['-map','0:a:0','-af',f'atrim=start={lo/fps:.12f}:end={hi/fps:.12f},asetpts=PTS-STARTPTS','-c:a','aac']
    else:cmd+=['-an']
    cmd+=['-movflags','+faststart',str(target)]
    subprocess.run(cmd,check=True)
    info=probe_supported_capture(target)
    if info['presentation_frames']!=hi-lo:
        raise ValueError('rendered clip frame coverage mismatch')
    return info


def _images(source,frames,staging,by_frame):
    folder=staging/'detail';folder.mkdir()
    cap=cv2.VideoCapture(str(source));result=[]
    try:
        if not cap.isOpened():raise ValueError('cannot decode source detail')
        cap.set(cv2.CAP_PROP_POS_FRAMES,frames[0])
        wanted=set(frames)
        for frame in range(frames[0],frames[-1]+1):
            ok,bgr=cap.read()
            if not ok:raise ValueError('source detail ended before expected frame')
            if frame not in wanted:continue
            image=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
            relative=f'detail/frame-{frame}.png';image.save(staging/relative)
            result.append(dict(frame=frame,time_s=by_frame[frame]['time_s'],image=relative,
                image_sha256=sha256(staging/relative),values={k:by_frame[frame][k] for k in ('speed_kmh','brake_pct','throttle_pct','gear')}))
    finally:cap.release()
    sheets=[]
    for page,start in enumerate(range(0,len(result),6)):
        chunk=result[start:start+6];sheet=Image.new('RGB',(1440,310*math.ceil(len(chunk)/3)),(22,30,40));draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(chunk):
            x=i%3*480;y=i//3*310
            with Image.open(staging/row['image']) as native:sheet.paste(native.resize((480,270)),(x,y+35))
            draw.text((x+7,y+5),f"Frame {row['frame']} | source {row['time_s']:.3f}s | automatic measurements",fill='white')
        name=f'detail/sequence-{page+1}.jpg';sheet.save(staging/name,quality=95);sheets.append(name)
    return result,sheets


def write_perception(session_path,zones_path,output,*,lap_number=4,settings_path=None,
                     detail_start_s=39.,detail_end_s=57.,sequence_start_s=49.,sequence_end_s=51.,sequence_step_s=.1):
    session_path,zones_path=Path(session_path),Path(zones_path)
    settings=load_event_settings(settings_path)
    session=read_session_artifacts(session_path);m=session.manifest
    artifact_hashes={name:digest for name,digest in m['files'].items()}
    artifact_hashes['manifest.json']=sha256(session_path/'manifest.json')
    if (m['timebase']['status']!='pass' or m['timebase']['fps']!=60
            or (m['video_info']['width'],m['video_info']['height'])!=(1920,1080)):
        raise ValueError('perception requires native 1920x1080 at exactly60fps CFR')
    source=source_identity(m['source']['path'])
    if source!=m['source']:raise ValueError('source does not match the session artifact')
    target=check_destination(output,source['path'])
    if target.is_relative_to(session_path.resolve()):raise ValueError('output cannot be inside session artifacts')
    zone_bytes=zones_path.read_bytes();zones_digest=hashlib.sha256(zone_bytes).hexdigest()
    spec=json.loads(zone_bytes)
    if (spec.get('schema_version')!='perception-zones-v1' or spec.get('source_sha256')!=source['sha256']
            or spec.get('source_size_bytes')!=source['size_bytes'] or spec.get('lap_number')!=lap_number):
        raise ValueError('zones do not match the source/lap')
    if not isinstance(spec.get('review'),dict) or not spec['review'].get('author') or not spec['review'].get('limits'):
        raise ValueError('zones require attributed review and explicit boundary limits')
    for evidence in spec.get('evidence_images',[]):
        if sha256(zones_path.parent/evidence['path'])!=evidence['sha256']:
            raise ValueError('zone review image integrity mismatch')
    lap=select_lap(m,lap_number);fps=60
    selected,summary=summarize_lap(session.samples,lap,spec['zones'],settings,fps)
    detail_lo,detail_hi=window_frames(detail_start_s,detail_end_s,fps,lap['start_frame'],lap['end_frame'])
    frames=frame_sequence(sequence_start_s,sequence_end_s,sequence_step_s,fps,lap['start_frame'],lap['end_frame'])
    if not detail_start_s<=sequence_start_s<=sequence_end_s<detail_end_s:
        raise ValueError('image sequence must be inside the detailed window')
    # Packet/metadata check before any new video decoding or rendering.
    probe=probe_supported_capture(source['path'])
    origin=m['clip_origin']['start_s'];fields=('speed_kmh','brake_pct','throttle_pct','gear')
    rows=[dict(frame=s.frame,time_s=s.time_s,source_time_s=s.time_s+origin,
        **{f:getattr(s,f) for f in fields},quality={f:s.field_quality.get(f,Q.MISSING).value for f in fields},
        speed_raw=s.source_values.get('speed_raw'),gear_raw=s.source_values.get('gear_raw'),
        reasons={f:list(s.field_reasons.get(f,())) for f in fields}) for s in selected]
    zones=[dict(z,start_time_s=z['start_frame']/fps,end_time_s=z['end_frame']/fps) for z in spec['zones']]
    target.parent.mkdir(parents=True,exist_ok=True);staging=Path(tempfile.mkdtemp(prefix='.perception-',dir=target.parent))
    try:
        (staging/'video').mkdir()
        media=dict(lap=render_lap_video(source['path'],staging/'video/lap.mp4',lap['start_frame'],lap['end_frame'],fps),
            detail=render_lap_video(source['path'],staging/'video/detail.mp4',detail_lo,detail_hi,fps))
        images,sheets=_images(source['path'],frames,staging,{r['frame']:r for r in rows})
        payload=dict(schema_version='lap-perception-v1',status='experimental',gate_a='FAIL',coaching_eligible=False,
            source=source,source_artifact_manifest_sha256=sha256(session_path/'manifest.json'),
            source_artifact_gate_a=m.get('gate_a'),zones_sha256=zones_digest,format=probe,
            clip_origin=m['clip_origin'],lap=lap,zone_review=spec['review'],zones=zones,
            event_settings=asdict(settings),summary=summary,samples=rows,media=media,
            detail=dict(start_time_s=detail_lo/fps,end_time_s=detail_hi/fps,
                start_frame=detail_lo,end_frame=detail_hi,requested_window_s=[detail_start_s,detail_end_s],
                sequence_start_s=sequence_start_s,sequence_end_s=sequence_end_s,
                requested_step_s=sequence_step_s,frames=images,sheets=sheets),
            capabilities=dict(full_lap_overview=True,temporal_detail=True,lateral_position_d=False,
                steering_angle_validated=False,driving_diagnosis=False),
            limitations=['All numeric samples are automatic readings; continuous correctness is not validated.',
                'Zone boundaries are coarse routing windows, not timing landmarks.',
                'Neutral events are candidates; threshold persistence is not measured event latency.',
                'Pedal bias/residuals and automatic blips remain; no smoothing or rescaling.',
                'Frame-detail images are selected evidence, not an exhaustive visual review.',
                'Audio is contextual; fine synchronization concerns video frames and existing sample timestamps.'])
        (staging/'perception.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,indent=2))
        with (staging/'samples.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['frame','time_s','source_time_s',*fields,'quality','reasons','speed_raw','gear_raw']);writer.writeheader()
            for row in rows:writer.writerow(dict(row,quality=json.dumps(row['quality']),reasons=json.dumps(row['reasons'])))
        from acc_telemetry.visualization.perception import render_viewer, render_index
        (staging/'index.html').write_text(render_viewer(payload))
        (staging/'OBSERVATIONS.md').write_text(render_index(payload))
        if source_identity(source['path'])!=source:raise ValueError('source changed during rendering')
        if sha256(zones_path)!=zones_digest or any(sha256(session_path/name)!=digest for name,digest in artifact_hashes.items()):
            raise ValueError('input evidence changed during rendering')
        files={str(p.relative_to(staging)):sha256(p) for p in staging.rglob('*') if p.is_file()}
        (staging/'integrity.json').write_text(json.dumps(dict(files=files,source_unchanged=True,
            source_artifacts_unchanged=True,frame_mapping='rendered video frame i = lap.start_frame + i',
            duration_s=(lap['end_frame']-lap['start_frame'])/fps),indent=2))
        _publish(staging,target)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return target
