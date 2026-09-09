"""Fresh OCR evidence through the real detector, pipeline and confirmer."""
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
from PIL import Image

import numpy as np

from acc_telemetry.extraction import laps as lap_module
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.lap_state import LapTransitionConfirmer
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.progress import ProgressSessionEstimator
from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.domain.observations import FieldObservation
from test_application_pipeline import FakeControls, FakeVideo


class TextBackend:
    def __init__(self, texts):
        self.GetUTF8Text = Mock(side_effect=texts)
    def SetImage(self, image):
        pass
    def SetPageSegMode(self, mode):
        pass
    def End(self):
        pass


def detector_with_texts(texts):
    detector = lap_module.LapDetector.__new__(lap_module.LapDetector)
    detector._last_valid_lap_number = 1
    detector._lap_number_history = [1] * 15
    detector._history_size = 15
    detector._enable_performance_stats = False
    detector._tesserocr_api = TextBackend(texts)
    detector._tesserocr_api_speed = None
    detector._tesserocr_api_gear = None
    detector._tesserocr_api_time = None
    detector.lap_number_roi = dict(x=0, y=0, width=10, height=10)
    return detector


class TestLapObservations(unittest.TestCase):
    def setUp(self):
        for name, value in (('tesserocr', SimpleNamespace(PSM=SimpleNamespace(SINGLE_WORD=8))),
                            ('Image', Image)):
            patcher = patch.object(lap_module, name, value, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_strict_parser(self):
        for text, expected in [(' 12\n', 12), ('0', 0), ('999', 999),
                               ('1000', None), ('12x3', None), ('', None),
                               ('-1', None), ('²', None)]:
            with self.subTest(text=text):
                self.assertEqual(lap_module.parse_lap_text(text), expected)

    def test_blank_ocr_is_missing_even_after_a_valid_lap(self):
        detector = detector_with_texts([])
        detector._read_lap_text = Mock(side_effect=['1', '', '1', '12x3'])
        frame = np.zeros((10, 10, 3), np.uint8)
        observations = [detector.observe_lap_number(frame) for _ in range(4)]
        self.assertEqual([o.value for o in observations], [1, None, 1, None])
        self.assertEqual(observations[1].quality, QualityFlag.MISSING)
        self.assertEqual(observations[0].quality, QualityFlag.OBSERVED)
        self.assertEqual(observations[3].raw_value, '12x3')
        self.assertEqual(detector._read_lap_text.call_count, 4)
        self.assertEqual(detector._lap_number_history, [1] * 15)
        self.assertEqual(detector._last_valid_lap_number, 1)

    def test_pipeline_passes_raw_not_held_lap_to_confirmer(self):
        cases = [
            (['1'] * 5 + ['2'] + [''] * 4, 0),
            (['1'] * 5 + ['2'] * 5 + [''] * 4, 1),
            (['1'] * 5 + ['3'] * 5 + ['0'] * 5, 0),
            (['1'] * 5 + ['2', '1', '2', '', '2', '2', '2', '2'], 0),
            (['1'] * 5 + ['2', '', '2', '2', '2', '2', '2'], 1),
        ]
        for texts, count in cases:
            with self.subTest(texts=texts):
                detector = detector_with_texts(texts)
                detector.observe_speed = Mock(return_value=FieldObservation(100, QualityFlag.OBSERVED, "100"))
                detector.observe_gear = Mock(return_value=FieldObservation(3, QualityFlag.OBSERVED, "3"))
                detector.extract_speed = Mock(return_value=100)
                detector.get_last_speed_quality = Mock(return_value=QualityFlag.OBSERVED)
                detector.extract_gear = Mock(return_value=3)
                detector.finalize_lap_detection = Mock(return_value=None)
                class Video(FakeVideo):
                    def process_frames(self):
                        self.current_frame = np.full((10, 10, 3), 255, np.uint8)
                        for i in range(len(texts)):
                            yield i, i / 60, {}
                confirmer = LapTransitionConfirmer(consecutive_observations=5)
                confirmer.observe = Mock(wraps=confirmer.observe)
                estimator = ProgressSessionEstimator(
                    settings=load_settings().progress, lap_confirmer=confirmer,
                    white_lower=(0, 0, 200), white_upper=(180, 50, 255))
                result = TelemetryPipeline(video=Video(), controls=FakeControls(),
                    laps=detector, progress=estimator, has_track_map=False).run()
                raw = [call.args[0].raw_lap_number for call in confirmer.observe.call_args_list]
                self.assertEqual(raw, [int(t) if t else None for t in texts])
                self.assertEqual(len(result.lap_transitions), count)
                self.assertEqual(detector._tesserocr_api.GetUTF8Text.call_count, len(texts))
                detector.finalize_lap_detection.assert_not_called()
                if count:
                    boundary = result.lap_transitions[0]
                    self.assertEqual(boundary['confirmed_at_s'], boundary['time'])
                    self.assertEqual(boundary['last_previous_lap_observed_time_s'], 4 / 60)

    def test_legacy_wrapper_still_holds_blank_and_filters_noise(self):
        detector = detector_with_texts(['', '1x'])
        frame = np.zeros((10, 10, 3), np.uint8)
        self.assertEqual(detector.extract_lap_number(frame), 1)
        self.assertEqual(detector.extract_lap_number(frame), 1)
