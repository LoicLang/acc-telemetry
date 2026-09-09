"""Speed visibility is source-bound evidence, not plausible OCR digits."""
import unittest
import hashlib
import json
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import numpy as np

from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.domain.telemetry import QualityFlag as Q
from test_application_pipeline import FakeVideo, FakeControls, FakeGenericProgress
from test_fresh_speed_observations import make_detector
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.speed_visibility import (
    SpeedVisibilityReview, SpeedVisibilitySpan, load_speed_visibility,
)
from acc_telemetry.application.session_artifacts import (
    read_session_artifacts, source_identity, write_session_artifacts, _json,
)


class TestSpeedVisibility(unittest.TestCase):
    def test_real_numeric_observation_without_visibility_abstains_with_raw(self):
        detector = make_detector()
        with patch('pytesseract.image_to_string', return_value='171\n') as backend:
            result = detector.observe_speed(np.full((10, 10, 3), 40, np.uint8))
        backend.assert_called_once()
        self.assertIsNone(result.value)
        self.assertEqual(result.quality, Q.MISSING)
        self.assertEqual(result.raw_value, '171\n')
        self.assertIn('speed_hud_unverified', result.reasons)

    def test_real_pipeline_without_review_does_not_send_digits_to_odometry(self):
        class Video(FakeVideo):
            def process_frames(self):
                self.current_frame = np.full((10, 10, 3), 40, np.uint8)
                yield 0, 0., {}
        progress = FakeGenericProgress()
        with patch('pytesseract.image_to_string', return_value='120\n') as backend:
            result = TelemetryPipeline(video=Video(), controls=FakeControls(),
                laps=make_detector(), progress=progress, has_track_map=False).run()
        backend.assert_called_once()
        self.assertIsNone(result.records[0]['speed'])
        self.assertEqual(result.records[0]['speed_raw'], '120\n')
        self.assertIsNone(progress.observations[0]['speed_kmh'])

    def test_source_bound_contexts_black_roi_return_and_artifact_provenance(self):
        times = [0., .1, .2, .3, .4, .5]
        texts = ['171\n', '120\n', '123\n', '99\n', '88\n', '0\n']
        expected = [171, None, None, None, None, 0]
        class Video(FakeVideo):
            def get_video_info(self):
                return dict(frame_count=6, fps=10., duration=.6)
            def process_frames(self):
                for i, time in enumerate(times):
                    self.current_frame = np.full((10, 10, 3), 0 if i == 4 else 40, np.uint8)
                    yield i, time, {}
        class Progress(FakeGenericProgress):
            def finalize(self):
                result = super().finalize()
                return replace(result, frames=tuple(replace(result.frames[0], frame=i) for i in range(6)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mov'
            source.write_bytes(b'synthetic source context fixture')
            identity = source_identity(source)
            review = SpeedVisibilityReview(identity['sha256'], identity['size_bytes'], (
                SpeedVisibilitySpan(0, .1, 'visible', 'fixture-reader'),
                SpeedVisibilitySpan(.1, .2, 'absent', 'menu-reviewer'),
                SpeedVisibilitySpan(.2, .3, 'unknown', 'uncertain-reviewer'),
                SpeedVisibilitySpan(.4, .6, 'visible', 'return-reviewer')))
            video = Video()
            video.video_path = str(source)
            progress = Progress()
            with patch('pytesseract.image_to_string', side_effect=texts) as backend:
                result = TelemetryPipeline(video=video, controls=FakeControls(), laps=make_detector(),
                    progress=progress, has_track_map=False, settings=load_settings(),
                    speed_visibility=review).run()
            self.assertEqual(backend.call_count, 6)
            self.assertEqual([r['speed'] for r in result.records], expected)
            self.assertEqual([r['speed_raw'] for r in result.records], texts)
            self.assertEqual([r['speed_kmh'] for r in progress.observations], expected)
            reasons = [r.observations['speed_kmh'].reasons for r in result.observations]
            self.assertIn('speed_hud_absent', reasons[1])
            self.assertIn('speed_hud_unverified', reasons[2])
            self.assertIn('speed_hud_unverified', reasons[3])
            self.assertIn('speed_roi_unavailable', reasons[4])
            self.assertEqual(result.observations[4].observations['speed_kmh'].last_observed_time_s, 0.)
            with patch('acc_telemetry.application.session_artifacts.probe_timebase',
                       return_value={'status': 'not_evaluated'}):
                write_session_artifacts(result, root / 'session', source_path=source,
                    source_before=identity, profile='ps5_full_map_1080p')
            loaded = read_session_artifacts(root / 'session')
            self.assertEqual(loaded.observations, result.observations)
            self.assertEqual(loaded.samples, result.samples)
            saved = loaded.manifest['config']['speed_visibility']
            self.assertEqual(saved['source_sha256'], identity['sha256'])
            self.assertEqual([s['reviewer'] for s in saved['spans']],
                             [s.reviewer for s in review.spans])
            other = root / 'other.mov'
            other.write_bytes(b'a different source must not inherit this review')
            with patch('acc_telemetry.application.session_artifacts.probe_timebase',
                       return_value={'status': 'not_evaluated'}), self.assertRaisesRegex(ValueError, 'speed visibility'):
                write_session_artifacts(result, root / 'wrong-session', source_path=other,
                    source_before=source_identity(other), profile='ps5_full_map_1080p')
            manifest_path = root / 'session/manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['config']['speed_visibility']['source_sha256'] = 'f' * 64
            manifest['config_sha256'] = hashlib.sha256(_json(manifest['config']).encode()).hexdigest()
            manifest_path.write_text(_json(manifest))
            with self.assertRaisesRegex(ValueError, 'speed visibility'):
                read_session_artifacts(root / 'session')

    def test_wrong_source_and_invalid_intervals_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.mov'
            source.write_bytes(b'actual video bytes')
            video = FakeVideo()
            video.video_path = str(source)
            review = SpeedVisibilityReview('0' * 64, source.stat().st_size, ())
            with patch('pytesseract.image_to_string') as backend, self.assertRaisesRegex(ValueError, 'source video'):
                TelemetryPipeline(video=video, controls=FakeControls(), laps=make_detector(),
                    progress=FakeGenericProgress(), has_track_map=False, speed_visibility=review).run()
            backend.assert_not_called()
            self.assertTrue(video.closed)
        for spans in ((SpeedVisibilitySpan(0, 1, 'visible', ''),),
                      (SpeedVisibilitySpan(float('nan'), 1, 'visible', 'r'),),
                      (SpeedVisibilitySpan(True, 2, 'visible', 'r'),),
                      (SpeedVisibilitySpan(0, 1, 'guessed', 'r'),),
                      (SpeedVisibilitySpan(0, 2, 'visible', 'r'), SpeedVisibilitySpan(1, 3, 'absent', 'r'))):
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                SpeedVisibilityReview('0' * 64, 10, spans).validate(duration_s=3)

    def test_loader_requires_source_binding_and_preserves_explicit_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'review.json'
            data = dict(schema_version='speed-visibility-v1', source_sha256='a' * 64,
                source_size_bytes=10, spans=[dict(start_s=0., end_s=1., state='unknown', reviewer='r')])
            path.write_text(json.dumps(data))
            review = load_speed_visibility(path)
            self.assertEqual(review.state_at(.5), 'unknown')
            self.assertEqual(review.state_at(1.), 'unknown')
            path.write_text('[]')
            with self.assertRaises(ValueError):
                load_speed_visibility(path)
        from acc_telemetry.adapters.cli import _parser
        self.assertEqual(_parser().parse_args(['v.mov', '--speed-visibility-json', 'review.json']).speed_visibility_json,
                         Path('review.json'))
