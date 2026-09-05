import unittest
import statistics
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src import lap_detector
from acc_telemetry.domain.telemetry import QualityFlag


class TestTessdataDiscovery(unittest.TestCase):
    def test_find_tessdata_path_prefers_repository_local_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tessdata = root / "data" / "shared" / "tessdata"
            tessdata.mkdir(parents=True)
            (tessdata / "eng.traineddata").write_bytes(b"fixture")

            result = lap_detector.find_tessdata_path(root)

        self.assertEqual(result, tessdata)


class FakeTesseractAPI:
    def __init__(self):
        self.page_seg_modes = []

    def SetPageSegMode(self, mode):
        self.page_seg_modes.append(mode)

    def SetImage(self, image):
        pass

    def GetUTF8Text(self):
        return "171"


class FailingTesseractAPI(FakeTesseractAPI):
    def GetUTF8Text(self):
        raise RuntimeError("OCR failed")


class SequenceTesseractAPI(FakeTesseractAPI):
    def __init__(self, texts):
        super().__init__()
        self.texts = iter(texts)

    def GetUTF8Text(self):
        return next(self.texts)


class CapturingTesseractAPI(FakeTesseractAPI):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.images = []

    def SetImage(self, image):
        self.images.append(image)

    def GetUTF8Text(self):
        return self.text


@unittest.skipUnless(lap_detector.USE_TESSEROCR, "tesserocr is not available")
class TestLapNumberOCRMode(unittest.TestCase):
    def test_extract_lap_number_enlarges_thresholded_digits(self):
        detector = lap_detector.LapDetector.__new__(lap_detector.LapDetector)
        detector.lap_number_roi = {"x": 0, "y": 0, "width": 58, "height": 60}
        detector._last_valid_lap_number = None
        detector._lap_number_history = []
        detector._history_size = 15
        detector._enable_performance_stats = False
        detector._total_frames_processed = 0
        detector._recognition_calls = 0
        detector._tesserocr_api = CapturingTesseractAPI("5")

        frame = np.full((60, 58, 3), 255, dtype=np.uint8)
        gray = np.full((60, 58), 255, dtype=np.uint8)
        thresholded = np.full((60, 58), 255, dtype=np.uint8)
        resized = np.full((180, 174), 255, dtype=np.uint8)
        resized_rgb = np.full((180, 174, 3), 255, dtype=np.uint8)
        with (
            patch.object(
                lap_detector.cv2,
                "cvtColor",
                side_effect=[gray, resized_rgb] * 3,
            ),
            patch.object(
                lap_detector.cv2,
                "threshold",
                return_value=(200, thresholded),
            ),
            patch.object(lap_detector.cv2, "resize", return_value=resized),
            patch.object(
                lap_detector.Image,
                "fromarray",
                side_effect=lambda image: image,
            ),
        ):
            for _ in range(3):
                lap_number = detector.extract_lap_number(frame)

        self.assertEqual(lap_number, 5)
        self.assertEqual(detector._tesserocr_api.images[-1].shape, (180, 174, 3))


