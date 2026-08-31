import unittest
from unittest.mock import patch

import numpy as np

from src import lap_detector


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


@unittest.skipUnless(lap_detector.USE_TESSEROCR, "tesserocr is not available")
class TestSpeedOCRMode(unittest.TestCase):
    def make_detector(self, api):
        detector = lap_detector.LapDetector.__new__(lap_detector.LapDetector)
        detector.speed_roi = {"x": 0, "y": 0, "width": 54, "height": 32}
        detector._speed_history = []
        detector._history_size = 15
        detector._last_valid_speed = None
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


if __name__ == "__main__":
    unittest.main()
