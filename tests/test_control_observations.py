"""Reviewed visibility, missing HUD and strict control pipeline regressions."""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from acc_telemetry.domain import observations as evidence
from acc_telemetry.domain.telemetry import QualityFlag as Q
from acc_telemetry.extraction.controls import TelemetryExtractor
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.config import load_settings
from acc_telemetry.normalization.samples import normalize_row
from test_application_pipeline import FakeVideo, FakeLaps, FakeGenericProgress


class TestControlObservations(unittest.TestCase):
    def spans(self):
        return tuple(evidence.VisibilitySpan(f, 0, 1, 'reviewer')
                     for f in ('throttle', 'brake', 'steering'))

    def test_empty_black_or_absent_roi_never_becomes_observed_zero(self):
        for roi in (None, np.zeros((0, 0, 3), np.uint8), np.zeros((20, 100, 3), np.uint8)):
            values = TelemetryExtractor().observe_frame_telemetry(
                dict(throttle=roi, brake=roi, steering=roi), time_s=0, visibility=self.spans())
            for observation in values.values():
                self.assertIsNone(observation.value)
                self.assertEqual(observation.quality, Q.MISSING)

    def test_reviewed_released_pedals_are_zero_but_missing_steering_dot_is_not(self):
        roi = np.full((20, 100, 3), 40, np.uint8)
        values = TelemetryExtractor().observe_frame_telemetry(
            dict(throttle=roi, brake=roi, steering=roi), time_s=0, visibility=self.spans())
        for field in ('throttle', 'brake'):
            self.assertEqual(values[field].value, 0)
            self.assertEqual(values[field].quality, Q.OBSERVED)
        self.assertIsNone(values['steering'].value)
        self.assertEqual(values['steering'].reasons, ('steering_candidate_missing',))
        for field in ('tc_active', 'abs_active'):
            self.assertEqual(values[field].reasons, ('indicator_semantics_unverified',))

    def test_unreviewed_and_overlay_intervals_abstain_with_half_open_bounds(self):
        roi = np.full((20, 100, 3), (0, 255, 0), np.uint8)
        spans = (evidence.VisibilitySpan('throttle', 0, 1, 'reviewer'),
                 evidence.VisibilitySpan('throttle', 2, 3, 'reviewer'))
        for time, expected in ((0, 100), (1, None), (1.5, None), (2, 100), (3, None)):
            result = TelemetryExtractor().observe_frame_telemetry(
                {'throttle': roi}, time_s=time, visibility=spans)['throttle']
            self.assertEqual(result.value, expected)
        result = TelemetryExtractor().observe_frame_telemetry(
            {'throttle': roi}, time_s=0, visibility=())['throttle']
        self.assertEqual(result.reasons, ('hud_visibility_unverified',))

    def test_span_validation_rejects_invalid_and_ambiguous_annotations(self):
        Span = evidence.VisibilitySpan
        bad = [(Span('throttle', 1, 0, 'r'),), (Span('throttle', 0, 4, 'r'),),
               (Span('throttle', float('nan'), 1, 'r'),), (Span('throttle', 0, 1, ''),),
               (Span('invalid', 0, 1, 'r'),),
               (Span('throttle', 1, 2, 'r'), Span('brake', 0, 1, 'r')),
               (Span('throttle', 0, 2, 'r'), Span('throttle', 1, 3, 'other'))]
        for spans in bad:
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                evidence.validate_visibility(spans, duration_s=3)
        evidence.validate_visibility(self.spans(), duration_s=1)

    def test_pipeline_without_visibility_preserves_all_missing_through_csv(self):
        class Video(FakeVideo):
            def process_frames(self):
                yield 0, 0., {f: np.zeros((20, 100, 3), np.uint8)
                              for f in ('throttle', 'brake', 'steering')}
        result = TelemetryPipeline(video=Video(), controls=TelemetryExtractor(),
            laps=FakeLaps(), progress=FakeGenericProgress(), has_track_map=False).run()
        rows = list(csv.DictReader(io.StringIO(pd.DataFrame(result.records).to_csv(index=False))))
        sample = normalize_row(rows[0], load_settings().normalization)
        for field in ('throttle_pct', 'brake_pct', 'steering', 'tc_active', 'abs_active'):
            self.assertEqual(sample.field_quality[field], Q.MISSING)
            self.assertIsNone(getattr(sample, field))
            self.assertTrue(sample.field_reasons[field])

    def test_summary_and_report_support_missing_controls(self):
        from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer
        row = dict(time=0., frame=0, lap_number=1, speed=100, gear=3,
                   throttle=None, brake=None, steering=None, tc_active=None, abs_active=None)
        with tempfile.TemporaryDirectory() as directory:
            visualizer = InteractiveTelemetryVisualizer(output_dir=directory)
            df = pd.DataFrame([row, dict(row, time=1., frame=1)])
            summary = visualizer.generate_summary(df)
            self.assertIsNone(summary['avg_throttle'])
            self.assertIsNone(summary['tc_active_percentage'])
            self.assertIsNone(summary['laps'][0]['avg_brake'])
            json.dumps(summary, allow_nan=False)
            self.assertTrue(Path(visualizer.plot_telemetry(df)).is_file())

    def test_visibility_json_loader_and_cli_argument(self):
        from acc_telemetry.application.visibility import load_visibility
        from acc_telemetry.adapters.cli import _parser
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'visibility.json'
            path.write_text('[{"field":"throttle","start_s":0,"end_s":1,"reviewer":"r"}]')
            spans = load_visibility(path)
            self.assertEqual(spans[0].reviewer, 'r')
            args = _parser().parse_args(['video.mov', '--visibility-json', str(path)])
            self.assertEqual(args.visibility_json, path)

