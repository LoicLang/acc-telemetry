"""Versioned evidence export, strict reloading and no-clobber publication."""
import importlib
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from acc_telemetry.application.config import load_settings
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.speed_visibility import SpeedVisibilityReview, SpeedVisibilitySpan
from acc_telemetry.domain.observations import FieldObservation
from acc_telemetry.domain.telemetry import QualityFlag as Q
from test_application_pipeline import FakeVideo, FakeLaps, FakeControls, FakeGenericProgress


class TestSessionArtifacts(unittest.TestCase):
    def setUp(self):
        self.artifacts = importlib.import_module('acc_telemetry.application.session_artifacts')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.mov'
        self.source.write_bytes(b'synthetic input, OCR and video mocked')
        self.before = self.artifacts.source_identity(self.source)
        self.speed_review = SpeedVisibilityReview(
            source_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(),
            source_size_bytes=self.source.stat().st_size,
            spans=(SpeedVisibilitySpan(0.0, 1 / 30, 'visible', 'test'),),
        )
        self.video = FakeVideo()
        self.video.video_path = self.source
        laps = FakeLaps()
        laps.observe_speed = Mock(return_value=FieldObservation(100, Q.HELD, '682',
            ('speed_out_of_range',), 0.0))
        laps.observe_gear = Mock(return_value=FieldObservation(None, Q.MISSING, 'R',
            ('unsupported_gear_symbol',)))
        self.result = TelemetryPipeline(video=self.video, controls=FakeControls(),
            laps=laps, progress=FakeGenericProgress(), has_track_map=False,
            settings=load_settings(), speed_visibility=self.speed_review).run()

    def write(self, destination=None):
        with patch.object(self.artifacts, 'probe_timebase', return_value={'status': 'not_evaluated'}):
            return self.artifacts.write_session_artifacts(self.result,
                destination or self.root / 'processed' / 'run-001', source_path=self.source,
                source_before=self.before, profile='ps5_full_map_720p',
                clip_origin={'source_id': 'parent', 'start_s': 10.0})

    def test_roundtrip_preserves_extraction_evidence_separately_from_confirmation(self):
        output = self.write()
        loaded = self.artifacts.read_session_artifacts(output)
        self.assertEqual(len(loaded.samples), 1)
        self.assertEqual(loaded.samples[0], self.result.samples[0])
        self.assertEqual(loaded.observations[0], self.result.observations[0])
        observation = loaded.observations[0].observations['speed_kmh']
        self.assertEqual(observation.quality, Q.HELD)
        self.assertEqual(observation.raw_value, '682')
        self.assertEqual(observation.reasons, ('speed_out_of_range',))
        self.assertIsNone(loaded.samples[0].gear)
        self.assertFalse(loaded.coaching_eligible)
        manifest = json.loads((output / 'manifest.json').read_text())
        self.assertEqual(manifest['schema_version'], 'telemetry-v2')
        self.assertEqual(manifest['source'], self.before)
        envelope = json.loads((output / 'observations.jsonl').read_text())
        self.assertEqual(envelope['source_sha256'], self.before['sha256'])
        self.assertEqual(envelope['source_time_s'], 10.0)
        self.assertEqual(envelope['frame'], 0)
        self.assertIn('config_sha256', manifest)
        self.assertIn('code', manifest)

    def test_unsafe_or_existing_destinations_refused(self):
        existing = self.root / 'existing'
        existing.mkdir()
        for dest in (existing, self.source, self.root / 'raw' / 'run'):
            with self.subTest(dest=dest), self.assertRaises((ValueError, FileExistsError)):
                self.write(dest)
        alias = self.root / 'alias'
        raw = self.root / 'raw'
        raw.mkdir()
        alias.symlink_to(raw, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.write(alias / 'run')
        self.assertEqual(self.artifacts.source_identity(self.source), self.before)

    def test_interruption_leaves_no_final_or_temporary_directory(self):
        dest = self.root / 'processed' / 'run'
        with patch.object(self.artifacts, '_write_jsonl', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.write(dest)
        self.assertFalse(dest.exists())
        self.assertEqual(list(dest.parent.iterdir()), [])

    def test_publish_never_replaces_a_destination_created_during_export(self):
        dest = self.root / 'processed' / 'run'
        publish = self.artifacts._publish
        def concurrent_directory(staging, target):
            target.mkdir()
            publish(staging, target)
        with patch.object(self.artifacts, '_publish', side_effect=concurrent_directory):
            with self.assertRaises(FileExistsError):
                self.write(dest)
        self.assertEqual(list(dest.iterdir()), [])

    def test_unknown_version_tampering_and_changed_source_rejected(self):
        output = self.write()
        manifest_path = output / 'manifest.json'
        original = manifest_path.read_text()
        manifest = json.loads(original)
        manifest['schema_version'] = 'telemetry-v999'
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            self.artifacts.read_session_artifacts(output)
        manifest_path.write_text(original)
        (output / 'samples.jsonl').write_text('{}\n')
        with self.assertRaises(ValueError):
            self.artifacts.read_session_artifacts(output)
        self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.write(self.root / 'second')

    def test_legacy_csv_is_readable_but_not_coaching_eligible(self):
        path = self.root / 'legacy.csv'
        path.write_text('frame,time,speed\n0,0,100\n')
        result = self.artifacts.read_session_artifacts(path, limits=load_settings().normalization)
        self.assertEqual(result.samples[0].speed_kmh, 100)
        self.assertFalse(result.coaching_eligible)
        self.assertEqual(result.observations, ())

    def test_source_hash_ignores_access_time_updates(self):
        import os
        os.utime(self.source, (1, 2))
        self.assertEqual(self.artifacts.source_identity(self.source)['sha256'], self.before['sha256'])

    def test_mutated_legacy_record_cannot_diverge_from_normalized_evidence(self):
        self.result.records[0]['speed'] = 200
        with self.assertRaises(ValueError):
            self.write()

    def test_reader_rejects_misaligned_envelope_even_with_matching_file_hash(self):
        output = self.write()
        path = output / 'samples.jsonl'
        envelope = json.loads(path.read_text())
        envelope['frame'] = 999
        path.write_text(json.dumps(envelope) + '\n')
        manifest_path = output / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['files']['samples.jsonl'] = self.artifacts._sha(path)
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            self.artifacts.read_session_artifacts(output)

    def test_nonfinite_raw_evidence_refused_without_final_output(self):
        self.result.records[0]['speed_raw'] = float('nan')
        with self.assertRaises(ValueError):
            self.write()
        self.assertFalse((self.root / 'processed' / 'run-001').exists())

class TestArtifactTimebase(unittest.TestCase):
    def test_cfr_variable_and_missing_pts_have_distinct_results(self):
        from types import SimpleNamespace
        from acc_telemetry.application.session_artifacts import probe_timebase
        for times, expected in (([0, 1, 2], 'pass'), ([0, 1, 5], 'fail'), ([0, 0, 1], 'fail'),
                                ([0], 'fail')):
            payload = {'streams': [{'time_base': '1/60', 'avg_frame_rate': '60/1'}],
                       'frames': [{'best_effort_timestamp': t} for t in times]}
            with patch('subprocess.run', return_value=SimpleNamespace(
                    stdout=json.dumps(payload), stderr='')):
                self.assertEqual(probe_timebase('fixture')['status'], expected)
        with patch('subprocess.run', side_effect=FileNotFoundError):
            self.assertEqual(probe_timebase('fixture')['status'], 'not_evaluated')

    def test_actual_ffprobe_on_synthetic_cfr_video(self):
        import shutil
        import subprocess
        from acc_telemetry.application.session_artifacts import probe_timebase
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('FFmpeg tools unavailable')
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / 'synthetic.mkv'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                'color=size=32x32:rate=30:duration=0.2', '-c:v', 'ffv1', str(video)], check=True)
            report = probe_timebase(video)
            self.assertEqual(report['status'], 'pass')
            self.assertEqual(report['frame_count'], 6)


