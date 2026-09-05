"""Pure temporal confirmation for raw lap-number observations."""

from dataclasses import dataclass

from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.domain.progress import ConfirmedLapBoundary, LapObservation


@dataclass(frozen=True)
class LapState:
    """Raw and confirmed lap state after one observation."""

    raw_lap_number: int | None
    confirmed_lap_number: int | None
    boundary: ConfirmedLapBoundary | None
    confidence: float
    reasons: tuple[str, ...]

    @property
    def quality(self) -> QualityFlag:
        """Quality of the confirmed label at this frame, not of the raw OCR."""
        if self.confirmed_lap_number is None:
            return QualityFlag.MISSING
        return (QualityFlag.OBSERVED if self.raw_lap_number == self.confirmed_lap_number
                else QualityFlag.HELD)


class LapTransitionConfirmer:
    """Require stable sequential evidence before publishing a lap boundary.

    Confidence is a consensus score, not a calibrated accuracy probability.
    Sustained plausible OCR errors can still confirm a false boundary.
    """

    def __init__(self, *, consecutive_observations: int):
        if consecutive_observations <= 0:
            raise ValueError("consecutive_observations must be positive")
        self.consecutive_observations = consecutive_observations
        self.confirmed_lap_number: int | None = None
        self._pending_lap_number: int | None = None
        self._pending_count = 0
        self._first_candidate_time_s: float | None = None
        self._last_confirmed_observed_time_s: float | None = None

    def _clear_pending(self) -> None:
        self._pending_lap_number = None
        self._pending_count = 0
        self._first_candidate_time_s = None

    def _advance_pending(self, lap_number: int, time_s: float) -> float:
        if self._pending_lap_number == lap_number:
            self._pending_count += 1
        else:
            self._pending_lap_number = lap_number
            self._pending_count = 1
            self._first_candidate_time_s = time_s
        return min(1.0, self._pending_count / self.consecutive_observations)

    def observe(self, observation: LapObservation) -> LapState:
        """Retain raw evidence and emit at most one trusted boundary."""
        raw = observation.raw_lap_number
        if raw is None:
            self._clear_pending()
            return LapState(
                raw_lap_number=None,
                confirmed_lap_number=self.confirmed_lap_number,
                boundary=None,
                confidence=0.0,
                reasons=("lap_observation_missing",),
            )

        if self.confirmed_lap_number is None:
            confidence = self._advance_pending(raw, observation.time_s)
            reasons = ("lap_confirmation_pending",)
            if self._pending_count >= self.consecutive_observations:
                self.confirmed_lap_number = raw
                self._last_confirmed_observed_time_s = observation.time_s
                self._clear_pending()
                reasons = ("lap_initial_confirmed",)
            return LapState(
                raw_lap_number=raw,
                confirmed_lap_number=self.confirmed_lap_number,
                boundary=None,
                confidence=confidence,
                reasons=reasons,
            )

        if raw == self.confirmed_lap_number:
            self._last_confirmed_observed_time_s = observation.time_s
            self._clear_pending()
            return LapState(raw, self.confirmed_lap_number, None, 1.0, ())

        if raw != self.confirmed_lap_number + 1:
            self._clear_pending()
            return LapState(
                raw,
                self.confirmed_lap_number,
                None,
                0.0,
                ("lap_observation_rejected",),
            )

        confidence = self._advance_pending(raw, observation.time_s)
        if self._pending_count < self.consecutive_observations:
            return LapState(
                raw,
                self.confirmed_lap_number,
                None,
                confidence,
                ("lap_confirmation_pending",),
            )

        previous_lap = self.confirmed_lap_number
        boundary = ConfirmedLapBoundary(
            frame=observation.frame,
            time_s=observation.time_s,
            from_lap=previous_lap,
            to_lap=raw,
            confidence=confidence,
            first_candidate_time_s=self._first_candidate_time_s,
            confirmed_at_s=observation.time_s,
            last_previous_lap_observed_time_s=self._last_confirmed_observed_time_s,
        )
        self._last_confirmed_observed_time_s = observation.time_s
        self.confirmed_lap_number = raw
        self._clear_pending()
        return LapState(
            raw,
            self.confirmed_lap_number,
            boundary,
            confidence,
            ("lap_boundary_confirmed",),
        )
