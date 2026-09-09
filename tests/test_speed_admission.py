"""Rate admission rejects values; it never reconstructs a measured speed."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import numpy as np
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.config import ConfigurationError
from acc_telemetry.application.speed_admission import SpeedAdmission
from acc_telemetry.application.speed_visibility import SpeedVisibilityReview, SpeedVisibilitySpan
from acc_telemetry.domain.telemetry import QualityFlag as Q
from acc_telemetry.domain.observations import FieldObservation
from test_configuration import _write_configuration, _telemetry_with_progress
from test_application_pipeline import FakeVideo, FakeControls, FakeGenericProgress
from test_fresh_speed_observations import make_detector


class TestSpeedAdmission(unittest.TestCase):
    def field(self, value, quality=Q.OBSERVED):
        return FieldObservation(value, quality, str(value))

    def guard(self):
        return SpeedAdmission(max_acceleration_m_s2=100., max_gap_s=.25)

    def test_boundary_rates_and_valid_abrupt_changes_are_not_smoothed(self):
        for values in ((100, 106, 112), (112, 106, 100)):
            guard = self.guard()
            readings = [guard.observe(self.field(v), time_s=i / 60) for i, v in enumerate(values)]
            self.assertEqual([v.value for v in readings], list(values))
        guard = self.guard()
        guard.observe(self.field(100), time_s=.2)
        self.assertEqual(guard.observe(self.field(136), time_s=.3).value, 136)
        self.assertIsNone(guard.observe(self.field(143), time_s=.3 + 1 / 60).value)

    def test_missing_rejected_context_and_long_gap_restart_fresh(self):
        guard = self.guard()
        guard.observe(self.field(162), time_s=0., context='one')
        rejected = guard.observe(self.field(4), time_s=1 / 60, context='one')
        self.assertEqual(rejected.raw_value, '4')
        self.assertIsNone(rejected.value)
        self.assertEqual(guard.observe(self.field(163), time_s=2 / 60, context='one').value, 163)
        self.assertEqual(guard.observe(self.field(0), time_s=3 / 60, context='new').value, 0)
        self.assertEqual(guard.observe(self.field(300), time_s=1., context='new').value, 300)
        for quality in (Q.MISSING, Q.ANOMALOUS, Q.HELD):
            guard.observe(self.field(None, quality), time_s=1.01, context='new')
            self.assertEqual(guard.observe(self.field(100), time_s=1.02, context='new').value, 100)

    def test_invalid_time_and_nonfinite_values_abstain(self):
        for time in (0., -1., float('nan'), float('inf')):
            guard = self.guard()
            guard.observe(self.field(100), time_s=0.)
            self.assertIsNone(guard.observe(self.field(100), time_s=time).value)
        for value in (float('nan'), float('inf'), -1, True):
            self.assertIsNone(self.guard().observe(self.field(value), time_s=0.).value)

    def test_admission_configuration_rejects_invalid_limits(self):
        for key in ('max_speed_acceleration_m_s2', 'max_speed_admission_gap_s'):
            for value in (0, -1, True, float('inf'), '100'):
                with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as directory:
                    config = _telemetry_with_progress()
                    config['ocr'][key] = value
                    _write_configuration(Path(directory), config)
                    with self.assertRaises(ConfigurationError):
                        load_settings(directory)

    def test_real_pipeline_rejects_digit_dropouts_then_recovers_fresh(self):
        for texts, expected in ((['162', '4', '163'], [162, None, 163]),
                                (['177', '7', '175'], [177, None, 175])):
            with self.subTest(texts=texts), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'source.mov'
                source.write_bytes(b'controlled OCR on synthetic reviewed frames')
                class Video(FakeVideo):
                    def get_video_info(self):
                        return dict(frame_count=3, fps=60., duration=3 / 60)
                    def process_frames(self):
                        self.current_frame = np.full((10, 10, 3), 40, np.uint8)
                        for i in range(3): yield i, i / 60, {}
                class Progress(FakeGenericProgress):
                    def finalize(self):
                        result = super().finalize()
                        return replace(result, frames=tuple(replace(result.frames[0], frame=i) for i in range(3)))
                video = Video()
                video.video_path = source
                review = SpeedVisibilityReview(hashlib.sha256(source.read_bytes()).hexdigest(),
                    source.stat().st_size, (SpeedVisibilitySpan(0., 3 / 60, 'visible', 'synthetic'),))
                progress = Progress()
                with patch('pytesseract.image_to_string', side_effect=texts) as backend:
                    result = TelemetryPipeline(video=video, controls=FakeControls(), laps=make_detector(),
                        progress=progress, has_track_map=False, settings=load_settings(), speed_visibility=review).run()
                self.assertEqual(backend.call_count, 3)
                self.assertEqual([r['speed'] for r in result.records], expected)
                self.assertEqual([r['speed_kmh'] for r in progress.observations], expected)
                self.assertEqual([r['speed_raw'] for r in result.records], texts)
                field = result.observations[1].observations['speed_kmh']
                self.assertEqual(field.quality, Q.ANOMALOUS)
                self.assertIn('speed_rate_exceeded', field.reasons)
                self.assertEqual(field.last_observed_time_s, 0.)
                self.assertEqual(result.samples[1].speed_kmh, None)