class TestArtifactAdapters(unittest.TestCase):
    def test_cli_exports_modern_session_with_explicit_settings(self):
        from acc_telemetry.adapters.cli import main
        from acc_telemetry.application.session_artifacts import read_session_artifacts
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.mov'
            source.write_bytes(b'fake video')
            destination = root / 'processed' / 'session'
            review = root / 'speed-visibility.json'
            review.write_text(json.dumps({
                'schema_version': 'speed-visibility-v1',
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'source_size_bytes': source.stat().st_size,
                'spans': [{'start_s': 0.0, 'end_s': 1 / 30,
                           'state': 'visible', 'reviewer': 'test'}],
            }))
            fake_video = FakeVideo()
            fake_video.video_path = source
            with (patch('acc_telemetry.application.components.VideoProcessor', return_value=fake_video),
                  patch('acc_telemetry.application.components.LapDetector', return_value=FakeLaps()),
                  patch('acc_telemetry.application.components.TelemetryExtractor', return_value=FakeControls()),
                  patch('acc_telemetry.application.components.ProgressSessionEstimator', return_value=FakeGenericProgress()),
                  patch('acc_telemetry.application.pipeline.TelemetryPipeline._extract_track_path'),
                  patch('acc_telemetry.application.session_artifacts.probe_timebase', return_value={'status':'fail'})):
                self.assertEqual(main([str(source), '--output', str(root / 'reports'),
                                       '--artifact-dir', str(destination),
                                       '--speed-visibility-json', str(review)]), 0)
            result = read_session_artifacts(destination)
            self.assertEqual(result.samples[0].speed_kmh, 171)
            self.assertFalse(result.coaching_eligible)
            self.assertEqual(result.manifest['timebase']['status'], 'fail')

