"""Episode boundaries, missing evidence and temporal arithmetic regressions."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_perception import sample
from acc_telemetry.analysis.control_episodes import build_control_episodes
from acc_telemetry.analysis.perception import control_events, EventSettings
from acc_telemetry.application.control_episodes import compare_annotations, write_control_episodes
from acc_telemetry.domain.telemetry import QualityFlag as Q


def rows(values, field='brake_pct'):
    return [sample(i, **{field.removesuffix('_pct'): value}) for i, value in enumerate(values)]


class TestControlEpisodes(unittest.TestCase):
    def test_complete_episode_candidate_times_peak_and_release(self):
        data = rows([0]*8 + [20]*7 + [80]*8 + [40]*8 + [0]*8)
        before = list(data)
        result = build_control_episodes(data)
        episode, = result['episodes']
        self.assertEqual(episode['start_candidate']['frame'], 8)
        self.assertEqual(episode['start_candidate']['confirmed_frame'], 14)
        self.assertEqual(episode['end_candidate']['frame'], 31)
        self.assertAlmostEqual(episode['metrics']['duration_s'], 23/60)
        self.assertEqual(episode['metrics']['observed_peak_pct'], 80)
        self.assertAlmostEqual(episode['metrics']['time_to_first_peak_s'], 7/60)
        self.assertEqual(episode['metrics']['last_peak']['frame'], 22)
        self.assertAlmostEqual(episode['metrics']['terminal_tail_s'], 9/60)
        self.assertAlmostEqual(episode['metrics']['terminal_tail_mean_slope_pct_per_s'], -80/(9/60))
        self.assertIsNone(episode['metrics']['release_onset_s'])
        self.assertEqual(result['events'], control_events(data, 'brake_pct', EventSettings()))
        self.assertEqual(data, before)

    def test_both_session_edges_truncated_and_zero_span_is_not_duration(self):
        episode, = build_control_episodes(rows([94]))['episodes']
        self.assertTrue(episode['left_truncated'] and episode['right_truncated'])
        self.assertIsNone(episode['metrics']['duration_s'])
        self.assertIsNone(episode['metrics']['time_to_first_peak_s'])
        self.assertIsNone(episode['metrics']['terminal_tail_s'])
        self.assertEqual(episode['metrics']['observed_span_s'], 0)
        self.assertEqual(episode['metrics']['observed_peak_pct'], 94)

    def test_missing_held_and_invalid_split_instead_of_pairing_across_gap(self):
        for bad in (None, -1, 101, float('nan')):
            data = rows([0]*8 + [80]*8 + [bad] + [80]*8 + [0]*8)
            result = build_control_episodes(data)
            a, b = result['episodes']
            self.assertTrue(a['right_truncated'])
            self.assertTrue(b['left_truncated'])
            self.assertIsNone(a['metrics']['duration_s'])
            self.assertIsNone(b['metrics']['duration_s'])
            self.assertEqual(result['resumptions'], [])
            self.assertEqual(result['gaps'][0]['start_frame'], 16)
        data[16] = replace(sample(16, brake=80), field_quality={'brake_pct': Q.HELD})
        self.assertEqual(len(build_control_episodes(data)['episodes']), 2)

    def test_absent_frame_smaller_than_max_gap_still_splits(self):
        data = rows([0]*8 + [80]*20 + [0]*8)
        del data[16]
        result = build_control_episodes(data)
        self.assertEqual(len(result['episodes']), 2)
        self.assertEqual(result['gaps'][0]['kind'], 'sampling_gap')

    def test_short_pulse_does_not_become_episode_and_pending_off_is_truncated(self):
        self.assertEqual(build_control_episodes(rows([0]*8 + [80]*3 + [0]*8))['episodes'], [])
        episode, = build_control_episodes(rows([0]*8 + [80]*8 + [0]*3))['episodes']
        self.assertTrue(episode['right_truncated'])
        self.assertIsNone(episode['end_candidate'])

    def test_resumption_only_after_confirmed_off_in_same_run(self):
        result = build_control_episodes(rows([0]*8 + [80]*8 + [0]*8 + [50]*8 + [0]*8))
        reprise, = result['resumptions']
        self.assertAlmostEqual(reprise['inactive_interval_s'], 8/60)
        self.assertEqual(reprise['on_candidate']['frame'], 24)

    def test_overlap_uses_onset_not_confirmation_and_can_be_zero(self):
        data = [sample(i, brake=80 if 8 <= i < 24 else 0,
                       throttle=94 if 16 <= i < 32 else 0) for i in range(40)]
        overlap, = build_control_episodes(data)['overlaps']
        self.assertEqual(overlap['start']['frame'], 16)
        self.assertEqual(overlap['end']['frame'], 24)
        self.assertAlmostEqual(overlap['observed_duration_s'], 8/60)
        self.assertFalse(overlap['boundary_limited'])
        data = [sample(i, brake=80 if 8 <= i < 24 else 0,
                       throttle=94 if 24 <= i < 32 else 0) for i in range(40)]
        self.assertEqual(build_control_episodes(data)['overlaps'], [])

    def test_missing_counterpart_is_not_reported_as_known_overlap(self):
        data = [sample(i, brake=80 if 8 <= i < 24 else 0, throttle=None) for i in range(40)]
        result = build_control_episodes(data)
        self.assertEqual(result['overlaps'], [])
        self.assertEqual(result['gaps'][0]['field'], 'throttle_pct')

    def test_reject_disordered_or_inconsistent_clocks(self):
        for data in ([sample(2), sample(1)], [sample(0), sample(0)], [sample(0), sample(1, time=1)]):
            with self.assertRaises(ValueError):
                build_control_episodes(data)
        self.assertEqual(build_control_episodes([])['episodes'], [])

    def test_sparse_labels_do_not_qualify_duration(self):
        data = rows([0]*8 + [80]*8 + [0]*8)
        payload = build_control_episodes(data)
        labels = dict(frames=[dict(frame=10, reviewed=True, brake_pct=85)],
                      passages=[dict(id='on', event_type='first_visible_brake', reviewed=True, frame_lo=7, frame_hi=8)],
                      evaluation_segments=[dict(id='window', frame_lo=0, frame_hi=20)])
        check = compare_annotations(payload, data, labels)
        self.assertEqual(check['points'][0]['error_pct'], -5)
        self.assertEqual(check['event_comparisons'][0]['candidate_minus_annotation_s'], [0, 1/60])
        self.assertIsNone(payload['episodes'][0]['annotation_evidence']['duration_accuracy_s'])

    def test_export_is_reproducible_preserves_missing_and_refuses_overwrite(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            session = root/'session'; session.mkdir()
            (session/'manifest.json').write_text('{}')
            m = dict(source=dict(path=str(root/'source.mov'), sha256='a', size_bytes=1), files={},
                     timebase=dict(status='pass', fps=60), video_info=dict(width=1920, height=1080),
                     clip_origin=dict(start_s=0))
            loaded = SimpleNamespace(manifest=m, samples=rows([0]*8+[80]*8+[None]+[0]*8))
            with patch('acc_telemetry.application.control_episodes.read_session_artifacts', return_value=loaded):
                a = write_control_episodes(session, root/'a')
                b = write_control_episodes(session, root/'b')
                self.assertEqual((a/'episodes.json').read_bytes(), (b/'episodes.json').read_bytes())
                raw = [json.loads(line) for line in (a/'pedal-samples.jsonl').read_text().splitlines()]
                self.assertIsNone(raw[16]['brake_pct'])
                self.assertEqual(raw[16]['quality']['brake_pct'], 'missing')
                with self.assertRaises(FileExistsError):
                    write_control_episodes(session, a)
                with self.assertRaises(ValueError):
                    write_control_episodes(session, session/'child')
                m['video_info']['height'] = 720
                with self.assertRaises(ValueError):
                    write_control_episodes(session, root/'wrong-format')
