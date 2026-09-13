"""Evidence admission, bounded times and non-destructive experimental report delivery."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from acc_telemetry.analysis.session_summary import summarize
from acc_telemetry.application.session_artifacts import LoadedSession
from acc_telemetry.application.session_report import render_report, write_report
from acc_telemetry.domain.telemetry import QualityFlag as Q, TelemetrySample


def sample(frame, speed=110, quality=Q.OBSERVED):
    return TelemetrySample(frame, frame / 60, 4, None, None, speed, None, None, None,
        None, None, None, {'speed_kmh': quality},
        field_reasons={'speed_kmh': ('speed_hud_unverified',)})


def fixture():
    samples = tuple(sample(f) for f in range(0, 121, 15))
    manifest = dict(schema_version='telemetry-v2', source={'sha256': 'a'*64,
        'size_bytes': 10, 'path': '/private/source.mov'}, files={'samples.jsonl': 'b'*64},
        clip_origin={'start_s': 10}, video_info={'width': 1920, 'height': 1080},
        timebase={'status': 'pass', 'fps': 60}, lap_transitions=[])
    case = dict(schema_version='session-coaching-case-v1',source_sha256='a'*64,
        source_size_bytes=10,artifact_files=manifest['files'],gate_a='FAIL',coaching_eligible=False,
        review={'date':'2026-09-13','author':'test reviewer','type':'synthetic review',
                'limits':'no actual imagery'},context='Synthetic test case',question='Consistency?',
        exclusions='No continuous pedal metrics',landmarks={'entry':'curb A','exit':'curb B'},
        landmark_limits='Approximate perspective',session_evidence='Synthetic evidence only',
        supporting_evidence={},
        passages=[dict(id=f'P{i+1}',window_frames=[start,start+60],entry=[start,start+15],
            exit=[start+45,start+60],reviewed_frames=list(range(start,start+61,15)),
            max_review_gap_s=.25,outcome='synthetic',comparison_limit='not a clean-lap benchmark')
            for i,start in enumerate([0,60])],
        speed_reviews=[dict(id='S1',frame=0,hud_kmh=110,context='entry',reason='point only')],
        visuals=[dict(id='V1',frames=[0,60],text='synthetic scenes')])
    return LoadedSession(samples, (), manifest),case


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.session,self.case=fixture()

    def summary(self):
        return summarize(self.session.samples,self.session.manifest,self.case)

    def test_interval_arithmetic_and_source_origin(self):
        summary=self.summary()
        self.assertEqual(summary['durations'][0]['range_s'],(.5,1))
        self.assertEqual(summary['speeds'][0]['time_s'],10)
        self.assertEqual(summary['speeds'][0]['admitted_kmh'],110)
        self.assertEqual(summary['speeds'][0]['reasons'],['speed_hud_unverified'])
        text=render_report(self.session,self.case,summary,case_sha256='c',manifest_sha256='m')
        self.assertIn('10.000 s / 0',text)
        self.assertIn('Gate A : FAIL',text)
        self.assertIn('`coaching_eligible=false`',text)
        self.assertNotIn('/private/',text)

    def test_missing_held_anomalous_and_disagreement_are_not_repaired(self):
        for value,quality in [(None,Q.MISSING),(110,Q.HELD),(110,Q.ANOMALOUS),(111,Q.OBSERVED)]:
            with self.subTest(value=value,quality=quality):
                samples=(sample(0,value,quality),*self.session.samples[1:])
                result=summarize(samples,self.session.manifest,self.case)
                self.assertIsNone(result['speeds'][0]['admitted_kmh'])
                self.assertEqual(result['speeds'][0]['extracted_kmh'],value)

    def test_unknown_manual_reading_is_unavailable(self):
        self.case['speed_reviews'][0]['hud_kmh']=None
        self.assertIsNone(self.summary()['speeds'][0]['admitted_kmh'])

    def test_missing_landmark_keeps_duration_unknown_with_reason(self):
        self.case['passages'][0]['exit']=None
        with self.assertRaises(ValueError): self.summary()
        self.case['passages'][0]['exit_missing_reason']='not visible after incident'
        self.assertIsNone(self.summary()['durations'][0]['range_s'])
        text=render_report(self.session,self.case,self.summary(),case_sha256='c',manifest_sha256='m')
        self.assertIn('not visible after incident',text)

    def test_source_mismatch_and_eligibility_escalation_rejected(self):
        for key,value in [('source_sha256','wrong'),('source_size_bytes',11),
                          ('artifact_files',{}),('coaching_eligible',True),('gate_a','PASS')]:
            with self.subTest(key=key):
                case=copy.deepcopy(self.case);case[key]=value
                with self.assertRaises(ValueError):
                    summarize(self.session.samples,self.session.manifest,case)

    def test_review_only_at_endpoints_cannot_admit_interval(self):
        self.case['passages'][0]['reviewed_frames'].remove(30)
        with self.assertRaisesRegex(ValueError,'spacing'): self.summary()

    def test_reversed_unreviewed_and_out_of_bounds_markers_rejected(self):
        for bounds in ([15,0],[0,14],[0,1000]):
            with self.subTest(bounds=bounds):
                self.case['passages'][0]['entry']=bounds
                with self.assertRaises(ValueError): self.summary()

    def test_duplicate_ids_and_nonfinite_values_rejected(self):
        for mutate in [lambda c:c['passages'][1].update(id='P1'),
                       lambda c:c['speed_reviews'][0].update(hud_kmh=float('nan')),
                       lambda c:c['passages'][0].update(max_review_gap_s=float('inf'))]:
            case=copy.deepcopy(self.case);mutate(case)
            with self.assertRaises(ValueError):
                summarize(self.session.samples,self.session.manifest,case)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.session,self.case=fixture()
        self.artifacts=self.root/'session';self.artifacts.mkdir()
        (self.artifacts/'manifest.json').write_text(json.dumps(self.session.manifest))
        self.case['manifest_sha256']=hashlib.sha256((self.artifacts/'manifest.json').read_bytes()).hexdigest()
        self.image=self.root/'review.png';self.image.write_bytes(b'synthetic evidence')
        self.case['frame_evidence']={str(f):dict(path='review.png',sha256=hashlib.sha256(
            self.image.read_bytes()).hexdigest()) for f in range(0,121,15)}
        self.case_path=self.root/'case.json';self.save_case()
        mock=patch('acc_telemetry.application.session_report.read_session_artifacts',return_value=self.session)
        mock.start();self.addCleanup(mock.stop)

    def save_case(self):
        self.case_path.write_text(json.dumps(self.case))

    def write(self,output=None):
        return write_report(self.artifacts,self.case_path,output or self.root/'reports'/'session_coaching.md')

    def test_complete_reproducible_output_and_no_overwrite(self):
        path=self.write()
        second=self.write(self.root/'copy.md')
        self.assertEqual(path.read_bytes(),second.read_bytes())
        self.assertTrue(path.read_text().endswith('\n'))
        with self.assertRaises(FileExistsError):self.write()
        self.assertEqual(list(path.parent.iterdir()),[path])

    def test_raw_source_artifacts_and_symlink_refused(self):
        raw=self.root/'raw';raw.mkdir()
        alias=self.root/'alias';alias.symlink_to(raw,target_is_directory=True)
        for dest in (raw/'report.md',alias/'report.md',self.artifacts/'new.md',Path('/private/source.mov')):
            with self.subTest(dest=dest),self.assertRaises(ValueError):self.write(dest)

    def test_tampered_or_missing_image_evidence_refused_before_output(self):
        self.image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'integrity'):self.write()
        self.assertFalse((self.root/'reports').exists())
        self.case['frame_evidence'].pop('0');self.save_case()
        with self.assertRaisesRegex(ValueError,'cover exactly'):self.write()

    def test_concurrent_publication_keeps_other_file(self):
        import os
        original_link=os.link
        def racing_link(source,target):
            Path(target).write_text('other writer')
            original_link(source,target)
        with patch('acc_telemetry.application.session_report.os.link',side_effect=racing_link):
            with self.assertRaises(FileExistsError):self.write()
        self.assertEqual((self.root/'reports/session_coaching.md').read_text(),'other writer')
        self.assertEqual(len(list((self.root/'reports').iterdir())),1)

    def test_non_cfr_proof_refused(self):
        self.session.manifest['timebase']['status']='fail'
        with self.assertRaisesRegex(ValueError,'CFR'):self.write()

    def test_manifest_changes_rejected(self):
        (self.artifacts/'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'manifest'):self.write()


if __name__=='__main__':
    unittest.main()
