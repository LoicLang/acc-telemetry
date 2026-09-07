"""Consolidation must preserve approved values without inventing unreviewed fields."""
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path

from acc_telemetry.analysis.validation import validate_annotations


class TestAnnotationReviewConsolidation(unittest.TestCase):
    def test_explicit_brake_and_throttle_markers_are_retained(self):
        path = self.approval([self.row])
        document = json.loads(path.read_text())
        document['approved_event_claims'] = [dict(window_id=f'E{i}', source_sha256='a'*64,
            kind=kind, frame=1) for i,kind in enumerate(('brake_onset','brake_release','throttle_reapplication'))]
        path.write_text(json.dumps(document))
        output = self.consolidate([path])
        labels = json.loads((output / ('a'*64) / 'labels.json').read_text())
        self.assertEqual([p['field'] for p in labels['passages']], ['brake','brake','throttle'])
        self.assertEqual(len(labels['passages']), 3)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'frames').mkdir()
        self.image = self.root / 'frames' / '00000001.png'
        self.image.write_bytes(b'synthetic image identity fixture')
        self.capture = dict(status='pass', fps=30., frame_count=3, width=32, height=32,
                            timestamps=[0., 1/30, 2/30], duration=.1)
        (self.root / 'capture.json').write_text(json.dumps(dict(
            source={'sha256': 'a'*64}, profile='synthetic', capture=self.capture)))
        self.row = dict(source_sha256='a'*64, frame=1, time_s=1/30,
            image=str(self.image), image_sha256=hashlib.sha256(self.image.read_bytes()).hexdigest(),
            reviewed=True, reviewer='user', window_id='B1',
            proposed=dict(speed_text='100', gear_text='3', lap_text='1',
                          throttle_pct=0, brake_pct=50, pedal_tolerance_pct=3))

    def approval(self, rows):
        path = self.root / 'approval.json'
        path.write_text(json.dumps(dict(schema_version='scoped-review-approval-v1',
            reviewer='user', approved_readings=rows, approved_event_claims=[],
            approved_visual_followups=[], coaching_eligible=False)))
        return path

    def consolidate(self, paths):
        module = importlib.import_module('acc_telemetry.application.annotation_reviews')
        return module.consolidate_approvals(paths, self.root / 'consolidated')

    def test_partial_review_preserves_unknown_visibility_and_degradation(self):
        output = self.consolidate([self.approval([self.row])])
        index = json.loads((output / 'index.json').read_text())
        document = json.loads((output / index['sources'][0]['labels']).read_text())
        row = document['frames'][0]
        self.assertEqual(row['brake_pct'], 50)
        self.assertIsNone(row['visibility']['steering'])
        self.assertIsNone(row['degraded'])
        self.assertEqual(row['review_scope'], 'provided_fields_only')
        report = validate_annotations(document, self.capture, source_sha256='a'*64)
        self.assertEqual(report['readable_frames']['speed'], 1)
        self.assertEqual(report['degraded_frames'], 0)
        self.assertFalse(index['coaching_eligible'])

    def test_duplicate_approvals_do_not_inflate_frame_counts(self):
        path = self.approval([self.row])
        output = self.consolidate([path, path])
        index = json.loads((output / 'index.json').read_text())
        self.assertEqual(index['approved_unique_frames'], 1)

    def test_unreviewed_or_conflicting_values_are_rejected(self):
        for rows in ([dict(self.row, reviewed=False)],
                     [self.row, dict(self.row, proposed=dict(self.row['proposed'], speed_text='999'))]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.consolidate([self.approval(rows)])

    def test_modified_image_is_rejected_and_original_approval_unchanged(self):
        path = self.approval([self.row])
        before = path.read_bytes()
        self.image.write_bytes(b'changed image')
        with self.assertRaises(ValueError):
            self.consolidate([path])
        self.assertEqual(path.read_bytes(), before)

    def test_lift_and_brake_in_one_window_do_not_count_as_two_windows(self):
        path = self.approval([self.row])
        document = json.loads(path.read_text())
        document['approved_event_claims'] = [dict(window_id='B1', source_sha256='a'*64,
            kind='throttle_release', frame=1)]
        document['approved_visual_followups'] = [dict(window_id='B1', reviewed=True,
            first_visible_brake_frame=2, previous_frame=1)]
        path.write_text(json.dumps(document))
        output = self.consolidate([path])
        report = json.loads((output / ('a'*64) / 'review-report.json').read_text())
        self.assertEqual(report['event_windows'], 1)

    def test_provided_fields_scope_cannot_validate_unknown_numeric_evidence(self):
        from acc_telemetry.analysis.validation import validate_annotations
        document = dict(schema_version='capture-annotations-v1', source_sha256='a'*64,
            role='development', annotator='user', reviewed=True, windows=[], passages=[], visibility=[],
            frames=[dict(frame=1, time_s=1/30, reviewed=True, review_scope='provided_fields_only',
                degraded=None, visibility={k:None for k in ('speed','gear','lap_number','throttle','brake','steering')},
                speed_text='100', gear_text=None, lap_text=None, throttle_pct=None,
                brake_pct=None, pedal_tolerance_pct=None)])
        with self.assertRaises(ValueError):
            validate_annotations(document, self.capture, source_sha256='a'*64)

    def test_explicitly_reviewed_absence_and_holdout_role_are_preserved(self):
        row = dict(self.row,
            proposed={k:None for k in self.row['proposed']},
            proposed_visibility={k:False for k in ('speed','gear','lap_number','throttle','brake','steering')},
            proposed_degraded=True)
        path = self.approval([row])
        document = json.loads(path.read_text())
        document['sources'] = {'a'*64: dict(role='holdout', recording_id='original-recording')}
        path.write_text(json.dumps(document))
        output = self.consolidate([path])
        labels = json.loads((output / ('a'*64) / 'labels.json').read_text())
        report = json.loads((output / ('a'*64) / 'review-report.json').read_text())
        self.assertEqual(labels['role'], 'holdout')
        self.assertEqual(labels['recording_id'], 'original-recording')
        self.assertTrue(labels['frames'][0]['degraded'])
        self.assertEqual(report['degraded_frames'], 1)
        self.assertEqual(report['readable_frames']['speed'], 0)
