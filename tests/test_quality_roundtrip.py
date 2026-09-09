"""Regression evidence across actual pipeline, DataFrame, CSV and normalization."""
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

import pandas as pd

from acc_telemetry.application.config import load_settings
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.speed_visibility import SpeedVisibilityReview, SpeedVisibilitySpan
from acc_telemetry.application.progress import ProgressSessionEstimator
from acc_telemetry.application.lap_state import LapTransitionConfirmer
from acc_telemetry.domain.observations import FieldObservation
from acc_telemetry.domain.telemetry import QualityFlag as Q
from acc_telemetry.normalization.samples import normalize_row
from test_application_pipeline import FakeLaps, FakeVideo, FakeControls


class TestQualityRoundtrip(unittest.TestCase):
    def run_records(self, speed, gear=None, laps=(1,)):
        detector = FakeLaps()
        detector.observe_speed = Mock(return_value=speed)
        detector.extract_speed = Mock(return_value=speed.value)
        detector.get_last_speed_quality = Mock(return_value=speed.quality)
        detector.observe_gear = Mock(return_value=gear or FieldObservation(3, Q.OBSERVED, '3'))
        detector.observe_lap_number = Mock(side_effect=[
            FieldObservation(v, Q.OBSERVED if v is not None else Q.MISSING, v) for v in laps])
        class Video(FakeVideo):
            def get_video_info(self):
                return {"fps": 60.0, "frame_count": len(laps), "duration": len(laps) / 60}

            def process_frames(self):
                for i in range(len(laps)):
                    yield i, i / 60, {}
        estimator = ProgressSessionEstimator(settings=load_settings().progress,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=5),
            white_lower=(0, 0, 200), white_upper=(180, 50, 255))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.mov'
            source.write_bytes(b'synthetic source bound to the visibility review')
            video = Video()
            video.video_path = source
            review = SpeedVisibilityReview(
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                source_size_bytes=source.stat().st_size,
                spans=(SpeedVisibilitySpan(0.0, len(laps) / 60, 'visible', 'test'),),
            )
            return TelemetryPipeline(video=video, controls=FakeControls(), laps=detector,
                progress=estimator, has_track_map=False,
                speed_visibility=review).run().records

    def roundtrip(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'telemetry.csv'
            pd.DataFrame(records).to_csv(path, index=False)
            with path.open(newline='') as handle:
                rows = list(csv.DictReader(handle))
        return [normalize_row(row, load_settings().normalization) for row in rows]

    def test_held_speed_stays_held_after_pipeline_csv(self):
        rows = self.run_records(FieldObservation(100, Q.HELD, '682', ('speed_out_of_range',)))
        self.assertIn('speed_kmh:held', rows[0]['quality_hint'])
        sample = self.roundtrip(rows)[0]
        self.assertEqual(sample.field_quality['speed_kmh'], Q.HELD)
        self.assertEqual(sample.source_values['speed_raw'], '682')
        self.assertEqual(sample.field_reasons['speed_kmh'], ('speed_out_of_range',))

    def test_missing_speed_and_gear_stay_null_with_reasons(self):
        rows = self.run_records(FieldObservation(None, Q.MISSING, ''),
            FieldObservation(None, Q.MISSING, 'R', ('unsupported_gear_symbol',)))
        sample = self.roundtrip(rows)[0]
        self.assertIsNone(sample.speed_kmh)
        self.assertIsNone(sample.gear)
        self.assertEqual(sample.field_quality['gear'], Q.MISSING)
        self.assertEqual(sample.field_reasons['gear'], ('unsupported_gear_symbol',))
        self.assertEqual(sample.source_values['gear_raw'], 'R')
        self.assertIsNone(sample.s)
        self.assertIsNone(sample.s_odometry)
        self.assertIsNone(sample.s_visual)
        self.assertEqual(sample.s_uncertainty, rows[0]['s_uncertainty'])
        self.assertEqual(sample.s_source.value, rows[0]['s_source'])
        self.assertEqual(sample.s_reasons, tuple(rows[0]['s_reasons'].split(';')))

    def test_lap_quality_and_confirmer_reasons_survive_missing_and_rejected_reads(self):
        rows = self.run_records(FieldObservation(100, Q.OBSERVED, '100'),
            laps=(1, 1, 1, 1, 1, None, 3, 2, 1))
        samples = self.roundtrip(rows)
        self.assertEqual([s.field_quality['lap_number'] for s in samples],
            [Q.MISSING]*4 + [Q.OBSERVED, Q.HELD, Q.HELD, Q.HELD, Q.OBSERVED])
        self.assertEqual(samples[5].field_reasons['lap_number'], ('lap_observation_missing',))
        self.assertEqual(samples[6].field_reasons['lap_number'], ('lap_observation_rejected',))
        self.assertEqual(samples[7].field_reasons['lap_number'], ('lap_confirmation_pending',))
        self.assertEqual(rows[6]['raw_lap_number'], 3)

    def test_real_detector_sequence_survives_pipeline_and_csv(self):
        from test_speed_ocr_mode import TestFieldOCRObservations
        detector = TestFieldOCRObservations().make_detector()
        detector.observe_lap_number = Mock(return_value=FieldObservation(1, Q.OBSERVED, '1'))
        class Video(FakeVideo):
            def get_video_info(self):
                return {"fps": 60.0, "frame_count": 3, "duration": 3 / 60}

            def process_frames(self):
                self.current_frame = np.full((10, 10, 3), 40, np.uint8)
                for i in range(3):
                    yield i, i / 60, {}
        estimator = ProgressSessionEstimator(settings=load_settings().progress,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=5),
            white_lower=(0, 0, 200), white_upper=(180, 50, 255))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.mov'
            source.write_bytes(b'synthetic source bound to the visibility review')
            video = Video()
            video.video_path = source
            review = SpeedVisibilityReview(
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                source_size_bytes=source.stat().st_size,
                spans=(SpeedVisibilitySpan(0.0, 3 / 60, 'visible', 'test'),),
            )
            with patch('pytesseract.image_to_string',
                       side_effect=['100', '4', '', '', '682', 'R']) as backend:
                rows = TelemetryPipeline(video=video, controls=FakeControls(), laps=detector,
                    progress=estimator, has_track_map=False,
                    speed_visibility=review).run().records
        self.assertEqual(backend.call_count, 6)
        samples = self.roundtrip(rows)
        self.assertEqual([s.gear for s in samples], [4, None, None])
        self.assertEqual([s.speed_kmh for s in samples], [100, None, None])
        self.assertEqual([s.field_quality['speed_kmh'] for s in samples],
                         [Q.OBSERVED, Q.MISSING, Q.ANOMALOUS])
        self.assertEqual(samples[-1].source_values['speed_raw'], '682')
        self.assertEqual(samples[-1].field_reasons['speed_kmh'], ('speed_out_of_range',))

    def test_modern_nonfinite_numbers_refused_before_and_after_csv(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=value):
                rows = self.run_records(FieldObservation(value, Q.OBSERVED, 'bad'))
                sample = normalize_row(rows[0], load_settings().normalization)
                self.assertIsNone(sample.speed_kmh)
                self.assertEqual(sample.source_values['speed_raw'], 'bad')
                self.assertIn('speed_value_invalid', sample.field_reasons['speed_kmh'])
                rows[0]['speed'] = value
                with self.assertRaisesRegex(ValueError, 'non-finite'):
                    normalize_row(rows[0], load_settings().normalization)
                # CSV empty is null; literal nonfinite strings must be refused.
                rows[0]['speed'] = str(value)
                with self.assertRaisesRegex(ValueError, 'non-finite'):
                    self.roundtrip(rows)
