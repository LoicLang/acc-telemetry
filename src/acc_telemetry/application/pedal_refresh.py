"""Refresh only fresh automatic pedal readings in a complete native session."""
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile

import cv2

from acc_telemetry.application.config import load_settings
from acc_telemetry.application.session_artifacts import (
    PAYLOADS, _code_identity, _json, _plain, _publish, _sha,
    check_destination, read_session_artifacts, source_identity,
)
from acc_telemetry.extraction.controls import TelemetryExtractor
from acc_telemetry.extraction.video import probe_supported_capture

PEDALS = {'brake_pct': 'brake', 'throttle_pct': 'throttle'}


def replace_pedals(sample_envelope, observation_envelope, readings):
    """Preserve all other evidence and prior abstentions; fail on new missing reads."""
    sample_row, obs_row = copy.deepcopy(sample_envelope), copy.deepcopy(observation_envelope)
    sample = sample_row['sample']
    for field, channel in PEDALS.items():
        old = obs_row['observations'][field]
        if old['quality'] != 'observed' or sample['field_quality'][field] != 'observed':
            continue
        if old['value'] != sample[field] or old['value'] is None:
            raise ValueError('unsupported prior pedal normalization')
        value = readings[channel].value
        if readings[channel].quality.value != 'observed' or value is None or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError('pedal refresh lost previously fresh evidence')
        sample[field] = value
        sample['source_values'][channel] = value
        old['value'] = value
        old['raw_value'] = readings[channel].raw_value
    return sample_row, obs_row


def refresh_pedals(session_path, output, *, progress=None):
    parent = Path(session_path).resolve()
    session = read_session_artifacts(parent)
    original = session.manifest
    if (original['profile'] != 'ps5_full_map_1080p' or
            original['config'].get('measurement_mode') != 'automatic' or
            original['clip_origin']['start_s'] != 0 or original['timebase']['status'] != 'pass'):
        raise ValueError('refresh supports complete automatic native1080p sessions at clip origin zero')
    source = source_identity(original['source']['path'])
    if source != original['source']:
        raise ValueError('source identity mismatch')
    target = check_destination(output, source['path'])
    if target.is_relative_to(parent):
        raise ValueError('output cannot be inside parent artifacts')
    # Read packet metadata BEFORE any new video decoding. Never resample or resize.
    probe = probe_supported_capture(source['path'])
    if probe['presentation_frames'] != len(session.samples):
        raise ValueError('parent must cover the complete source')
    for i, row in enumerate(session.samples):
        if row.frame != i or not math.isclose(row.time_s, i / 60, abs_tol=1e-8):
            raise ValueError('parent frame/time coverage mismatch')
    inputs = {str(parent / name): digest for name, digest in original['files'].items()}
    inputs[str(parent / 'manifest.json')] = _sha(parent / 'manifest.json')
    rois = _plain(load_settings().profile(original['profile']).rois)
    old_rois = original['config']['settings']['profiles'][original['profile']]['rois']
    manifest = copy.deepcopy(original)
    for channel in PEDALS.values():
        manifest['config']['settings']['profiles'][original['profile']]['rois'][channel] = rois[channel]
    manifest['config_sha256'] = hashlib.sha256(_json(manifest['config']).encode()).hexdigest()
    manifest.update(code=_code_identity(), created_at=datetime.now(timezone.utc).isoformat(),
                    gate_a='FAIL', coaching_eligible=False)
    manifest['pedal_refresh'] = dict(
        schema_version='pedal-refresh-v1', parent_path=str(parent), input_sha256=inputs,
        parent_code=original['code'], refreshed_fields=list(PEDALS),
        policy='Only fresh observed pedals replaced; prior non-observed evidence preserved; all other channels reused.',
        format=probe, ocr_replayed=False, source_identity_verified=True,
        old_rois={c: old_rois[c] for c in PEDALS.values()}, new_rois={c: rois[c] for c in PEDALS.values()})
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.pedal-refresh-', dir=target.parent))
    cap = None
    try:
        cap = cv2.VideoCapture(source['path'])
        if not cap.isOpened():
            raise ValueError('cannot decode source')
        extractor = TelemetryExtractor()
        old_matches = 0
        with (parent/'samples.jsonl').open() as samples_in, (parent/'observations.jsonl').open() as obs_in, \
                (parent/'telemetry.csv').open(newline='') as csv_in, \
                (staging/'samples.jsonl').open('w') as samples_out, (staging/'observations.jsonl').open('w') as obs_out, \
                (staging/'telemetry.csv').open('w', newline='') as csv_out:
            reader = csv.DictReader(csv_in)
            writer = csv.DictWriter(csv_out, fieldnames=reader.fieldnames)
            writer.writeheader()
            for i in range(len(session.samples)):
                ok, image = cap.read()
                if not ok or image.shape[:2] != (1080, 1920):
                    raise ValueError(f'incomplete or wrong-sized decode at frame {i}')
                if not math.isclose(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, i / 60, abs_tol=1e-5):
                    raise ValueError(f'decoder timestamp mismatch at frame {i}')
                sample, obs, record = json.loads(next(samples_in)), json.loads(next(obs_in)), next(reader)
                def crop(r):
                    return image[r['y']:r['y']+r['height'], r['x']:r['x']+r['width']]
                fresh = extractor.observe_frame_telemetry(
                    {c: crop(rois[c]) for c in PEDALS.values()}, time_s=i/60, visibility=(), allow_unreviewed=True)
                # Replay the old pedal geometry alongside the new one as an alignment/regression check.
                for field, channel in PEDALS.items():
                    old = obs['observations'][field]
                    if old['quality'] == 'observed':
                        value = extractor.extract_bar_percentage(crop(old_rois[channel]),
                                    'green' if channel == 'throttle' else 'red', 'horizontal')
                        if value != old['value']:
                            raise ValueError(f'old pedal reading mismatch at {i}: {field}')
                        old_matches += 1
                sample, obs = replace_pedals(sample, obs, fresh)
                for field, channel in PEDALS.items():
                    # Existing CSV text for untouched/missing fields is retained exactly.
                    if sample['sample']['field_quality'][field] == 'observed' and obs['observations'][field]['quality'] == 'observed':
                        record[channel] = sample['sample']['source_values'][channel]
                samples_out.write(_json(sample)+'\n')
                obs_out.write(_json(obs)+'\n')
                writer.writerow(record)
                if progress and (i + 1) % 3000 == 0:
                    progress(i + 1, len(session.samples))
            if cap.read()[0] or next(samples_in, None) or next(obs_in, None) or next(reader, None):
                raise ValueError('extra source/artifact frames')
        manifest['pedal_refresh']['old_readings_reproduced'] = old_matches
        manifest['pedal_refresh']['decoded_frames'] = len(session.samples)
        manifest['files'] = {name: _sha(staging/name) for name in PAYLOADS}
        (staging/'manifest.json').write_text(_json(manifest)+'\n')
        read_session_artifacts(staging)
        if source_identity(source['path']) != source or any(_sha(Path(p)) != h for p, h in inputs.items()):
            raise ValueError('source or parent artifacts changed')
        _publish(staging, target)
    finally:
        if cap is not None:
            cap.release()
        if staging.exists():
            shutil.rmtree(staging)
    return target
