"""Traceable HUD control episodes, without smoothing or physical interpretation."""
from dataclasses import asdict
import math

from acc_telemetry.analysis.perception import EventSettings, _fresh, control_events

FIELDS = ('brake_pct', 'throttle_pct')


def _point(row):
    return dict(frame=row.frame, time_s=row.time_s)


def _valid(row, field):
    return _fresh(row, field) and 0 <= getattr(row, field) <= 100


def _runs(samples, field, settings, fps):
    """Split at every absent/invalid sample, including absent frame IDs."""
    runs, gaps, current = [], [], []
    for i, row in enumerate(samples):
        previous = samples[i - 1] if i else None
        if previous and (row.frame != previous.frame + 1 or
                         row.time_s - previous.time_s > settings.max_gap_s + 1e-12):
            if current:
                runs.append(current)
                current = []
            gaps.append(dict(field=field, kind='sampling_gap',
                             after=_point(previous), before=_point(row)))
        if _valid(row, field):
            current.append(row)
        else:
            if current:
                runs.append(current)
                current = []
            reasons = sorted(set(row.field_reasons.get(field, ())) | {'not_fresh_or_out_of_range'})
            if gaps and gaps[-1]['kind'] == 'invalid_samples' and gaps[-1]['end_frame_exclusive'] == row.frame:
                gaps[-1]['end_frame_exclusive'] = row.frame + 1
                gaps[-1]['end_time_s'] = row.time_s + 1 / fps
                gaps[-1]['reasons'] = sorted(set(gaps[-1]['reasons'] + reasons))
            else:
                gaps.append(dict(field=field, kind='invalid_samples', start_frame=row.frame,
                                 end_frame_exclusive=row.frame + 1, start_time_s=row.time_s,
                                 end_time_s=row.time_s + 1 / fps, reasons=reasons))
    if current:
        runs.append(current)
    return runs, gaps


def _episode(rows, start, end, run_id, left_reason, right_reason):
    active = [r for r in rows if r.frame >= start['frame'] and
              (end is None or r.frame < end['frame'])]
    first, last = active[0], active[-1]
    field = start['field']
    left = start['type'].endswith('active_unbounded')
    finish = next(r for r in rows if r.frame == end['frame']) if end else last
    peak = max(getattr(r, field) for r in active)
    peaks = [r for r in active if getattr(r, field) == peak]
    bounded = not left and end is not None
    tail_s = finish.time_s - peaks[-1].time_s if end else None
    profile = active + ([finish] if end else [])
    return dict(
        id=f"{field}-episode-{first.frame}", field=field, run_id=run_id,
        start_candidate=None if left else start, initial_active_evidence=start if left else None,
        end_candidate=end, observed_start=_point(first), observed_end=_point(finish),
        left_truncated=left, right_truncated=end is None,
        truncation_reasons=([left_reason] if left else []) + ([right_reason] if end is None else []),
        quality=dict(status='candidate_hud_episode', complete_boundaries=bounded,
                     continuous_fresh_samples=True, physical_accuracy='not_qualified',
                     reasons=sorted({reason for r in rows if first.frame <= r.frame <=
                                     (end['confirmed_frame'] if end else last.frame)
                                     for reason in r.field_reasons.get(field, ())})),
        metrics=dict(duration_s=finish.time_s - first.time_s if bounded else None,
                     observed_span_s=finish.time_s - first.time_s,
                     observed_peak_pct=peak, first_peak=_point(peaks[0]), last_peak=_point(peaks[-1]),
                     time_to_first_peak_s=peaks[0].time_s - first.time_s if not left else None,
                     terminal_tail_s=tail_s,
                     terminal_tail_mean_slope_pct_per_s=(getattr(finish, field) - peak) / tail_s
                     if tail_s is not None and tail_s > 0 else None,
                     release_onset_s=None),
        raw_profile=dict(start_frame=first.frame, end_frame_inclusive=finish.frame,
                         sample_count=len(profile), field=field),
        # The tail is a descriptor from the LAST exact observed maximum, not detected release onset.
        terminal_tail=dict(start=_point(peaks[-1]), end=_point(finish) if end else None,
                           definition='last exact observed maximum to off candidate; raw profile may rise again'),
    )


def build_control_episodes(samples, settings=None, *, fps=60):
    settings = settings or EventSettings()
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ValueError('invalid frame rate')
    samples = list(samples)
    for i, row in enumerate(samples):
        if (type(row.frame) is not int or row.frame < 0 or not math.isfinite(row.time_s) or
                (i and (row.frame <= samples[i - 1].frame or row.time_s <= samples[i - 1].time_s or
                        not math.isclose(row.time_s - samples[i - 1].time_s,
                                         (row.frame - samples[i - 1].frame) / fps, abs_tol=1e-8)))):
            raise ValueError('samples must have ordered native frame/time coordinates')
    episodes, events, gaps, resumptions = [], [], [], []
    for field in FIELDS:
        runs, field_gaps = _runs(samples, field, settings, fps)
        gaps.extend(field_gaps)
        for run in runs:
            run_id = f'{field}-run-{run[0].frame}'
            candidates = control_events(run, field, settings)
            events.extend(candidates)
            start = None
            run_episodes = []
            for event in candidates:
                if event['type'].endswith(('_on', '_active_unbounded')):
                    start = event
                elif start is not None:
                    run_episodes.append(_episode(run, start, event, run_id,
                                                'session_start' if run[0] == samples[0] else 'evidence_gap',
                                                'evidence_gap'))
                    start = None
            if start is not None:
                run_episodes.append(_episode(run, start, None, run_id,
                                            'session_start' if run[0] == samples[0] else 'evidence_gap',
                                            'session_end' if run[-1] == samples[-1] else 'evidence_gap'))
            for previous, following in zip(run_episodes, run_episodes[1:]):
                off, on = previous['end_candidate'], following['start_candidate']
                resumptions.append(dict(field=field, previous_episode_id=previous['id'],
                                        next_episode_id=following['id'], off_candidate=off, on_candidate=on,
                                        inactive_interval_s=on['time_s'] - off['time_s'],
                                        meaning='successive threshold episodes in one evidence run; not voluntary reapplication'))
            episodes.extend(run_episodes)
    overlaps = []
    brakes = [e for e in episodes if e['field'] == 'brake_pct']
    throttles = [e for e in episodes if e['field'] == 'throttle_pct']
    for brake in brakes:
        for throttle in throttles:
            start = max((brake['observed_start'], throttle['observed_start']), key=lambda p: p['time_s'])
            end = min((brake['observed_end'], throttle['observed_end']), key=lambda p: p['time_s'])
            if start['time_s'] < end['time_s']:
                overlaps.append(dict(brake_episode_id=brake['id'], throttle_episode_id=throttle['id'],
                                     start=start, end=end, observed_duration_s=end['time_s'] - start['time_s'],
                                     boundary_limited=any(e['left_truncated'] or e['right_truncated']
                                                          for e in (brake, throttle)),
                                     meaning='intersection of candidate hysteresis states; not simultaneous physical pedal use'))
    return dict(schema_version='control-episodes-v1', gate_a='FAIL', coaching_eligible=False,
                event_settings=asdict(settings), fps=fps,
                episodes=sorted(episodes, key=lambda e: (e['observed_start']['frame'], e['field'])),
                events=sorted(events, key=lambda e: (e['frame'], e['type'])),
                gaps=gaps, resumptions=resumptions, overlaps=overlaps)