@unittest.skipUnless(lap_detector.USE_TESSEROCR, "tesserocr is not available")
class TestSpeedOCRMode(unittest.TestCase):
    def make_detector(self, api):
        detector = lap_detector.LapDetector.__new__(lap_detector.LapDetector)
        detector.speed_roi = {"x": 0, "y": 0, "width": 54, "height": 32}
        detector._speed_history = []
        detector._history_size = 15
        detector._last_valid_speed = None
        detector._pending_speed_values = []
        detector._tesserocr_api = api
        return detector

    def extract_speed(self, detector):
        converted_roi = np.zeros((32, 54, 3), dtype=np.uint8)
        with (
            patch.object(lap_detector.cv2, "cvtColor", return_value=converted_roi),
            patch.object(lap_detector.Image, "fromarray", side_effect=lambda image: image),
        ):
            return detector.extract_speed(np.zeros((32, 54, 3), dtype=np.uint8))

    def test_extract_speed_uses_single_line_then_restores_single_word(self):
        detector = self.make_detector(FakeTesseractAPI())

        speed = self.extract_speed(detector)

        self.assertEqual(speed, 171)
        self.assertEqual(
            detector._tesserocr_api.page_seg_modes,
            [
                lap_detector.tesserocr.PSM.SINGLE_LINE,
                lap_detector.tesserocr.PSM.SINGLE_WORD,
            ],
        )
        self.assertEqual(detector.get_last_speed_quality(), QualityFlag.OBSERVED)

    def test_extract_speed_restores_single_word_when_ocr_raises(self):
        detector = self.make_detector(FailingTesseractAPI())

        speed = self.extract_speed(detector)

        self.assertIsNone(speed)
        self.assertEqual(
            detector._tesserocr_api.page_seg_modes,
            [
                lap_detector.tesserocr.PSM.SINGLE_LINE,
                lap_detector.tesserocr.PSM.SINGLE_WORD,
            ],
        )
        self.assertEqual(detector.get_last_speed_quality(), QualityFlag.MISSING)

    def test_extract_speed_rejects_large_ocr_jumps_before_smoothing(self):
        detector = self.make_detector(SequenceTesseractAPI(["11", "147", "120"]))
        detector._last_valid_speed = 111
        detector._speed_history = [111] * detector._history_size

        speeds = []
        histories = []
        for _ in range(3):
            speeds.append(self.extract_speed(detector))
            histories.append(detector._speed_history.copy())

        self.assertEqual(speeds, [111, 111, 111])
        self.assertEqual(histories[0], [111] * detector._history_size)
        self.assertEqual(histories[1], [111] * detector._history_size)
        self.assertEqual(histories[2], [111] * 14 + [120])
        self.assertEqual(detector.get_last_speed_quality(), QualityFlag.OBSERVED)

    def test_pending_jump_returns_held_speed_with_explicit_quality(self):
        detector = self.make_detector(SequenceTesseractAPI(["147"]))
        detector._last_valid_speed = 111
        detector._speed_history = [111] * detector._history_size

        speed = self.extract_speed(detector)

        self.assertEqual(speed, 111)
        self.assertEqual(detector.get_last_speed_quality(), QualityFlag.HELD)

    def test_extract_speed_recovers_from_a_confirmed_stable_jump(self):
        readings = ["80"] * 23
        detector = self.make_detector(SequenceTesseractAPI(readings))
        detector._last_valid_speed = 50
        detector._speed_history = [50] * detector._history_size

        speeds = [self.extract_speed(detector) for _ in readings]

        self.assertEqual(speeds[: detector._history_size - 1], [50] * 14)
        self.assertEqual(speeds[detector._history_size - 1], 80)
        self.assertEqual(speeds[-1], 80)
        self.assertEqual(detector._speed_history, [80] * detector._history_size)
        self.assertIsNone(getattr(detector, "_pending_speed_candidate", None))
        self.assertEqual(getattr(detector, "_pending_speed_candidate_count", 0), 0)

    def test_extract_speed_recovers_from_a_confirmed_stable_brake_event(self):
        readings = ["140"] * 15
        detector = self.make_detector(SequenceTesseractAPI(readings))
        detector._last_valid_speed = 200
        detector._speed_history = [200] * detector._history_size

        speeds = [self.extract_speed(detector) for _ in readings]

        self.assertEqual(speeds[: detector._history_size - 1], [200] * 14)
        self.assertEqual(speeds[detector._history_size - 1], 140)
        self.assertEqual(detector._speed_history, [140] * detector._history_size)
        self.assertIsNone(getattr(detector, "_pending_speed_candidate", None))
        self.assertEqual(getattr(detector, "_pending_speed_candidate_count", 0), 0)
        self.assertEqual(getattr(detector, "_pending_speed_values", []), [])

    def test_extract_speed_promotes_representative_median_of_confirmed_window(self):
        readings = ["143"] + ["140"] * 14
        detector = self.make_detector(SequenceTesseractAPI(readings))
        detector._last_valid_speed = 200
        detector._speed_history = [200] * detector._history_size

        speeds = [self.extract_speed(detector) for _ in readings]

        self.assertEqual(speeds[: detector._history_size - 1], [200] * 14)
        self.assertEqual(speeds[detector._history_size - 1], 140)
        self.assertEqual(detector._speed_history, [140] * detector._history_size)
        self.assertEqual(getattr(detector, "_pending_speed_values", []), [])

    def test_extract_speed_tracks_coherent_window_until_median_promotion(self):
        readings = ["80", "83"] * 7 + ["80"]
        detector = self.make_detector(SequenceTesseractAPI(readings))
        detector._last_valid_speed = 50
        detector._speed_history = [50] * detector._history_size

        pending_speeds = [self.extract_speed(detector) for _ in readings[:-1]]
        pending_window = getattr(detector, "_pending_speed_values", []).copy()
        confirmed_speed = self.extract_speed(detector)

        self.assertEqual(pending_speeds, [50] * 14)
        self.assertEqual(pending_window, [int(reading) for reading in readings[:-1]])
        self.assertEqual(getattr(detector, "_pending_speed_values", []), [])
        expected_speed = int(statistics.median(int(reading) for reading in readings))
        self.assertEqual(confirmed_speed, expected_speed)
        self.assertEqual(
            detector._speed_history,
            [expected_speed] * detector._history_size,
        )
        self.assertIsNone(getattr(detector, "_pending_speed_candidate", None))
        self.assertEqual(getattr(detector, "_pending_speed_candidate_count", 0), 0)

    def test_extract_speed_plausible_reading_resets_pending_recovery(self):
        detector = self.make_detector(
            SequenceTesseractAPI(["147"] * 5 + ["120"])
        )
        detector._last_valid_speed = 111
        detector._speed_history = [111] * detector._history_size

        pending_speeds = [self.extract_speed(detector) for _ in range(5)]
        pending_before_plausible_reading = (
            getattr(detector, "_pending_speed_candidate", None),
            getattr(detector, "_pending_speed_candidate_count", 0),
        )
        speed = self.extract_speed(detector)

        self.assertEqual(pending_speeds, [111] * 5)
        self.assertEqual(pending_before_plausible_reading, (147, 5))
        self.assertEqual(speed, 111)
        self.assertIsNone(getattr(detector, "_pending_speed_candidate", None))
        self.assertEqual(getattr(detector, "_pending_speed_candidate_count", 0), 0)
        self.assertEqual(getattr(detector, "_pending_speed_values", []), [])
        self.assertNotIn(147, detector._speed_history)
        self.assertEqual(detector._speed_history[-1], 120)


