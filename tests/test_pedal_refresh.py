"""Pedal-only replacement must not change missing evidence or inherited channels."""
import copy
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from acc_telemetry.application.pedal_refresh import replace_pedals, refresh_pedals
from acc_telemetry.domain.observations import FieldObservation
from acc_telemetry.domain.telemetry import QualityFlag as Q


class TestPedalRefresh(unittest.TestCase):
    def rows(self, quality='observed', value=94.):
        sample = dict(sample=dict(throttle_pct=value, brake_pct=value, speed_kmh=None,
                      source_values=dict(throttle=value, brake=value, speed_raw='bad'),
                      field_quality=dict(throttle_pct=quality, brake_pct=quality),
                      field_reasons=dict(throttle_pct=['unverified'], brake_pct=['unverified'])))
        obs = dict(observations={f:dict(value=value, raw_value=value, quality=quality,
                                       reasons=['unverified'], last_observed_time_s=0)
                                 for f in ('throttle_pct', 'brake_pct')})
        readings = {f:FieldObservation(100., Q.OBSERVED, 100., (), 0) for f in ('throttle', 'brake')}
        return sample, obs, readings

    def test_changes_only_values_and_preserves_source_inputs(self):
        s, o, r = self.rows()
        before = copy.deepcopy((s, o))
        a, b = replace_pedals(s, o, r)
        self.assertEqual((s, o), before)
        self.assertIsNone(a['sample']['speed_kmh'])
        self.assertEqual(a['sample']['source_values']['speed_raw'], 'bad')
        self.assertEqual(a['sample']['throttle_pct'], 100)
        self.assertEqual(b['observations']['brake_pct']['raw_value'], 100)
        self.assertEqual(a['sample']['field_reasons'], s['sample']['field_reasons'])
        self.assertEqual(b['observations']['throttle_pct']['reasons'], ['unverified'])

    def test_prior_null_or_nonfresh_remains_untouched(self):
        for quality, value in [('missing', None), ('held', 94.), ('interpolated', 70.)]:
            s, o, r = self.rows(quality, value)
            self.assertEqual(replace_pedals(s, o, r), (s, o))

    def test_new_missing_or_invalid_read_aborts(self):
        for value in (None, float('nan'), 101, -1):
            s, o, r = self.rows()
            r['throttle'] = FieldObservation(value, Q.MISSING if value is None else Q.OBSERVED, value)
            with self.assertRaises(ValueError):
                replace_pedals(s, o, r)

    def test_different_prior_normalization_aborts(self):
        s, o, r = self.rows()
        s['sample']['throttle_pct'] = 50
        with self.assertRaises(ValueError):
            replace_pedals(s, o, r)

    def test_unsupported_parent_is_rejected_before_decoding(self):
        loaded = SimpleNamespace(manifest={'profile': 'other'})
        with patch('acc_telemetry.application.pedal_refresh.read_session_artifacts', return_value=loaded), \
                patch('acc_telemetry.application.pedal_refresh.cv2.VideoCapture') as decoder:
            with self.assertRaises(ValueError):
                refresh_pedals('source', 'destination')
            decoder.assert_not_called()

    def test_incomplete_decode_leaves_no_published_or_staging_output(self):
        import tempfile
        from pathlib import Path
        from acc_telemetry.application.config import load_settings
        from acc_telemetry.application.session_artifacts import _plain, source_identity
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/'source.mov'; source.write_bytes(b'mocked decoder input')
            parent = root/'parent'; parent.mkdir()
            (parent/'manifest.json').write_text('{}')
            for name in ('samples.jsonl', 'observations.jsonl'):
                (parent/name).write_text('')
            (parent/'telemetry.csv').write_text('frame,brake,throttle\n')
            manifest = dict(profile='ps5_full_map_1080p', code={}, files={},
                            source=source_identity(source), clip_origin={'start_s': 0}, timebase={'status': 'pass'},
                            config=dict(measurement_mode='automatic', settings=_plain(load_settings())))
            loaded = SimpleNamespace(manifest=manifest, samples=[SimpleNamespace(frame=0, time_s=0)])
            decoder = Mock(); decoder.read.return_value = (False, None)
            with patch('acc_telemetry.application.pedal_refresh.read_session_artifacts', return_value=loaded), \
                    patch('acc_telemetry.application.pedal_refresh.probe_supported_capture', return_value={'presentation_frames': 1}), \
                    patch('acc_telemetry.application.pedal_refresh.cv2.VideoCapture', return_value=decoder):
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    refresh_pedals(parent, root/'processed'/'out')
            self.assertEqual(list((root/'processed').iterdir()), [])
            decoder.release.assert_called_once()
