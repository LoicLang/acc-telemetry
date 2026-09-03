
import sys
import os
import numpy as np
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from position_tracker_v2 import PositionDecision, PositionTrackerV2
from acc_telemetry.extraction.map_progress import extract_red_candidates

class TestPositionTrackerV2(unittest.TestCase):
    def setUp(self):
        self.tracker = PositionTrackerV2(fps=30.0, max_jump_per_frame=5.0)
        
        # Manually set up a simple square track path
        # 0,0 -> 100,0 -> 100,100 -> 0,100 -> 0,0
        # Total length = 400
        self.tracker.track_path = []
        # Bottom edge
        for x in range(0, 100): self.tracker.track_path.append((x, 0))
        # Right edge
        for y in range(0, 100): self.tracker.track_path.append((100, y))
        # Top edge
        for x in range(100, 0, -1): self.tracker.track_path.append((x, 100))
        # Left edge
        for y in range(100, 0, -1): self.tracker.track_path.append((0, y))
        
        self.tracker.total_path_pixels = len(self.tracker.track_path)
        self.tracker.total_track_length = 400.0 # Approx
        self.tracker.track_center = (50.0, 50.0)
        self.tracker.path_extracted = True
        self.tracker.validation_passed = True
        
        # Mock detect_red_dot to return values we control
        self.tracker.detect_red_dot = MagicMock()

    def test_lap_reset_logic(self):
        """Test that reset_for_new_lap forces 0% and resets start anchor."""
        # 1. Start a lap
        self.tracker.reset_for_new_lap()
        self.assertTrue(self.tracker.lap_just_started)
        
        # 2. First frame: dot at (10, 0) - should be 0%
        self.tracker.detect_red_dot.return_value = (10, 0)
        pos = self.tracker.extract_position(np.zeros((100,100,3), dtype=np.uint8))
        
        self.assertEqual(pos, 0.0)
        self.assertFalse(self.tracker.lap_just_started)
        self.assertEqual(self.tracker.start_position, (10, 0))
        diagnostic = self.tracker.get_last_position_diagnostic()
        self.assertEqual(diagnostic.dot_position, (10, 0))
        self.assertEqual(diagnostic.closest_idx, 10)
        self.assertEqual(diagnostic.start_idx, 10)
        self.assertEqual(diagnostic.start_source, "lap_transition")
        self.assertEqual(diagnostic.raw_position, 0.0)
        self.assertEqual(diagnostic.validated_position, 0.0)
        self.assertEqual(diagnostic.decision, PositionDecision.LAP_RESET)
        
        # 3. Second frame: dot at (20, 0) - moved 10 pixels = 2.5% of 400
        self.tracker.detect_red_dot.return_value = (20, 0)
        pos = self.tracker.extract_position(np.zeros((100,100,3), dtype=np.uint8))
        
        self.assertAlmostEqual(pos, 2.5, delta=0.1)
        diagnostic = self.tracker.get_last_position_diagnostic()
        self.assertEqual(diagnostic.dot_position, (20, 0))
        self.assertEqual(diagnostic.closest_idx, 20)
        self.assertEqual(diagnostic.start_idx, 10)
        self.assertEqual(diagnostic.start_source, "lap_transition")
        self.assertAlmostEqual(diagnostic.raw_position, 2.5, delta=0.1)
        self.assertFalse(diagnostic.completion_forced)
        self.assertAlmostEqual(diagnostic.validated_position, 2.5, delta=0.1)
        self.assertEqual(diagnostic.decision, PositionDecision.OBSERVED)
        
        # 4. Trigger lap reset
        self.tracker.reset_for_new_lap()
        self.assertTrue(self.tracker.lap_just_started)
        self.assertEqual(self.tracker.last_position, 0.0)
        
        # 5. Next frame: dot at (20, 0) - this is the NEW start line
        # Even though it's physically at the same spot, it should be 0% now
        self.tracker.detect_red_dot.return_value = (20, 0)
        pos = self.tracker.extract_position(np.zeros((100,100,3), dtype=np.uint8))
        
        self.assertEqual(pos, 0.0)
        self.assertEqual(self.tracker.start_position, (20, 0))

    def test_validation_smoothing(self):
        """Test that validation smooths jumps and ignores backward movement."""
        self.tracker.max_jump_per_frame = 1.0
        # Setup start
        self.tracker.reset_for_new_lap()
        self.tracker.detect_red_dot.return_value = (0, 0)
        self.tracker.extract_position(np.zeros((1,1), dtype=np.uint8)) # Init at 0%
        
        # 1. Normal move: 0 -> 0.5% (2 pixels)
        self.tracker.detect_red_dot.return_value = (2, 0)
        pos = self.tracker.extract_position(np.zeros((1,1), dtype=np.uint8))
        self.assertAlmostEqual(pos, 0.5, delta=0.1)
        
        # 2. Backward move: 0.5% -> 0.25% (1 pixel) - should be ignored
        self.tracker.detect_red_dot.return_value = (1, 0)
        pos = self.tracker.extract_position(np.zeros((1,1), dtype=np.uint8))
        self.assertAlmostEqual(pos, 0.5, delta=0.1) # Should stay at 0.5
        
        # 3. Huge forward jump: 0.5% -> 5.0% (20 pixels) - should be clamped
        # Max jump is 1.0%
        self.tracker.detect_red_dot.return_value = (20, 0)
        pos = self.tracker.extract_position(np.zeros((1,1), dtype=np.uint8))
        self.assertAlmostEqual(pos, 1.5, delta=0.1) # 0.5 + 1.0 = 1.5
        
    def test_wraparound(self):
        """Test 99% -> 1% wraparound logic."""
        # Manually set last position to 99.5%
        self.tracker.last_position = 99.5
        
        # Mock a raw position of 0.5% (wrapped around)
        # We need to bypass calculate_position logic for this test or set up the dots correctly
        # Let's just test _validate_position directly
        
        val_pos = self.tracker._validate_position(0.5)
        self.assertEqual(val_pos, 0.5) # Should accept it
        self.assertEqual(self.tracker.last_position, 0.5)

    def test_spike_removal(self):
        """Test that sharp spikes (start/finish line artifacts) are removed."""
        # Create a path with a spike
        # 0,0 -> 50,0 -> 50,20 (spike tip) -> 50,0 -> 100,0
        path = []
        for x in range(0, 50): path.append((x, 0))
        # Spike out
        for y in range(0, 20): path.append((50, y))
        # Spike back
        for y in range(20, 0, -1): path.append((50, y))
        # Continue
        for x in range(50, 100): path.append((x, 0))
        
        # Clean path
        cleaned = self.tracker._remove_path_spikes(path, window=5, angle_threshold=60.0)
        
        # Verify spike is gone
        # The path should be roughly 0,0 -> 100,0
        # Length should be much smaller than original
        original_len = len(path)
        cleaned_len = len(cleaned)
        
        self.assertLess(cleaned_len, original_len - 30) # Should remove at least 30 points (spike is 40 total)
        
        # Verify no points have y > 5 (spike went to y=20)
        max_y = 0
        for p in cleaned:
            if p[1] > max_y: max_y = p[1]
            
        self.assertLess(max_y, 5)

    def test_position_from_closest_index_prefers_forward_direction(self):
        """Test that a small forward distance yields a forward travel direction."""
        self.tracker.total_track_length = 100.0
        self.tracker.start_idx = 0

        with patch.object(self.tracker, "_calculate_path_distance", return_value=2.0):
            pos = self.tracker._position_from_closest_index(2)

        self.assertEqual(pos, 2.0)
        self.assertEqual(self.tracker.travel_direction, 1)

    def test_position_from_closest_index_prefers_reverse_direction(self):
        """Test that a near-complete forward distance yields a reverse travel direction."""
        self.tracker.total_track_length = 100.0
        self.tracker.start_idx = 0

        with patch.object(self.tracker, "_calculate_path_distance", return_value=98.0):
            pos = self.tracker._position_from_closest_index(98)

        self.assertEqual(pos, 2.0)
        self.assertEqual(self.tracker.travel_direction, -1)

    def test_position_from_closest_index_initializes_forward_mid_lap(self):
        """Test that direction initializes for a shorter forward arc even mid-lap."""
        self.tracker.total_track_length = 100.0
        self.tracker.start_idx = 0

        with patch.object(self.tracker, "_calculate_path_distance", return_value=40.0):
            pos = self.tracker._position_from_closest_index(40)

        self.assertEqual(pos, 40.0)
        self.assertEqual(self.tracker.travel_direction, 1)

    def test_position_from_closest_index_initializes_reverse_mid_lap(self):
        """Test that direction initializes for a shorter reverse arc even mid-lap."""
        self.tracker.total_track_length = 100.0
        self.tracker.start_idx = 0

        with patch.object(self.tracker, "_calculate_path_distance", return_value=60.0):
            pos = self.tracker._position_from_closest_index(60)

        self.assertEqual(pos, 40.0)
        self.assertEqual(self.tracker.travel_direction, -1)

    def test_position_from_closest_index_holds_zero_for_near_zero_movement(self):
        """Test that near-zero movement does not lock a travel direction."""
        self.tracker.total_track_length = 100.0
        self.tracker.start_idx = 0

        with patch.object(self.tracker, "_calculate_path_distance", return_value=0.01):
            pos = self.tracker._position_from_closest_index(0)

        self.assertEqual(pos, 0.0)
        self.assertIsNone(self.tracker.travel_direction)

    def test_validation_clamps_large_jump_from_zero(self):
        """Test that an initial large jump from zero is clamped instead of accepted raw."""
        self.tracker.max_jump_per_frame = 1.0
        self.tracker.last_position = 0.0

        pos = self.tracker._validate_position(20.0)

        self.assertEqual(pos, 1.0)
        self.assertEqual(self.tracker.last_position, 1.0)

    def test_diagnostic_marks_missing_position_as_held(self):
        self.tracker.start_position = (0, 0)
        self.tracker.start_idx = 0
        self.tracker.start_source = "geometric"
        self.tracker.travel_direction = 1
        self.tracker.last_position = 12.0
        self.tracker.detect_red_dot.return_value = None

        position = self.tracker.extract_position(np.zeros((1, 1), dtype=np.uint8))

        self.assertEqual(position, 12.0)
        self.assertEqual(
            self.tracker.get_last_position_diagnostic().decision,
            PositionDecision.MISSING_HELD,
        )

    def test_diagnostic_marks_backward_position_as_held(self):
        self.tracker.start_position = (0, 0)
        self.tracker.start_idx = 0
        self.tracker.start_source = "geometric"
        self.tracker.travel_direction = 1
        self.tracker.last_position = 10.0
        self.tracker.detect_red_dot.return_value = (20, 0)

        position = self.tracker.extract_position(np.zeros((1, 1), dtype=np.uint8))

        self.assertEqual(position, 10.0)
        diagnostic = self.tracker.get_last_position_diagnostic()
        self.assertAlmostEqual(diagnostic.raw_position, 5.0, delta=0.1)
        self.assertEqual(diagnostic.decision, PositionDecision.BACKWARD_HELD)

    def test_diagnostic_marks_large_jump_as_clamped(self):
        self.tracker.start_position = (0, 0)
        self.tracker.start_idx = 0
        self.tracker.start_source = "geometric"
        self.tracker.travel_direction = 1
        self.tracker.last_position = 0.0
        self.tracker.max_jump_per_frame = 1.0
        self.tracker.detect_red_dot.return_value = (20, 0)

        position = self.tracker.extract_position(np.zeros((1, 1), dtype=np.uint8))

        self.assertEqual(position, 1.0)
        self.assertEqual(
            self.tracker.get_last_position_diagnostic().decision,
            PositionDecision.JUMP_CLAMPED,
        )

    def test_diagnostic_marks_smoothed_position(self):
        self.tracker.start_position = (0, 0)
        self.tracker.start_idx = 0
        self.tracker.start_source = "geometric"
        self.tracker.travel_direction = 1
        self.tracker.last_position = 10.0
        self.tracker.max_jump_per_frame = 5.0
        self.tracker.detect_red_dot.return_value = (44, 0)

        position = self.tracker.extract_position(np.zeros((1, 1), dtype=np.uint8))

        self.assertAlmostEqual(position, 10.8, delta=0.1)
        self.assertEqual(
            self.tracker.get_last_position_diagnostic().decision,
            PositionDecision.SMOOTHED,
        )

    def test_diagnostic_exposes_forced_completion(self):
        self.tracker.start_position = (0, 0)
        self.tracker.start_idx = 0
        self.tracker.start_source = "geometric"
        self.tracker.travel_direction = 1
        self.tracker.last_position = 96.0
        self.tracker.max_jump_per_frame = 5.0
        self.tracker.detect_red_dot.return_value = (40, 0)

        position = self.tracker.extract_position(np.zeros((1, 1), dtype=np.uint8))

        self.assertAlmostEqual(position, 99.8, delta=0.1)
        diagnostic = self.tracker.get_last_position_diagnostic()
        self.assertAlmostEqual(diagnostic.raw_position, 10.0, delta=0.1)
        self.assertTrue(diagnostic.completion_forced)
        self.assertEqual(diagnostic.decision, PositionDecision.FORCED_COMPLETION)

    def test_characterizes_projection_switching_between_contour_branches(self):
        first_branch = [(x, 0) for x in range(50)]
        nearby_return_branch = [(x, 1) for x in range(49, -1, -1)]
        self.tracker.track_path = first_branch + nearby_return_branch

        first_index = self.tracker._closest_path_index(25, 0)
        nearby_index = self.tracker._closest_path_index(25, 1)

        self.assertEqual(first_index, 25)
        self.assertEqual(nearby_index, 74)
        self.assertGreater(abs(nearby_index - first_index), 40)

    def test_characterizes_large_red_background_masking_valid_dot(self):
        roi = np.zeros((100, 100, 3), dtype=np.uint8)
        roi[0:31, 0:31] = (0, 0, 255)
        roi[67:74, 67:74] = (0, 0, 255)

        dot = PositionTrackerV2().detect_red_dot(roi)
        candidates = extract_red_candidates(
            roi,
            min_area_fraction=0.00002,
            max_area_fraction=0.005,
            min_circularity=0.35,
        )

        self.assertIsNone(dot)
        self.assertEqual(
            [candidate.centroid for candidate in candidates],
            [(70.0, 70.0)],
        )

if __name__ == '__main__':
    unittest.main()
