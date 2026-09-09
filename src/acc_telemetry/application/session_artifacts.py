"""Atomic, versioned local evidence artifacts; no automatic coaching admission."""
import csv
import ctypes
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from acc_telemetry.domain.observations import FieldObservation, FrameObservation
from acc_telemetry.domain.progress import ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag, TelemetrySample
from acc_telemetry.normalization.samples import load_csv_samples

SCHEMA = 'telemetry-v2'
PAYLOADS = ('observations.jsonl', 'samples.jsonl', 'telemetry.csv')


def _plain(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _json(value):
    return json.dumps(_plain(value), allow_nan=False, sort_keys=True, ensure_ascii=False)


def _read_json(text):
    def reject(value):
        raise ValueError(f'non-finite JSON: {value}')
    value = json.loads(text, parse_constant=reject)
    _json(value)  # also reject numeric overflow such as 1e999
    return value


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def source_identity(path):
    path = Path(path).resolve(strict=True)
    before = path.stat()
    digest = _sha(path)
    after = path.stat()
    if any(getattr(before, field) != getattr(after, field) for field in
           ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')):
        raise ValueError('source changed during hashing')
    return {'path': str(path), 'size_bytes': before.st_size, 'sha256': digest}


def _check_speed_review_source(config, source):
    # Missing review is valid for older artifacts; never retroactively grant it.
    review = config.get('speed_visibility')
    if review is not None and (not isinstance(review, dict)
            or review.get('source_sha256') != source['sha256']
            or review.get('source_size_bytes') != source['size_bytes']):
        raise ValueError('speed visibility does not match artifact source')


def probe_timebase(path):
    """Check every decoded PTS against nominal CFR within one stream tick.

    This validates timestamps only; pipeline decoding coverage is a separate A6 gate.
    """
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames',
               '-show_entries', 'stream=time_base,avg_frame_rate:frame=best_effort_timestamp',
               '-of', 'json', str(path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = _read_json(result.stdout)
        stream = data['streams'][0]
        tick = Fraction(stream['time_base'])
        rate = Fraction(stream['avg_frame_rate'])
        pts = [int(frame['best_effort_timestamp']) for frame in data['frames']]
        if len(pts) < 2 or rate <= 0 or tick <= 0:
            raise ValueError('insufficient timestamp evidence')
        monotonic = all(b > a for a, b in zip(pts, pts[1:]))
        residual = max(abs((pts[i] - pts[0]) * tick - Fraction(i, 1) / rate)
                       for i in range(len(pts)))
        return {'status': 'pass' if monotonic and residual <= tick and not result.stderr.strip() else 'fail',
                'frame_count': len(pts), 'fps': float(rate), 'time_base': str(tick),
                'first_pts_s': float(pts[0] * tick), 'last_pts_s': float(pts[-1] * tick),
                'max_cfr_residual_s': float(residual), 'tolerance_s': float(tick),
                'criterion': 'monotonic PTS, CFR residual <= one stream tick, no decoder errors'}
    except FileNotFoundError:
        return {'status': 'not_evaluated', 'reason': 'ffprobe_unavailable'}
    except (subprocess.CalledProcessError, ValueError, KeyError, IndexError, ZeroDivisionError):
        return {'status': 'fail', 'reason': 'invalid_or_unreadable_timestamp_evidence'}


def _code_identity():
    root = Path(__file__).resolve().parents[3]
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    return {'git_commit': git('rev-parse', 'HEAD'),
            'dirty': bool(git('status', '--porcelain')),
            'module_sha256': {str(p.relative_to(root)): _sha(p)
                for p in sorted((root / 'src' / 'acc_telemetry').rglob('*.py'))}}


def check_destination(destination, source_path):
    original = Path(destination).absolute()
    target = original.resolve()
    source = Path(source_path).resolve()
    if 'raw' in original.parts or 'raw' in target.parts or target == source:
        raise ValueError('artifact destination cannot be raw or source')
    if original.exists() or original.is_symlink() or target.exists():
        raise FileExistsError(str(original))
    return target


def _write_jsonl(path, rows):
    with path.open('x', encoding='utf-8') as handle:
        for row in rows:
            handle.write(_json(row) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def _publish(staging, target):
    """Atomic rename with kernel-enforced no replacement, including empty dirs."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        result = rename(os.fsencode(staging), os.fsencode(target), 4)  # RENAME_EXCL
    elif sys.platform.startswith('linux') and hasattr(libc, 'renameat2'):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        result = rename(-100, os.fsencode(staging), -100, os.fsencode(target), 1)  # NOREPLACE
    else:
        raise RuntimeError('atomic no-replace directory publication unsupported on this platform')
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def write_session_artifacts(result, destination, *, source_path, source_before,
                            profile, clip_origin=None):
    target = check_destination(destination, source_path)
    source = source_identity(source_path)
    if source != source_before:
        raise ValueError('source changed since extraction started')
    if (not result.records or len(result.samples) != len(result.records)
            or len(result.observations) != len(result.records) or result.resolved_config is None):
        raise ValueError('modern artifacts require aligned observations and explicit normalized settings')
    config = _plain(result.resolved_config)
    _check_speed_review_source(config, source)
    if profile not in config['settings']['profiles']:
        raise ValueError('profile absent from resolved settings')
    origin = clip_origin or {'source_id': source['sha256'], 'start_s': 0.0}
    start_s = origin['start_s']
    if not isinstance(origin['source_id'], str) or not origin['source_id'] or not math.isfinite(start_s) or start_s < 0:
        raise ValueError('invalid clip origin')
    # Validate every value, including CSV-only evidence, before any output is visible.
    _json(result.records)
    timebase = probe_timebase(source_path)
    manifest = {'schema_version': SCHEMA, 'source': source, 'source_id': source['sha256'],
                'profile': profile, 'clip_origin': origin, 'config': config,
                'config_sha256': hashlib.sha256(_json(config).encode()).hexdigest(),
                'code': _code_identity(), 'timebase': timebase,
                'video_info': result.video_info, 'frame_count': len(result.records),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'lap_transitions': result.lap_transitions,
                'coaching_eligible': False, 'gate_a': 'not_evaluated',
                'decode_coverage': 'not_evaluated'}
    def envelope(frame, time_s):
        return {'schema_version': SCHEMA, 'source_id': source['sha256'],
                'source_sha256': source['sha256'], 'profile': profile,
                'frame': frame, 'time_s': time_s, 'source_time_s': start_s + time_s}
    observations = []
    samples = []
    for record, obs, sample in zip(result.records, result.observations, result.samples):
        if (dict(sample.source_values) != record
                or obs.frame != sample.frame or obs.time_s != sample.time_s
                or record['frame'] != sample.frame or record['time'] != sample.time_s):
            raise ValueError('misaligned session evidence')
        observations.append(dict(envelope(obs.frame, obs.time_s), observations=obs.observations,
            field_quality={k: o.quality for k, o in obs.observations.items()},
            field_reasons={k: o.reasons for k, o in obs.observations.items()}))
        samples.append(dict(envelope(sample.frame, sample.time_s), sample=sample,
                            field_quality=sample.field_quality, field_reasons=sample.field_reasons))
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{target.name}-', dir=target.parent))
    try:
        _write_jsonl(staging / 'observations.jsonl', observations)
        _write_jsonl(staging / 'samples.jsonl', samples)
        with (staging / 'telemetry.csv').open('x', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(result.records[0]))
            writer.writeheader()
            writer.writerows(result.records)
        manifest['files'] = {name: _sha(staging / name) for name in PAYLOADS}
        (staging / 'manifest.json').write_text(_json(manifest) + '\n', encoding='utf-8')
        if source_identity(source_path) != source:
            raise ValueError('source changed while preparing artifacts')
        for name in (*PAYLOADS, 'manifest.json'):
            with (staging / name).open('rb') as handle:
                os.fsync(handle.fileno())
        _publish(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


@dataclass(frozen=True)
class LoadedSession:
    samples: tuple[TelemetrySample, ...]
    observations: tuple[FrameObservation, ...]
    manifest: dict
    coaching_eligible: bool = False


def _sample(data):
    data = dict(data)
    data['field_quality'] = MappingProxyType({k: QualityFlag(v) for k, v in data['field_quality'].items()})
    data['field_reasons'] = MappingProxyType({k: tuple(v) for k, v in data['field_reasons'].items()})
    data['source_values'] = MappingProxyType(data['source_values'])
    data['anomalies'] = tuple(data['anomalies'])
    data['s_reasons'] = tuple(data['s_reasons'])
    data['s_source'] = ProgressSource(data['s_source']) if data['s_source'] is not None else None
    return TelemetrySample(**data)


def read_session_artifacts(path, *, limits=None):
    path = Path(path)
    if path.is_file() and path.suffix.lower() == '.csv':
        if limits is None:
            raise ValueError('legacy CSV requires explicit normalization limits')
        return LoadedSession(tuple(load_csv_samples(path, limits)), (), {'schema_version': 'legacy'})
    manifest = _read_json((path / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != SCHEMA:
        raise ValueError('unsupported telemetry schema')
    _check_speed_review_source(manifest['config'], manifest['source'])
    if hashlib.sha256(_json(manifest['config']).encode()).hexdigest() != manifest['config_sha256']:
        raise ValueError('configuration integrity mismatch')
    rows = {}
    for name in PAYLOADS:
        if _sha(path / name) != manifest['files'][name]:
            raise ValueError(f'artifact integrity mismatch: {name}')
        if name.endswith('.jsonl'):
            rows[name] = [_read_json(line) for line in (path / name).read_text().splitlines()]
            for row in rows[name]:
                if (row['schema_version'] != SCHEMA or row['source_sha256'] != manifest['source']['sha256']
                        or row['source_id'] != manifest['source_id'] or row['profile'] != manifest['profile']):
                    raise ValueError('inconsistent evidence envelope')
                expected_time = manifest['clip_origin']['start_s'] + row['time_s']
                if row['source_time_s'] != expected_time:
                    raise ValueError('inconsistent source time')
                if name == 'samples.jsonl':
                    inner = row['sample']
                    if (row['frame'] != inner['frame'] or row['time_s'] != inner['time_s']
                            or row['field_quality'] != inner['field_quality']
                            or row['field_reasons'] != inner['field_reasons']):
                        raise ValueError('inconsistent sample envelope')
                else:
                    observed = row['observations']
                    if (row['field_quality'] != {k: v['quality'] for k, v in observed.items()}
                            or row['field_reasons'] != {k: v['reasons'] for k, v in observed.items()}):
                        raise ValueError('inconsistent observation envelope')
    samples = tuple(_sample(row['sample']) for row in rows['samples.jsonl'])
    observations = tuple(FrameObservation(row['frame'], row['time_s'], {
        k: FieldObservation(v['value'], QualityFlag(v['quality']), v['raw_value'],
                            tuple(v['reasons']), v['last_observed_time_s'])
        for k, v in row['observations'].items()}) for row in rows['observations.jsonl'])
    if len(samples) != len(observations) or len(samples) != manifest['frame_count']:
        raise ValueError('artifact row count mismatch')
    for sample, observation in zip(samples, observations):
        if sample.frame != observation.frame or sample.time_s != observation.time_s:
            raise ValueError('misaligned artifact rows')
    return LoadedSession(samples, observations, manifest)
