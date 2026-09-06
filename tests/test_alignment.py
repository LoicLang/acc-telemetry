"""Evidence coverage regressions for the actual position comparator."""
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer


def rows(positions, times=None):
    return [dict(frame=i, time=(times[i] if times else i * .02), lap_number=1,
        track_position=p, throttle=50., brake=0., steering=0., speed=100.)
        for i, p in enumerate(positions)]


class TestAlignment(unittest.TestCase):
    def test_partial_lap_never_extends_to_whole_track(self):
        visualizer = InteractiveTelemetryVisualizer.__new__(InteractiveTelemetryVisualizer)
        result = visualizer._resample_lap_by_position(pd.DataFrame(rows([20, 30])))
        self.assertTrue(result.loc[(result.position < 20) | (result.position > 30), 'speed'].isna().all())
        self.assertTrue(result.loc[(result.position > 20) & (result.position < 30), 'speed'].isna().all())

    def test_bounded_interpolation_and_invalid_inputs(self):
        fn = importlib.import_module('acc_telemetry.analysis.alignment').bounded_interpolate
        values = fn([.2, .202, .3], [10, 20, 30], [.1, .2, .201, .25, .3, .4], max_x_gap=.005)
        np.testing.assert_allclose(values, [np.nan, 10, 15, np.nan, 30, np.nan], equal_nan=True)
        for x, y in (([1, 1], [1, 2]), ([2, 1], [1, 2]), ([1, 2], [1, np.inf])):
            with self.assertRaises(ValueError):
                fn(x, y, [1], max_x_gap=.1)

    def test_gaps_duplicates_backward_and_nonfinite_are_not_repaired_by_sorting(self):
        fn = importlib.import_module('acc_telemetry.analysis.alignment').resample_records
        for positions in ([20, None, 20.4], [20, 20, 20.4], [20.4, 20], [20, np.inf, 20.4]):
            with self.subTest(positions=positions):
                result = fn(rows(positions), [.202], max_position_gap_s=.005, max_time_gap_s=.1)
                self.assertTrue(np.isnan(result['speed'][0]))
        result = fn(rows([20, 20.4], [0, .2]), [.202], max_position_gap_s=.005, max_time_gap_s=.1)
        self.assertTrue(np.isnan(result['speed'][0]))

    def test_field_quality_and_gate_are_required_for_coaching(self):
        fn = importlib.import_module('acc_telemetry.analysis.alignment').resample_records
        data = rows([20, 20.4])
        for row in data:
            row.update(s_fused=row['track_position']/100, s_source='fused', s_uncertainty=.001,
                       quality_hint='speed_kmh:observed;throttle_pct:held')
        kwargs = dict(max_position_gap_s=.005, max_time_gap_s=.1, max_s_uncertainty=.05)
        self.assertTrue(np.isnan(fn(data, [.202], coaching=True, **kwargs)['speed'][0]))
        result = fn(data, [.202], coaching=True, progress_gate_passed=True, **kwargs)
        self.assertEqual(result['speed_quality'][0], 'interpolated')
        self.assertEqual(result['speed'][0], 100)
        self.assertTrue(np.isnan(result['throttle'][0]))

    def test_delta_uses_confirmed_boundary_and_only_common_coverage(self):
        visualizer = InteractiveTelemetryVisualizer.__new__(InteractiveTelemetryVisualizer)
        a = pd.DataFrame(dict(position=[20, 21, 22], time=[12., np.nan, 14.],
                              lap_start_time_s=[10.]*3))
        b = pd.DataFrame(dict(position=[20, 21, 22], time=[23., 24., np.nan],
                              lap_start_time_s=[20.]*3))
        np.testing.assert_allclose(visualizer._calculate_time_delta(a,b), [-1,np.nan,np.nan], equal_nan=True)
        b['lap_start_time_s'] = np.nan
        self.assertTrue(np.isnan(visualizer._calculate_time_delta(a,b)).all())

    def test_report_preserves_missing_rows_before_resampling_and_breaks_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            visualizer = InteractiveTelemetryVisualizer(directory)
            data = rows([20, None, 20.5])
            data += [dict(row, lap_number=2) for row in data]
            with patch('plotly.graph_objects.Figure.write_html', autospec=True) as write:
                visualizer.plot_position_based_comparison(pd.DataFrame(data))
                write.assert_called_once()
                figure = write.call_args.args[0]
                throttle = figure.data[0]
                self.assertFalse(throttle.connectgaps)
                i = list(throttle.x).index(20.)
                j = list(throttle.x).index(20.5)
                self.assertIn(None, list(throttle.y)[i+1:j])
                self.assertTrue(all(v is None for v in figure.data[-1].y))


