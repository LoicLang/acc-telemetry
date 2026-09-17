#!/usr/bin/env python3
"""Print episode data from synthetic controls; no capture, OCR or private dataset."""
import json

from acc_telemetry.analysis.control_episodes import build_control_episodes
from acc_telemetry.domain.telemetry import QualityFlag as Q, TelemetrySample


def synthetic_samples():
    for frame in range(160):
        brake = (0 if frame < 30 else 70 if frame < 60 else 30 if frame < 75
                 else 0 if frame < 100 else 40 if frame < 110 else None
                 if frame < 115 else 20 if frame < 130 else 0)
        throttle = 90 if frame < 20 or frame >= 120 else 50 if 80 <= frame < 100 else 0
        values = dict(speed_kmh=None, brake_pct=brake, throttle_pct=throttle, gear=None,
                      steering=None, tc_active=None, abs_active=None)
        yield TelemetrySample(frame=frame, time_s=frame/60, lap_number=None,
                              lap_time_s=None, s=None, **values,
                              field_quality={k: Q.MISSING if v is None else Q.OBSERVED for k,v in values.items()},
                              field_reasons={k: ('synthetic_demo',) for k in values})


if __name__ == '__main__':
    result = build_control_episodes(synthetic_samples())
    result['provenance'] = 'synthetic_demo_not_driving_measurements'
    print(json.dumps(result, indent=2, allow_nan=False))
