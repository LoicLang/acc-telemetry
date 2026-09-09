"""Conservative causal speed admission; no smoothing, holding or reconstruction."""
from dataclasses import replace
import math
from acc_telemetry.domain.observations import FieldObservation
from acc_telemetry.domain.telemetry import QualityFlag as Q


class SpeedAdmission:
    def __init__(self, *, max_acceleration_m_s2: float, max_gap_s: float):
        if any(isinstance(v, bool) or not isinstance(v, (int, float))
               or not math.isfinite(v) or v <= 0 for v in (max_acceleration_m_s2, max_gap_s)):
            raise ValueError('speed admission limits must be finite and positive')
        self.max_acceleration_m_s2 = max_acceleration_m_s2
        self.max_gap_s = max_gap_s
        self.previous = None
        self.context = None

    def observe(self, observation: FieldObservation, *, time_s: float, context=None):
        if context != self.context:
            self.previous = None
            self.context = context
        if observation.quality != Q.OBSERVED or observation.value is None:
            self.previous = None
            return observation
        if (isinstance(observation.value, bool) or not isinstance(observation.value, (int, float))
                or not math.isfinite(observation.value) or observation.value < 0):
            self.previous = None
            return replace(observation, value=None, quality=Q.ANOMALOUS,
                           reasons=observation.reasons + ('speed_value_invalid',))
        if (isinstance(time_s, bool) or not isinstance(time_s, (int, float))
                or not math.isfinite(time_s) or time_s < 0):
            self.previous = None
            return replace(observation, value=None, quality=Q.ANOMALOUS,
                           reasons=observation.reasons + ('speed_timebase_invalid',))
        if self.previous is not None:
            previous_time, previous_value = self.previous
            dt = time_s - previous_time
            if dt <= 0:
                self.previous = None
                return replace(observation, value=None, quality=Q.ANOMALOUS,
                               reasons=observation.reasons + ('speed_timebase_invalid',))
            allowed_delta = self.max_acceleration_m_s2 * 3.6 * dt
            delta = abs(observation.value - previous_value)
            if dt <= self.max_gap_s and delta > allowed_delta and not math.isclose(delta, allowed_delta):
                self.previous = None
                return replace(observation, value=None, quality=Q.ANOMALOUS,
                               reasons=observation.reasons + ('speed_rate_exceeded',))
        self.previous = (time_s, observation.value)
        return observation
