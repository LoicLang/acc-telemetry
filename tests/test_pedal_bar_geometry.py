"""Spatial pedal fill must reject HUD fragments without losing small real inputs."""
import unittest
import numpy as np

from acc_telemetry.extraction.controls import TelemetryExtractor as T
from acc_telemetry.analysis.perception import EventSettings, control_events
from test_perception import sample


class TestPedalBarGeometry(unittest.TestCase):
    def read(self, image, mode='left_connected'):
        return T.extract_bar_percentage(image, 'green', 'horizontal', horizontal_mode=mode)

    def test_disconnected_text_does_not_keep_throttle_active(self):
        image = np.full((21, 144, 3), 40, np.uint8)
        image[12:20, 100:103] = (0, 255, 0)
        # Reproduce the old counterexample: 3/144 exceeds the unchanged off threshold.
        self.assertGreater(self.read(image, 'longest_run'), 2)
        self.assertEqual(self.read(image), 0)

    def test_empty_rows_count_and_single_graphic_row_cannot_create_fill(self):
        image = np.full((21, 144, 3), 40, np.uint8)
        image[2, :30] = (0, 255, 0)
        self.assertGreater(self.read(image, 'longest_run'), 5)
        self.assertEqual(self.read(image), 0)

    def test_actual_small_and_full_fill_survive_disconnected_fragments(self):
        for width in (1, 2, 3, 7, 72, 144):
            image = np.full((21, 144, 3), 40, np.uint8)
            image[:, :width] = (0, 255, 0)
            if width < 72:
                image[:, 100:110] = (0, 255, 0)
            self.assertAlmostEqual(self.read(image), width/144*100)

    def test_text_holes_leave_sufficient_unobscured_rows_at_full_scale(self):
        image = np.full((21, 144, 3), (0, 255, 0), np.uint8)
        image[7:16, 20:28] = 255
        self.assertEqual(self.read(image), 100)

    def test_corrected_off_and_reprise_use_existing_persistence(self):
        full = np.full((21, 144, 3), (0, 255, 0), np.uint8)
        residue = np.full((21, 144, 3), 40, np.uint8)
        residue[12:20, 100:103] = (0, 255, 0)
        images = [full]*8 + [residue]*10 + [full]*10
        rows = [sample(i, throttle=self.read(im)) for i, im in enumerate(images)]
        events = control_events(rows, 'throttle_pct', EventSettings())
        self.assertEqual([(e['type'], e['frame']) for e in events],
                         [('throttle_active_unbounded',0), ('throttle_off',8), ('throttle_on',18)])
        self.assertEqual(events[1]['confirmed_frame'],14)

    def test_unknown_mode_fails_and_legacy_is_still_default(self):
        with self.assertRaises(ValueError): T(horizontal_bar_mode='guess')
        with self.assertRaises(ValueError): self.read(np.ones((4,4,3),np.uint8),'guess')
        self.assertEqual(T().horizontal_bar_mode, 'longest_run')
