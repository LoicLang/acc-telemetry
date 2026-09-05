"""Tests for raw lap evidence and trusted temporal confirmation."""

import unittest

from acc_telemetry.application.lap_state import LapTransitionConfirmer
from acc_telemetry.domain.progress import LapObservation


def _observe(confirmer, values, *, start_frame=0):
    states = []
    for offset, value in enumerate(values):
        frame = start_frame + offset
        states.append(
            confirmer.observe(
                LapObservation(frame=frame, time_s=frame / 60.0, raw_lap_number=value)
            )
        )
    return states


class TestLapTransitionConfirmer(unittest.TestCase):
    def setUp(self):
        self.confirmer = LapTransitionConfirmer(consecutive_observations=5)

    def initialize_lap_eight(self):
        states = _observe(self.confirmer, [8, 8, 8, 8, 8])
        self.assertEqual(states[-1].confirmed_lap_number, 8)
        self.assertIsNone(states[-1].boundary)

    def test_initial_state_requires_consensus_without_emitting_a_boundary(self):
        states = _observe(self.confirmer, [8, 8, 8, 8, 8])

        self.assertIsNone(states[3].confirmed_lap_number)
        self.assertEqual(states[3].confidence, 0.8)
        self.assertEqual(states[4].confirmed_lap_number, 8)
        self.assertEqual(states[4].confidence, 1.0)
        self.assertIsNone(states[4].boundary)

    def test_isolated_increment_does_not_confirm_a_boundary(self):
        self.initialize_lap_eight()

        states = _observe(self.confirmer, [8, 8, 9, 8, 8], start_frame=5)

        self.assertTrue(all(state.boundary is None for state in states))
        self.assertEqual(states[-1].confirmed_lap_number, 8)

    def test_fifth_stable_increment_emits_exactly_one_boundary(self):
        self.initialize_lap_eight()

        states = _observe(self.confirmer, [9, 9, 9, 9, 9, 9], start_frame=5)
        boundaries = [state.boundary for state in states if state.boundary is not None]

        self.assertEqual(len(boundaries), 1)
        self.assertEqual(boundaries[0].from_lap, 8)
        self.assertEqual(boundaries[0].to_lap, 9)
        self.assertEqual(boundaries[0].frame, 9)
        self.assertEqual(boundaries[0].confidence, 1.0)
        self.assertEqual(states[-1].confirmed_lap_number, 9)

    def test_missing_value_retains_confirmation_without_boundary(self):
        self.initialize_lap_eight()

        state = _observe(self.confirmer, [None], start_frame=5)[0]

        self.assertIsNone(state.raw_lap_number)
        self.assertEqual(state.confirmed_lap_number, 8)
        self.assertIsNone(state.boundary)
        self.assertEqual(state.reasons, ("lap_observation_missing",))

    def test_invalid_jump_or_decrease_never_confirms(self):
        self.initialize_lap_eight()

        states = _observe(self.confirmer, [10, 10, 10, 10, 10, 7, 7, 7, 7, 7], start_frame=5)

        self.assertTrue(all(state.boundary is None for state in states))
        self.assertTrue(all(state.confirmed_lap_number == 8 for state in states))
        self.assertTrue(all("lap_observation_rejected" in state.reasons for state in states))

    def test_gap_restarts_candidate_timing_without_moving_confirmation_anchor(self):
        self.initialize_lap_eight()
        states = _observe(self.confirmer, [9, None, 9, 9, 9, 9, 9, None], start_frame=5)
        boundary = states[-2].boundary
        self.assertEqual(boundary.first_candidate_time_s, 7 / 60)
        self.assertEqual(boundary.last_previous_lap_observed_time_s, 4 / 60)
        self.assertEqual(boundary.confirmed_at_s, 11 / 60)
        self.assertEqual(boundary.time_s, boundary.confirmed_at_s)
        self.assertIsNone(states[-1].boundary)
        self.assertEqual(states[-1].confirmed_lap_number, 9)

    def test_pending_confidence_tracks_stable_observation_count(self):
        self.initialize_lap_eight()

        states = _observe(self.confirmer, [9, 9, 9, 9], start_frame=5)

        self.assertEqual([state.confidence for state in states], [0.2, 0.4, 0.6, 0.8])
        self.assertTrue(all(state.raw_lap_number == 9 for state in states))


if __name__ == "__main__":
    unittest.main()
