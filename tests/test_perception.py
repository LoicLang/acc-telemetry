"""Meaningful M1 checks: neutral transitions, missing evidence and complete routing."""
from dataclasses import replace
import unittest

from acc_telemetry.domain.telemetry import TelemetrySample, QualityFlag as Q
from acc_telemetry.analysis.perception import EventSettings, control_events, gear_events, missing_intervals, validate_zones, select_lap


def sample(frame, brake=0., throttle=0., speed=100., gear=3, time=None):
    values=dict(speed_kmh=speed,brake_pct=brake,throttle_pct=throttle,gear=gear)
    return TelemetrySample(frame=frame,time_s=frame/60 if time is None else time,lap_number=4,
        lap_time_s=None,s=None,steering=None,tc_active=None,abs_active=None,
        field_quality={k:Q.MISSING if v is None else Q.OBSERVED for k,v in values.items()},
        field_reasons={k:('hud_visibility_unverified',) for k in values},**values)


class TestPerception(unittest.TestCase):
    def test_short_pulse_is_not_confirmed_and_onset_keeps_first_frame(self):
        values=[0]*4+[20]*3+[0]*4+[20]*8+[0]*8
        events=control_events([sample(i,brake=v) for i,v in enumerate(values)],'brake_pct',EventSettings())
        on=[e for e in events if e['type']=='brake_on']
        off=[e for e in events if e['type']=='brake_off']
        self.assertEqual([e['frame'] for e in on],[11])
        self.assertEqual(on[0]['confirmed_frame'],17)
        self.assertEqual(off[0]['frame'],19)
        self.assertEqual(on[0]['status'],'candidate')
        self.assertIn('hud_visibility_unverified',on[0]['reasons'])

    def test_missing_or_held_breaks_evidence_without_fabricating_release(self):
        rows=[sample(i,brake=100) for i in range(8)]+[sample(8,brake=None)]+[sample(i,brake=0) for i in range(9,18)]
        events=control_events(rows,'brake_pct',EventSettings())
        self.assertEqual(events[0]['type'],'brake_active_unbounded')
        self.assertFalse(any(e['type']=='brake_off' for e in events))
        rows[8]=replace(sample(8,brake=100),field_quality={'brake_pct':Q.HELD})
        self.assertFalse(any(e['type']=='brake_off' for e in control_events(rows,'brake_pct',EventSettings())))

    def test_timestamp_gap_cannot_bridge_a_pending_transition(self):
        rows=[sample(0)]+[sample(i,brake=100) for i in range(1,5)]+[sample(30,brake=100)]
        events=control_events(rows,'brake_pct',EventSettings())
        self.assertFalse(any(e['type']=='brake_on' for e in events))
        self.assertEqual(events[-1]['type'],'brake_active_unbounded')

    def test_gear_change_requires_two_fresh_adjacent_observations(self):
        rows=[sample(0,gear=3),sample(1,gear=4),sample(2,gear=None),sample(3,gear=2)]
        events=gear_events(rows,EventSettings())
        self.assertEqual([(e['from_value'],e['to_value']) for e in events],[(3,4)])

    def test_missing_intervals_preserve_end_exclusive_frame_bounds(self):
        rows=[sample(0),sample(1,speed=None),sample(2,speed=None),sample(3)]
        result=missing_intervals(rows,'speed_kmh',60)
        self.assertEqual(result[0]['start_frame'],1)
        self.assertEqual(result[0]['end_frame_exclusive'],3)
        self.assertAlmostEqual(result[0]['end_time_s'],3/60)

    def test_zone_partition_must_cover_every_frame_once(self):
        zones=[dict(id='a',label='A',start_frame=19,end_frame=50),dict(id='b',label='B',start_frame=50,end_frame=99)]
        validate_zones(zones,19,99)
        for broken in ([dict(zones[0],end_frame=49),zones[1]], [zones[0],dict(zones[1],start_frame=49)], [zones[0]], [zones[0],dict(zones[1],id='a')]):
            with self.assertRaises(ValueError):validate_zones(broken,19,99)

    def test_lap_uses_confirmations_and_rejects_final_partial(self):
        m={'lap_transitions':[dict(to_lap=4,frame=19,confirmed_at_s=19/60),dict(to_lap=5,frame=99,confirmed_at_s=99/60)]}
        lap=select_lap(m,4)
        self.assertEqual((lap['start_frame'],lap['end_frame']),(19,99))
        with self.assertRaises(ValueError):select_lap(m,5)

    def test_settings_are_finite_positive_and_hysteresis_is_ordered(self):
        for kwargs in (dict(on_pct=2,off_pct=5),dict(persistence_s=0),dict(max_gap_s=float('nan')),dict(on_pct=True)):
            with self.assertRaises(ValueError):EventSettings(**kwargs)