class TestSpeedOCRFallback(unittest.TestCase):
    def test_extract_speed_uses_single_line_pytesseract_config(self):
        detector = lap_detector.LapDetector.__new__(lap_detector.LapDetector)
        detector.speed_roi = {"x": 0, "y": 0, "width": 54, "height": 32}
        detector._speed_history = []
        detector._history_size = 15
        detector._last_valid_speed = None
        detector._tesserocr_api = None
        detector.tesseract_config_lap = (
            "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789"
        )
        detector.tesseract_config_speed = (
            "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789"
        )

        with patch("pytesseract.image_to_string", return_value="171") as image_to_string:
            speed = detector.extract_speed(
                np.zeros((32, 54, 3), dtype=np.uint8)
            )

        config = image_to_string.call_args.kwargs["config"]
        self.assertEqual(speed, 171)
        self.assertIn("--psm 7", config)
        self.assertNotIn("--psm 8", config)

class TestFieldOCRObservations(unittest.TestCase):
    def make_detector(self):
        detector = lap_detector.LapDetector.__new__(lap_detector.LapDetector)
        detector.speed_roi = detector.gear_roi = dict(x=0, y=0, width=10, height=10)
        detector._speed_history = []
        detector._gear_history = [3] * 15
        detector._history_size = 15
        detector._last_valid_speed = None
        detector._last_valid_gear = 3
        detector._tesserocr_api = None
        detector.tesseract_config_speed = '--psm 7'
        return detector

    def test_speed_raw_rejection_missing_and_existing_filter_are_preserved(self):
        detector = self.make_detector()
        texts = ['100', '', '682', '120']
        with patch('pytesseract.image_to_string', side_effect=texts) as backend:
            observations = [detector.observe_speed(np.zeros((10, 10, 3), np.uint8)) for _ in texts]
        self.assertEqual(backend.call_count, 4)
        self.assertEqual([o.raw_value for o in observations], texts)
        self.assertEqual([o.value for o in observations], [100, 100, 100, 110])
        self.assertEqual([o.quality for o in observations], [QualityFlag.OBSERVED,
            QualityFlag.HELD, QualityFlag.HELD, QualityFlag.OBSERVED])
        self.assertIn('speed_out_of_range', observations[2].reasons)
        self.assertIn('speed_median_filtered', observations[3].reasons)

    def test_speed_unavailable_has_no_value_even_when_raw_is_out_of_range(self):
        detector = self.make_detector()
        with patch('pytesseract.image_to_string', return_value='682'):
            observation = detector.observe_speed(np.zeros((10, 10, 3), np.uint8))
        self.assertIsNone(observation.value)
        self.assertEqual(observation.quality, QualityFlag.MISSING)
        self.assertEqual(observation.raw_value, '682')
        self.assertIn('speed_out_of_range', observation.reasons)

    def test_fresh_gear_does_not_relabel_history_and_neutral_reverse_stay_missing(self):
        detector = self.make_detector()
        texts = ['4', '', 'N', 'R', '4x']
        with patch('pytesseract.image_to_string', side_effect=texts) as backend:
            observations = [detector.observe_gear(np.zeros((10, 10, 3), np.uint8)) for _ in texts]
        self.assertEqual(backend.call_count, 5)
        self.assertEqual([o.value for o in observations], [4, None, None, None, None])
        self.assertEqual([o.raw_value for o in observations], texts)
        self.assertEqual(observations[1].quality, QualityFlag.MISSING)
        self.assertEqual(observations[2].reasons, ('unsupported_gear_symbol',))
        self.assertEqual(observations[3].reasons, ('unsupported_gear_symbol',))
        self.assertEqual(detector._gear_history, [3] * 15)
        self.assertIn('NR', backend.call_args.kwargs['config'])


if __name__ == "__main__":
    unittest.main()