class TestWebArtifactAdapter(unittest.IsolatedAsyncioTestCase):
    async def test_web_exports_with_effective_ocr_settings_and_default_visibility(self):
        from dataclasses import replace
        from acc_telemetry.adapters.web.services.processing import VideoProcessingService
        from acc_telemetry.application.session_artifacts import read_session_artifacts
        settings = load_settings()
        settings = replace(settings, ocr=replace(settings.ocr, max_speed_delta_kmh=13))
        laps = FakeLaps()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mov'
            source.write_bytes(b'mocked video')
            destination = root / 'processed' / 'session'
            service = VideoProcessingService()
            with (patch.object(service, 'load_roi_config', return_value={'ps5_full_map_720p': {}}),
                  patch.object(service, '_build_progress_estimator', return_value=FakeGenericProgress()),
                  patch('acc_telemetry.adapters.web.services.processing.VideoProcessor', return_value=FakeVideo()),
                  patch('acc_telemetry.adapters.web.services.processing.TelemetryExtractor', return_value=FakeControls()),
                  patch('acc_telemetry.adapters.web.services.processing.LapDetector', return_value=laps),
                  patch('acc_telemetry.adapters.web.services.processing.load_settings', return_value=settings),
                  patch('acc_telemetry.application.session_artifacts.probe_timebase', return_value={'status':'fail'}),
                  patch.object(service.storage, 'get_video_directory', return_value=root / 'reports'),
                  patch.object(service.storage, 'save_metadata')):
                await service.process_video(str(source), 'session', profile_name='ps5_full_map_720p',
                                            artifact_dir=str(destination))
            result = read_session_artifacts(destination)
            self.assertEqual(laps._max_speed_ocr_delta_kmh, 13)
            self.assertEqual(result.manifest['config']['settings']['ocr']['max_speed_delta_kmh'], 13)
            self.assertEqual(result.manifest['config']['visibility'], [])
            self.assertEqual(result.observations[0].frame, 0)
