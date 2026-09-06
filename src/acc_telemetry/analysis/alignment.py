"""Pure, quality-aware interpolation on original temporal runs."""
import math
from collections import Counter
import numpy as np

CHANNELS = {'throttle': 'throttle_pct', 'brake': 'brake_pct', 'steering': 'steering',
            'speed': 'speed_kmh', 'time': None, 'frame': None}


def bounded_interpolate(x, y, targets, *, max_x_gap):
    x, y, targets = (np.asarray(a, dtype=float) for a in (x, y, targets))
    if (x.ndim != 1 or y.ndim != 1 or len(x) != len(y) or len(x) < 2
            or not np.all(np.diff(x) > 0)):
        raise ValueError('expected increasing paired observations')
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError('non-finite observations')
    if not math.isfinite(max_x_gap) or max_x_gap <= 0:
        raise ValueError('invalid interpolation gap')
    result = np.full(targets.shape, np.nan)
    for j, t in np.ndenumerate(targets):
        if not np.isfinite(t):
            continue
        i = int(np.searchsorted(x, t))
        if i < len(x) and x[i] == t:
            result[j] = y[i]
        elif 0 < i < len(x) and x[i] - x[i-1] <= np.nextafter(max_x_gap, np.inf):
            f = (t - x[i-1]) / (x[i] - x[i-1])
            result[j] = y[i-1] + f * (y[i] - y[i-1])
    return result


def _number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _hints(row):
    value = row.get('quality_hint')
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return {}
    return dict(item.split(':', 1) for item in str(value).split(';') if ':' in item)


def confirmed_start_time(records):
    times = [row['time'] for row in records if
             'lap_boundary_confirmed' in str(row.get('s_reasons', '')).split(';')]
    return _number(times[0]) if len(times) == 1 else None


def resample_records(records, targets, *, max_position_gap_s, max_time_gap_s,
                     max_s_uncertainty=None, coaching=False, progress_gate_passed=False,
                     lap_start_time_s=None):
    """Never sort/remove holes before splitting; overlapping passages are ambiguous.

    Targets and position gap use normalized s, not seconds or physical metres.
    The gate argument is trusted caller context, never an input CSV claim.
    """
    if not 0 < max_position_gap_s <= 1 or not math.isfinite(max_time_gap_s) or max_time_gap_s <= 0:
        raise ValueError('invalid alignment limits')
    targets = np.asarray(targets, dtype=float)
    if targets.ndim != 1 or not np.all(np.isfinite(targets)):
        raise ValueError('expected finite target vector')
    positions = []
    for row in records:
        if 's_fused' in row or 's_source' in row:
            positions.append(_number(row.get('s_fused')))
        else:
            percent = _number(row.get('track_position'))
            positions.append(None if percent is None else percent / 100)
    repeated = Counter(p for p in positions if p is not None)
    times = [_number(row.get('time')) for row in records]
    hints = [_hints(row) for row in records]
    position_ok = []
    for i, row in enumerate(records):
        p = positions[i]
        modern = 's_source' in row or 's_fused' in row
        flag = row.get('s_source') if modern else hints[i].get('s', 'legacy_unverified')
        accepted = flag in ('observed', 'legacy_unverified') and (not coaching or flag == 'observed')
        if flag in ('fused', 'predicted', 'interpolated'):
            uncertainty = _number(row.get('s_uncertainty'))
            accepted = (not coaching or progress_gate_passed) and uncertainty is not None and (
                max_s_uncertainty is not None and uncertainty < max_s_uncertainty)
        if hints[i].get('s') in ('held', 'missing', 'anomalous'):
            accepted = False
        position_ok.append(p is not None and 0 <= p <= 1 and repeated[p] == 1
                           and times[i] is not None and accepted)
    result = {'position': targets * 100}
    for channel, quality_name in CHANNELS.items():
        output = np.full(targets.shape, np.nan)
        quality = np.full(targets.shape, 'missing', dtype=object)
        run_ids = np.full(targets.shape, -1, dtype=int)
        claims = np.zeros(targets.shape, dtype=int)
        runs, current = [], []
        for i, row in enumerate(records):
            value = _number(row.get(channel))
            flag = hints[i].get(quality_name, 'legacy_unverified') if quality_name else 'observed'
            good = position_ok[i] and value is not None and (
                flag == 'observed' or (not coaching and flag == 'legacy_unverified'))
            connected = not current or (good and positions[i] > positions[current[-1]]
                and positions[i] - positions[current[-1]] <= np.nextafter(max_position_gap_s, np.inf)
                and 0 < times[i] - times[current[-1]] <= np.nextafter(max_time_gap_s, np.inf))
            if not good or not connected:
                if current:
                    runs.append(current)
                current = []
            if good:
                current.append(i)
        if current:
            runs.append(current)
        for run_id, run in enumerate(runs):
            x = np.array([positions[i] for i in run])
            y = np.array([float(records[i][channel]) for i in run])
            values = (bounded_interpolate(x, y, targets, max_x_gap=max_position_gap_s)
                      if len(run) > 1 else np.where(targets == x[0], y[0], np.nan))
            valid = np.isfinite(values)
            claims[valid] += 1
            output[valid] = values[valid]
            run_ids[valid] = run_id
            quality[valid] = 'interpolated'
            for i in run:
                exact = valid & (targets == positions[i])
                quality[exact] = hints[i].get(quality_name, 'legacy_unverified') if quality_name else 'observed'
        ambiguous = claims > 1
        output[ambiguous] = np.nan
        quality[ambiguous] = 'ambiguous'
        run_ids[ambiguous] = -1
        result[channel] = output
        result[channel + '_quality'] = quality
        result[channel + '_run'] = run_ids
    start = _number(lap_start_time_s) if lap_start_time_s is not None else confirmed_start_time(records)
    result['lap_start_time_s'] = np.full(targets.shape, np.nan if start is None else start)
    return result


def common_time_delta(a, b):
    if not np.array_equal(a['position'], b['position']):
        raise ValueError('time delta requires a common position grid')
    result = np.full(len(a['position']), np.nan)
    if 'lap_start_time_s' not in a or 'lap_start_time_s' not in b:
        return result
    ta, tb, sa, sb = (np.asarray(value, dtype=float) for value in
                     (a['time'], b['time'], a['lap_start_time_s'], b['lap_start_time_s']))
    valid = np.isfinite(ta) & np.isfinite(tb) & np.isfinite(sa) & np.isfinite(sb)
    result[valid] = (ta[valid] - sa[valid]) - (tb[valid] - sb[valid])
    return result
