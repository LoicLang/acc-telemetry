"""Independent capture validation targets, separate from coaching settings."""
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
import yaml


@dataclass(frozen=True)
class ValidationSettings:
    speed_mae_kmh: float
    speed_p95_kmh: float
    pedal_mae_pct: float
    event_p95_s: float
    min_coverage: float
    selection_step_s: float
    min_readable_frames: int
    min_degraded_frames: int
    min_event_windows: int
    min_sources: int
    min_passages_per_source: int
    event_matching_window_s: float
    fresh_crossing_max_gap_s: float
    pedal_crossing_pct: float
    resolutions: Mapping[str, tuple[int, int]]


def load_validation_settings(path=None):
    path = Path(path) if path else Path(__file__).resolve().parents[3] / 'config/validation.yaml'
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict) or set(raw) != set(ValidationSettings.__dataclass_fields__):
        raise ValueError('invalid validation settings fields')
    for key, value in raw.items():
        if key == 'resolutions':
            continue
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'invalid validation setting {key}')
        if key.startswith('min_') and key != 'min_coverage' and not isinstance(value,int):
            raise ValueError(f'expected integer for {key}')
    if raw['pedal_crossing_pct'] >= 100 or raw['min_coverage'] > 1 or raw['pedal_mae_pct'] > 100 or raw['speed_mae_kmh'] > raw['speed_p95_kmh']:
        raise ValueError('invalid validation limits')
    resolutions = raw['resolutions']
    if not isinstance(resolutions,dict) or not resolutions:
        raise ValueError('expected profile resolutions')
    for name, value in resolutions.items():
        if (not isinstance(name,str) or not name or not isinstance(value,list) or len(value)!=2
                or any(type(v) is not int or v<=0 for v in value)):
            raise ValueError('invalid profile resolution')
    raw['resolutions']=MappingProxyType({k:tuple(v) for k,v in resolutions.items()})
    return ValidationSettings(**raw)
