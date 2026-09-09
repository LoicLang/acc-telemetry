"""Modern lap OCR bounds foreground without truncating decimal components."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from PIL import Image
from acc_telemetry.extraction import laps
from acc_telemetry.application.config import load_settings, ConfigurationError
from test_configuration import _write_configuration, _telemetry_with_progress


class TestLapPreprocessing(unittest.TestCase):
    def test_foreground_margin_is_validated_configuration(self):
        settings = load_settings()
        self.assertTrue(settings.profile('ps5_full_map_720p').lap_foreground_bounds)
        self.assertFalse(settings.profile('ps5_full_map_1080p').lap_foreground_bounds)
        for value in (-1, True, 1.5, float('nan'), '1'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                config = _telemetry_with_progress()
                config['ocr']['lap_foreground_margin_px'] = value
                _write_configuration(Path(directory), config)
                with self.assertRaises(ConfigurationError):
                    load_settings(directory)

    def detector(self):
        detector = laps.LapDetector.__new__(laps.LapDetector)
        detector.lap_number_roi = dict(x=0, y=0, width=40, height=30)
        detector._enable_performance_stats = False
        detector._tesserocr_api = None
        detector.tesseract_config_lap = '--psm 8'
        detector._last_valid_lap_number = None
        detector._lap_number_history = []
        detector._history_size = 15
        detector._lap_foreground_bounds = True
        return detector

    def frame(self):
        frame = np.zeros((30, 40, 3), np.uint8)
        frame[8:20, 9:12] = 255
        frame[8:20, 16:19] = 255
        frame[8:20, 23:27] = 255
        return frame

    def test_modern_bounds_all_components_and_legacy_keeps_original_roi(self):
        detector = self.detector()
        with patch('pytesseract.image_to_string', return_value='120') as backend:
            observation = detector.observe_lap_number(self.frame())
        self.assertEqual(observation.value, 120)
        backend.assert_called_once()
        self.assertEqual(backend.call_args.args[0].shape, (42, 60))
        with patch('pytesseract.image_to_string', return_value='120') as backend:
            detector.extract_lap_number(self.frame())
        self.assertEqual(backend.call_args.args[0].shape, (90, 120))

    def test_blank_modern_threshold_abstains_without_ocr(self):
        with patch('pytesseract.image_to_string', return_value='7') as backend:
            observation = self.detector().observe_lap_number(np.zeros((30, 40, 3), np.uint8))
        backend.assert_not_called()
        self.assertIsNone(observation.value)

    def test_unconfigured_profile_keeps_full_modern_roi(self):
        detector = self.detector()
        detector._lap_foreground_bounds = False
        with patch('pytesseract.image_to_string', return_value='120') as backend:
            self.assertEqual(detector.observe_lap_number(self.frame()).value, 120)
        self.assertEqual(backend.call_args.args[0].shape, (90, 120))

    def test_modern_shared_mode_restores_after_backend_exception(self):
        modes = []
        class Backend:
            def SetPageSegMode(self, mode): modes.append(mode)
            def SetImage(self, image): pass
            def GetUTF8Text(self): raise RuntimeError('OCR unavailable')
        detector = self.detector()
        detector._tesserocr_api = Backend()
        with (patch.object(laps, 'tesserocr', SimpleNamespace(PSM=SimpleNamespace(SINGLE_WORD=8)), create=True),
              patch.object(laps, 'Image', Image, create=True)):
            self.assertIsNone(detector.observe_lap_number(self.frame()).value)
        self.assertEqual(modes, [8, 8])
