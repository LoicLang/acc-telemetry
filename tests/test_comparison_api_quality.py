"""Actual comparison/summary endpoints with temporary CSV storage."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pydantic import TypeAdapter

from acc_telemetry.adapters.web.api import telemetry
from acc_telemetry.adapters.web.models import ComparisonRequest, LapComparisonData, TelemetryDataPoint
from acc_telemetry.adapters.web.services.storage import StorageService


def modern_row():
    return dict(frame=0, time=0., lap_number=1, speed=100., gear=None,
        throttle=None, brake=None, steering=None, tc_active=None, abs_active=None,
        track_position=None, s_fused=None, s_odometry=.2, s_visual=None, s_uncertainty=.05,
        s_source='missing', s_reasons='uncertainty_limit', quality_hint='speed_kmh:held',
        field_reasons='{"speed_kmh":["speed_jump_pending"]}', speed_raw='001', gear_raw='R')


class TestComparisonAPIQuality(unittest.IsolatedAsyncioTestCase):
    async def test_comparison_keeps_provenance_and_nulls_through_declared_response(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = StorageService()
            storage.output_dir = Path(directory)
            for name in ('a','b'):
                target = storage.output_dir / name
                target.mkdir()
                pd.DataFrame([modern_row()]).to_csv(target / 'telemetry.csv', index=False)
            with patch.object(telemetry, 'storage', storage):
                result = await telemetry.compare_laps(ComparisonRequest(laps=[
                    dict(video_name=n, lap_number=1) for n in ('a','b')]))
                summary = await telemetry.get_telemetry_summary('a')
            encoded = TypeAdapter(list[LapComparisonData]).dump_json(result)
            row = json.loads(encoded)[0]['data'][0]
            self.assertIsNone(row['throttle'])
            self.assertEqual(row['s_source'], 'missing')
            self.assertEqual(row['s_odometry'], .2)
            self.assertIsNone(row['s_fused'])
            self.assertEqual(row['quality_hint'], 'speed_kmh:held')
            self.assertEqual(row['speed_raw'], '001')
            self.assertEqual(row['field_reasons'], modern_row()['field_reasons'])
            self.assertIsNone(summary['avg_throttle'])

    def test_model_preserves_modern_fields_for_numeric_legacy_controls(self):
        row = modern_row()
        row.update(throttle=0., brake=0., steering=0., tc_active=False, abs_active=False)
        result = TelemetryDataPoint(**row).model_dump()
        for name in ('s_fused','s_odometry','s_visual','s_uncertainty','s_source','s_reasons','quality_hint','field_reasons'):
            self.assertEqual(result[name], row[name])