class TestControlAdapterWiring(unittest.TestCase):
    def test_pipeline_rejects_review_past_video_end_and_closes_video(self):
        video = FakeVideo()
        with self.assertRaises(ValueError):
            TelemetryPipeline(video=video, controls=TelemetryExtractor(), laps=FakeLaps(),
                progress=FakeGenericProgress(), has_track_map=False,
                visibility=(evidence.VisibilitySpan('throttle', 0, 2, 'r'),)).run()
        self.assertTrue(video.closed)

    def test_centered_dot_is_observed_and_legacy_missing_still_returns_zero(self):
        roi = np.full((20, 100, 3), 40, np.uint8)
        extractor = TelemetryExtractor()
        self.assertEqual(extractor.extract_steering_position(roi), 0)
        roi[12:17, 48:53] = 255
        result = extractor.observe_frame_telemetry({'steering': roi}, time_s=0,
            visibility=(evidence.VisibilitySpan('steering', 0, 1, 'r'),))['steering']
        self.assertEqual(result.value, 0)
        self.assertEqual(result.quality, Q.OBSERVED)

    def test_cli_wires_reviewed_spans_to_actual_pipeline_and_export(self):
        from unittest.mock import patch
        from acc_telemetry.adapters.cli import main
        class Video(FakeVideo):
            def process_frames(self):
                yield 0, 0., {f: np.full((20, 100, 3), 40, np.uint8)
                              for f in ('throttle', 'brake', 'steering')}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video_path = root / 'source.mov'
            video_path.write_bytes(b'fixture; decoding replaced')
            visibility = root / 'visibility.json'
            visibility.write_text('[{"field":"throttle","start_s":0,"end_s":0.01,"reviewer":"r"}]')
            with (patch('acc_telemetry.application.components.VideoProcessor', return_value=Video()),
                  patch('acc_telemetry.application.components.LapDetector', return_value=FakeLaps()),
                  patch('acc_telemetry.application.components.ProgressSessionEstimator',
                        return_value=FakeGenericProgress()),
                  patch('acc_telemetry.application.pipeline.TelemetryPipeline._extract_track_path')):
                self.assertEqual(main([str(video_path), '--output', str(root / 'reports'),
                                       '--visibility-json', str(visibility)]), 0)
            with next((root / 'reports').glob('*.csv')).open() as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(float(row['throttle']), 0)
            self.assertEqual(row['brake'], '')
            self.assertIn('throttle_pct:observed', row['quality_hint'])
            self.assertIn('brake_pct:missing', row['quality_hint'])


class TestWebMissingControls(unittest.IsolatedAsyncioTestCase):
    async def test_web_processing_saves_nullable_metadata_without_visibility(self):
        from unittest.mock import patch
        from acc_telemetry.adapters.web.services.processing import VideoProcessingService
        class Video(FakeVideo):
            def process_frames(self):
                yield 0, 0., {}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video_path = root / 'source.mov'
            video_path.write_bytes(b'fixture')
            service = VideoProcessingService()
            with (patch.object(service, 'load_roi_config', return_value={'ps5_full_map_720p': {}}),
                  patch.object(service, '_build_progress_estimator', return_value=FakeGenericProgress()),
                  patch('acc_telemetry.adapters.web.services.processing.VideoProcessor', return_value=Video()),
                  patch('acc_telemetry.adapters.web.services.processing.LapDetector', return_value=FakeLaps()),
                  patch.object(service.storage, 'get_video_directory', return_value=root),
                  patch.object(service.storage, 'save_metadata') as save):
                metadata = await service.process_video(str(video_path), 'session',
                    profile_name='ps5_full_map_720p')
            save.assert_called_once()
            self.assertIsNone(metadata.laps[0].avg_throttle)
            json.dumps(metadata.model_dump(), allow_nan=False)
            with (root / 'telemetry.csv').open() as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row['throttle'], '')
            self.assertIn('throttle_pct:missing', row['quality_hint'])
