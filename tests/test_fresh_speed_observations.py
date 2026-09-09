"""Fresh-speed regressions exercise real extraction with only OCR text controlled."""
import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from acc_telemetry.extraction.laps import LapDetector
from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.application.pipeline import TelemetryPipeline
from test_application_pipeline import FakeVideo, FakeControls, FakePosition, FakeGenericProgress


def make_detector():
    detector = LapDetector.__new__(LapDetector)
    detector.speed_roi = dict(x=0, y=0, width=10, height=10)
    detector._speed_history = []
    detector._history_size = 15
    detector._last_valid_speed = None
    detector._tesserocr_api = None
    detector.tesseract_config_speed = '--psm 7'
    # Other fields abstain through their real methods, without extra OCR.
    detector.lap_number_roi = detector.gear_roi = {}
    return detector


class TestFreshSpeedObservations(unittest.TestCase):
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    def test_descending_and_ascending_are_current_readings_after_full_history(self):
        for readings in ([255] * 15 + [246, 237, 228], [179] * 15 + [188, 197, 206]):
            with self.subTest(readings=readings):
                detector = make_detector()
                with patch('pytesseract.image_to_string', side_effect=list(map(str, readings))) as backend:
                    observations = [detector.observe_speed(self.frame) for _ in readings]
                self.assertEqual(backend.call_count, len(readings))
                self.assertEqual([o.value for o in observations], readings)
                self.assertTrue(all(o.quality == QualityFlag.OBSERVED for o in observations))
                self.assertTrue(all(o.reasons == () for o in observations))

    def test_invalid_text_is_absent_preserves_raw_and_recovers_without_history(self):
        texts = ['100', '', '12x3', 'NaN', 'inf', '-1', '401', ' 246\n', '0']
        detector = make_detector()
        with patch('pytesseract.image_to_string', side_effect=texts) as backend:
            observations = [detector.observe_speed(self.frame) for _ in texts]
        self.assertEqual(backend.call_count, len(texts))
        self.assertEqual([o.raw_value for o in observations], texts)
        self.assertEqual([o.value for o in observations], [100] + [None] * 6 + [246, 0])
        for observation in observations[1:7]:
            self.assertNotIn(observation.quality, (QualityFlag.OBSERVED, QualityFlag.HELD))
            self.assertTrue(observation.reasons)
        self.assertIn('speed_out_of_range', observations[6].reasons)

    def test_bad_frame_roi_and_ocr_exception_never_hold_previous_value(self):
        detector = make_detector()
        with patch('pytesseract.image_to_string', return_value='100'):
            detector.observe_speed(self.frame)
        with patch('pytesseract.image_to_string') as backend:
            observations = [detector.observe_speed(frame) for frame in (None, np.zeros((0, 0, 3)), np.zeros((2, 2, 3)))]
        backend.assert_not_called()
        with patch('pytesseract.image_to_string', side_effect=RuntimeError('backend failed')) as backend:
            observations.append(detector.observe_speed(self.frame))
        backend.assert_called_once()
        for observation in observations:
            self.assertIsNone(observation.value)
            self.assertIsNone(observation.raw_value)
            self.assertEqual(observation.quality, QualityFlag.MISSING)
            self.assertTrue(observation.reasons)

    def test_modern_observation_does_not_read_or_mutate_legacy_history(self):
        detector = make_detector()
        detector._speed_history = [188] * 15
        detector._last_valid_speed = 188
        with patch('pytesseract.image_to_string', return_value='179'):
            observation = detector.observe_speed(self.frame)
        self.assertEqual(observation.value, 179)
        self.assertEqual(detector._speed_history, [188] * 15)
        self.assertEqual(detector._last_valid_speed, 188)

    def test_real_pipeline_keeps_fresh_speed_and_absence_at_original_frame_time(self):
        texts = ['255'] * 15 + ['246', '', '179']

        class Video(FakeVideo):
            def get_video_info(self):
                return dict(fps=30.0, frame_count=len(texts), duration=len(texts) / 30)

            def process_frames(self):
                for i in range(len(texts)):
                    self.current_frame = np.zeros((10, 10, 3), dtype=np.uint8)
                    yield i, i / 30, {}

        class Progress(FakeGenericProgress):
            def finalize(self):
                result = super().finalize()
                return replace(result, frames=tuple(replace(result.frames[0], frame=i) for i in range(len(texts))))

        progress = Progress()
        with patch('pytesseract.image_to_string', side_effect=texts) as backend:
            result = TelemetryPipeline(video=Video(), controls=FakeControls(), laps=make_detector(),
                position=FakePosition(), progress=progress, has_track_map=False).run()
        self.assertEqual(backend.call_count, len(texts))
        expected = [255] * 15 + [246, None, 179]
        self.assertEqual([r['speed'] for r in result.records], expected)
        self.assertEqual([r['speed_raw'] for r in result.records], texts)
        self.assertEqual([r['frame'] for r in result.records], list(range(len(texts))))
        self.assertEqual([r['time'] for r in result.records], [i / 30 for i in range(len(texts))])
        self.assertEqual([r['speed_kmh'] for r in progress.observations], expected)
        for i, observation in enumerate(result.observations):
            speed = observation.observations['speed_kmh']
            self.assertEqual(speed.value, expected[i])
            self.assertEqual(speed.raw_value, texts[i])
            self.assertEqual(speed.last_observed_time_s, (i if i != 16 else 15) / 30)
