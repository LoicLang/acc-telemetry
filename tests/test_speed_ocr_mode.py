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


if __name__ == "__main__":
    unittest.main()
