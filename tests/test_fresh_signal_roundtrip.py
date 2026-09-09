"""Fresh measurements through real extraction, artifacts, API and odometry.

Images and text backends are synthetic; these are software regressions, not
independent capture-accuracy or HUD-presence evidence.
"""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from acc_telemetry.adapters.web.api import telemetry
from acc_telemetry.adapters.web.models import TelemetryDataPoint
from acc_telemetry.adapters.web.services.storage import StorageService
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.lap_state import LapTransitionConfirmer
from acc_telemetry.application.odometry import integrate_speed
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.progress import ProgressSessionEstimator
from acc_telemetry.application.session_artifacts import (
    read_session_artifacts, source_identity, write_session_artifacts,
)
from acc_telemetry.domain.observations import FieldObservation, VisibilitySpan
from acc_telemetry.domain.progress import ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag as Q
from acc_telemetry.extraction.controls import TelemetryExtractor
from test_application_pipeline import FakeVideo
import test_speed_ocr_mode as ocr_fixtures


def pedal_roi(value, color):
    if value is None:
        return np.zeros((20, 100, 3), np.uint8)
    roi = np.full((20, 100, 3), 40, np.uint8)
    roi[:, :value] = color
    return roi


class TestFreshSignalRoundtrip(unittest.TestCase):
    def pipeline(self, texts, *, times=None, pedals=None, legacy=None):
        times = times or [i / 60 for i in range(len(texts))]
        pedals = pedals or [(0, 0)] * len(texts)
        detector = ocr_fixtures.TestFieldOCRObservations().make_detector()
        detector.observe_lap_number = Mock(return_value=FieldObservation(1, Q.OBSERVED, '1'))
        if legacy is not None:
            # Explicit old-artifact compatibility only; modern tests use real OCR.
            detector.observe_speed = Mock(side_effect=legacy)
        class Video(FakeVideo):
            def get_video_info(self):
                return dict(fps=60., frame_count=len(texts), duration=times[-1] + 1 / 60)

            def process_frames(self):
                self.current_frame = np.full((10, 10, 3), 255, np.uint8)
                for i, (time, (throttle, brake)) in enumerate(zip(times, pedals)):
                    yield i, time, dict(throttle=pedal_roi(throttle, (0, 255, 0)),
                                        brake=pedal_roi(brake, (0, 0, 255)))
        settings = load_settings()
        progress = ProgressSessionEstimator(settings=settings.progress,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=5),
            white_lower=(0, 0, 200), white_upper=(180, 50, 255))
        backend_texts = ['3' for _ in texts] if legacy is not None else [
            text for speed in texts for text in (speed, '3')]
        with (patch('pytesseract.image_to_string', side_effect=backend_texts) as backend,
              patch('acc_telemetry.application.progress.integrate_speed', wraps=integrate_speed) as integrate):
            result = TelemetryPipeline(video=Video(), controls=TelemetryExtractor(),
                laps=detector, progress=progress, has_track_map=False, settings=settings,
                visibility=tuple(VisibilitySpan(field, 0, times[-1] + 1 / 60, 'synthetic-test')
                                 for field in ('throttle', 'brake'))).run()
        self.assertEqual(backend.call_count, len(backend_texts))
        return result, integrate.call_args.args[0]

    def artifact_and_api(self, result):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mov'
            source.write_bytes(b'synthetic frame source; no capture accuracy claim')
            output = root / 'session'
            with patch('acc_telemetry.application.session_artifacts.probe_timebase',
                       return_value={'status': 'not_evaluated'}):
                write_session_artifacts(result, output, source_path=source,
                    source_before=source_identity(source), profile='ps5_full_map_1080p',
                    clip_origin={'source_id': 'synthetic-parent', 'start_s': 12.5})
            loaded = read_session_artifacts(output)
            self.assertEqual(loaded.observations, result.observations)
            self.assertEqual(loaded.samples, result.samples)
            envelopes = [json.loads(line) for line in (output / 'observations.jsonl').read_text().splitlines()]
            for envelope, sample in zip(envelopes, loaded.samples):
                self.assertEqual(envelope['source_time_s'], sample.time_s + 12.5)
            storage = StorageService()
            storage.output_dir = root
            with patch.object(telemetry, 'storage', storage):
                rows = asyncio.run(telemetry.get_telemetry_data('session'))
            rows = [TelemetryDataPoint(**row).model_dump(mode='json') for row in rows]
            # JSON consumers must accept the payload without NaN/inf.
            json.dumps(rows, allow_nan=False)
            return loaded, rows

    def test_fresh_speed_null_raw_quality_reasons_and_times_reach_artifact_and_api(self):
        texts = ['255'] * 15 + ['246', '', '682', '179']
        expected = [255] * 15 + [246, None, None, 179]
        result, odometry_input = self.pipeline(texts)
        self.assertEqual([row['speed'] for row in result.records], expected)
        loaded, rows = self.artifact_and_api(result)
        last_fresh = None
        for i, (sample, row, original, value, raw, odom) in enumerate(zip(
                loaded.samples, rows, result.records, expected, texts, odometry_input)):
            field = loaded.observations[i].observations['speed_kmh']
            quality = Q.OBSERVED if value is not None else (Q.ANOMALOUS if raw == '682' else Q.MISSING)
            if value is not None:
                last_fresh = i / 60
            self.assertEqual(field.last_observed_time_s, last_fresh)
            self.assertEqual((sample.frame, sample.time_s), (i, i / 60))
            self.assertEqual((row['frame'], row['time']), (i, i / 60))
            self.assertEqual((sample.speed_kmh, row['speed'], odom.speed_kmh), (value,) * 3)
            self.assertEqual(sample.source_values['speed_raw'], raw)
            self.assertEqual(row['speed_raw'], raw)
            self.assertEqual(sample.field_quality['speed_kmh'], quality)
            self.assertEqual(odom.quality, quality)
            self.assertEqual(row['quality_hint'], original['quality_hint'])
            self.assertEqual(tuple(json.loads(row['field_reasons'])['speed_kmh']), field.reasons)
            self.assertEqual(sample.field_reasons['speed_kmh'], field.reasons)
            if value is None:
                self.assertTrue(field.reasons)

    def test_real_pedal_decoder_preserves_attack_release_interruptions_blip_and_hud_gap(self):
        pedals = [(0, 0), (100, 100), (0, 100), (0, 80), (0, 50), (0, 20),
                  (0, 0), (100, 100), (0, 0), (100, 100), (None, None), (0, 0)]
        result, _ = self.pipeline(['100'] * len(pedals), pedals=pedals)
        loaded, rows = self.artifact_and_api(result)
        for i, (expected, sample, row) in enumerate(zip(pedals, loaded.samples, rows)):
            self.assertEqual((sample.throttle_pct, sample.brake_pct), expected)
            self.assertEqual((row['throttle'], row['brake']), expected)
            self.assertEqual((row['frame'], row['time']), (i, i / 60))
            for name, value in zip(('throttle_pct', 'brake_pct'), expected):
                observation = loaded.observations[i].observations[name]
                self.assertEqual(observation.value, value)
                self.assertEqual(observation.raw_value, value)
                self.assertEqual(sample.field_quality[name], Q.MISSING if value is None else Q.OBSERVED)
                self.assertEqual(sample.field_reasons[name], observation.reasons)
                self.assertEqual(tuple(json.loads(row['field_reasons'])[name]), observation.reasons)
                self.assertEqual(observation.last_observed_time_s, (i if value is not None else i - 1) / 60)
        self.assertEqual(loaded.samples[10].field_reasons['brake_pct'], ('control_roi_unavailable',))

    def test_legacy_held_keeps_original_quality_raw_and_last_fresh_timestamp(self):
        legacy = [FieldObservation(100, Q.OBSERVED, '100', (), 0.),
                  FieldObservation(100, Q.HELD, '682', ('speed_out_of_range',), 0.)]
        result, odometry_input = self.pipeline(['100', '682'], legacy=legacy)
        loaded, rows = self.artifact_and_api(result)
        observation = loaded.observations[1].observations['speed_kmh']
        self.assertEqual(observation, legacy[1])
        self.assertEqual(loaded.samples[1].field_quality['speed_kmh'], Q.HELD)
        self.assertIn('speed_kmh:held', rows[1]['quality_hint'])
        self.assertEqual(rows[1]['speed_raw'], '682')
        trace = integrate_speed(odometry_input, max_interpolation_gap_s=.25)
        self.assertEqual(trace[-1].distance_m, 0.)
        self.assertEqual(trace[-1].source, ProgressSource.MISSING)

    def test_rejected_outlier_and_gaps_only_interpolate_internal_odometry(self):
        for times, interpolated, distance in (([0., .1, .2], True, 2.),
                                               ([0., .2, .4], False, 0.)):
            for raw in ('', '682'):
                with self.subTest(times=times, raw=raw):
                    result, odometry_input = self.pipeline(['36', raw, '36'], times=times)
                    self.assertEqual([o.speed_kmh for o in odometry_input], [36, None, 36])
                    self.assertEqual([r['speed'] for r in result.records], [36, None, 36])
                    trace = integrate_speed(odometry_input, max_interpolation_gap_s=.25)
                    self.assertAlmostEqual(trace[-1].distance_m, distance)
                    self.assertEqual(trace[1].source,
                                     ProgressSource.INTERPOLATED if interpolated else ProgressSource.MISSING)
                    reason = 'speed_gap_interpolated' if interpolated else ('speed_anomalous' if raw == '682' else 'speed_missing')
                    self.assertIn(reason, trace[1].reasons)
                    self.assertEqual(result.samples[1].field_quality['speed_kmh'],
                                     Q.ANOMALOUS if raw == '682' else Q.MISSING)
                    self.assertEqual(result.samples[1].source_values['speed_raw'], raw)
                    self.assertIsNone(result.samples[1].speed_kmh)
