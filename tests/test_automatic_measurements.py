"""Automatic extraction is independent of validation annotations, not verified truth."""
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest
import inspect
import numpy as np

from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.session_artifacts import read_session_artifacts, write_session_artifacts, source_identity
from acc_telemetry.domain.observations import VisibilitySpan
from acc_telemetry.extraction.controls import TelemetryExtractor
from test_application_pipeline import FakeVideo, FakeGenericProgress
from test_fresh_speed_observations import make_detector
from test_fresh_signal_roundtrip import pedal_roi


class TestAutomaticMeasurements(unittest.TestCase):
    def test_unknown_speed_can_be_extracted_but_never_claims_reviewed_visibility(self):
        detector = make_detector()
        for state, black, text, expected in [('unknown', False, '100', 100),
                ('unknown', False, '0', 0), ('absent', False, '100', None),
                ('unknown', True, '100', None), ('unknown', False, '682', None),
                ('unknown', False, '', None)]:
            with self.subTest(state=state, black=black, text=text), patch('pytesseract.image_to_string', return_value=text):
                observation = detector.observe_speed(np.full((10, 10, 3), 0 if black else 40, np.uint8),
                    hud_state=state, allow_unreviewed=True)
                self.assertEqual(observation.value, expected)
                self.assertEqual(observation.raw_value, text)
                if state == 'unknown':
                    self.assertIn('speed_hud_unverified', observation.reasons)

    def test_pipeline_automatic_signal_nulls_and_mode_survive_artifacts(self):
        class Video(FakeVideo):
            def get_video_info(self):
                return dict(fps=60., frame_count=4, duration=4/60)
            def process_frames(self):
                self.current_frame = np.full((10, 10, 3), 40, np.uint8)
                for i, pedal in enumerate((0, 100, None, 0)):
                    yield i, i/60, dict(throttle=pedal_roi(pedal, (0,255,0)), brake=pedal_roi(pedal, (0,0,255)))
        class Progress(FakeGenericProgress):
            def finalize(self):
                result = super().finalize()
                return replace(result, frames=tuple(replace(result.frames[0], frame=i) for i in range(4)))
        progress = Progress()
        with patch('pytesseract.image_to_string', side_effect=['100', '103', '682', '106']):
            result = TelemetryPipeline(video=Video(), controls=TelemetryExtractor(), laps=make_detector(),
                progress=progress, settings=load_settings(), has_track_map=False, measurement_mode='automatic').run()
        self.assertEqual([r['speed'] for r in result.records], [100,103,None,106])
        self.assertEqual([r['throttle'] for r in result.records], [0,100,None,0])
        self.assertEqual([r['brake'] for r in result.records], [0,100,None,0])
        self.assertEqual([r['speed_kmh'] for r in progress.observations], [100,103,None,106])
        self.assertEqual(result.resolved_config['measurement_mode'], 'automatic')
        self.assertIsNone(result.resolved_config['speed_visibility'])
        self.assertEqual(result.resolved_config['visibility'], ())
        for r in result.records:
            self.assertIn('automatic_measurements_unverified', r['s_reasons'])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'source.mov';source.write_bytes(b'synthetic')
            with patch('acc_telemetry.application.session_artifacts.probe_timebase', return_value={'status':'not_evaluated'}):
                write_session_artifacts(result, Path(directory)/'session', source_path=source,
                    source_before=source_identity(source), profile='ps5_full_map_1080p')
            loaded = read_session_artifacts(Path(directory)/'session')
            self.assertEqual(loaded.manifest['config']['measurement_mode'], 'automatic')
            self.assertFalse(loaded.manifest['coaching_eligible'])
            self.assertEqual(loaded.samples, result.samples)
            self.assertEqual(loaded.observations, result.observations)
            self.assertIn('hud_visibility_unverified', loaded.samples[1].field_reasons['throttle_pct'])
            self.assertEqual(loaded.observations[1].observations['speed_kmh'].last_observed_time_s, 1/60)

    def test_automatic_mode_rejects_annotation_inputs_and_invalid_modes(self):
        arguments = dict(video=FakeVideo(), controls=TelemetryExtractor(), laps=make_detector(),
            progress=FakeGenericProgress(), has_track_map=False)
        with self.assertRaisesRegex(ValueError, 'annotations'):
            TelemetryPipeline(**arguments, measurement_mode='automatic',
                visibility=(VisibilitySpan('brake',0,1,'test'),))
        with self.assertRaisesRegex(ValueError, 'measurement mode'):
            TelemetryPipeline(**arguments, measurement_mode='guessed')

    def test_adapters_expose_explicit_automatic_mode_and_keep_reviewed_default(self):
        from acc_telemetry.adapters.cli import _parser
        from acc_telemetry.adapters.web.services.processing import VideoProcessingService
        self.assertEqual(_parser().parse_args(['v.mov']).measurement_mode, 'reviewed')
        self.assertEqual(_parser().parse_args(['v.mov','--measurement-mode','automatic']).measurement_mode, 'automatic')
        self.assertEqual(inspect.signature(VideoProcessingService.process_video).parameters['measurement_mode'].default, 'reviewed')

    def test_web_service_forwards_automatic_mode_to_shared_pipeline(self):
        import asyncio
        from acc_telemetry.adapters.web.services.processing import VideoProcessingService
        module = 'acc_telemetry.adapters.web.services.processing.'
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'source.mov';source.write_bytes(b'synthetic')
            with patch(module+'TelemetryPipeline') as pipeline, patch(module+'LapDetector'):
                pipeline.return_value.run.side_effect = RuntimeError('stop after wiring')
                with self.assertRaisesRegex(RuntimeError, 'stop after wiring'):
                    asyncio.run(VideoProcessingService().process_video(str(source), 'trial', measurement_mode='automatic'))
                self.assertEqual(pipeline.call_args.kwargs['measurement_mode'], 'automatic')
                self.assertEqual(pipeline.call_args.kwargs['visibility'], ())
                self.assertIsNone(pipeline.call_args.kwargs['speed_visibility'])