class TestAlignmentAdditionalEvidence(unittest.TestCase):
    def test_overlapping_forward_runs_are_ambiguous_not_last_value_wins(self):
        from acc_telemetry.analysis.alignment import resample_records
        data = rows([20,20.4,20.1,20.5])
        result = resample_records(data, [.202], max_position_gap_s=.005, max_time_gap_s=.1)
        self.assertTrue(np.isnan(result['speed'][0]))
        self.assertEqual(result['speed_quality'][0], 'ambiguous')

    def test_no_common_coverage_has_no_delta(self):
        from acc_telemetry.analysis.alignment import common_time_delta
        a = dict(position=[20,21], time=[1.,np.nan], lap_start_time_s=[0.,0.])
        b = dict(position=[20,21], time=[np.nan,3.], lap_start_time_s=[0.,0.])
        self.assertTrue(np.isnan(common_time_delta(a,b)).all())

    def test_confirmed_start_survives_missing_progress_at_boundary(self):
        from acc_telemetry.analysis.alignment import resample_records
        data = rows([None,20,20.4], [10.,12.,12.02])
        data[0]['s_reasons'] = 'lap_boundary_confirmed;calibration_unavailable'
        result = resample_records(data, [.202], max_position_gap_s=.005, max_time_gap_s=.1)
        self.assertEqual(result['lap_start_time_s'][0], 10.)
        self.assertAlmostEqual(result['time'][0], 12.01)

    def test_legacy_points_remain_unverified_and_held_channel_does_not_bridge(self):
        from acc_telemetry.analysis.alignment import resample_records
        data = rows([20,20.2,20.4])
        data[1]['quality_hint'] = 'speed_kmh:held'
        result = resample_records(data, [.20,.201,.202,.203,.204],
            max_position_gap_s=.005, max_time_gap_s=.1)
        self.assertEqual(result['speed_quality'][0], 'legacy_unverified')
        self.assertTrue(np.isnan(result['speed'][1:4]).all())

    def test_comparison_limits_are_validated(self):
        import yaml
        from acc_telemetry.application.config import load_settings, ConfigurationError
        from test_configuration import _write_configuration, ROOT
        base = yaml.safe_load((ROOT / 'config' / 'telemetry.yaml').read_text())
        self.assertEqual(load_settings().comparison.max_position_gap_s, .005)
        self.assertEqual(load_settings().comparison.max_time_gap_s, .1)
        for key in ('max_position_gap_s','max_time_gap_s'):
            for invalid in (0,-1,float('nan'),float('inf'),True):
                with self.subTest(key=key, value=invalid), tempfile.TemporaryDirectory() as directory:
                    base['comparison'][key] = invalid
                    _write_configuration(Path(directory), base)
                    with self.assertRaises(ConfigurationError):
                        load_settings(Path(directory))
            base['comparison'][key] = .005 if key == 'max_position_gap_s' else .1

    def test_absent_or_nonfinite_boundary_times_never_produce_a_delta(self):
        from acc_telemetry.analysis.alignment import common_time_delta
        a = dict(position=[20], time=[1.])
        b = dict(position=[20], time=[3.], lap_start_time_s=[0.])
        self.assertTrue(np.isnan(common_time_delta(a,b)).all())
        a['lap_start_time_s'] = [float('inf')]
        self.assertTrue(np.isnan(common_time_delta(a,b)).all())

    def test_anomalous_position_hint_overrides_plausible_fused_source(self):
        from acc_telemetry.analysis.alignment import resample_records
        data = rows([20,20.4])
        for row in data:
            row.update(s_fused=row['track_position']/100, s_source='fused', s_uncertainty=.001,
                       quality_hint='s:anomalous;speed_kmh:observed')
        result = resample_records(data, [.202], max_position_gap_s=.005, max_time_gap_s=.1,
            max_s_uncertainty=.05, coaching=True, progress_gate_passed=True)
        self.assertTrue(np.isnan(result['speed'][0]))
