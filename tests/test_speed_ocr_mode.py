import unittest

import numpy as np
import tesserocr

from src.lap_detector import LapDetector


class FakeTesseractAPI:
    def __init__(self):
        self.page_seg_modes = []

    def SetPageSegMode(self, mode):
        self.page_seg_modes.append(mode)

    def SetImage(self, image):
        pass

    def GetUTF8Text(self):
        return "171"


class TestSpeedOCRMode(unittest.TestCase):
    def test_extract_speed_uses_single_line_then_restores_single_word(self):
        detector = LapDetector.__new__(LapDetector)
        detector.speed_roi = {"x": 0, "y": 0, "width": 54, "height": 32}
        detector._speed_history = []
        detector._history_size = 15
        detector._last_valid_speed = None
        detector._tesserocr_api = FakeTesseractAPI()

        speed = detector.extract_speed(np.zeros((32, 54, 3), dtype=np.uint8))

        self.assertEqual(speed, 171)
        self.assertEqual(
            detector._tesserocr_api.page_seg_modes,
            [tesserocr.PSM.SINGLE_LINE, tesserocr.PSM.SINGLE_WORD],
        )


if __name__ == "__main__":
    unittest.main()
