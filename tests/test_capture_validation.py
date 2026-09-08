"""Independent evidence must not turn missing truth or shared bias into accuracy."""
import unittest
from acc_telemetry.analysis.validation import match_events, field_errors, landmark_dispersion


class CaptureValidationTests(unittest.TestCase):
    def test_empty_truth_is_not_evaluated(self):
        self.assertEqual(field_errors([], [])['status'], 'not_evaluated')
        self.assertEqual(match_events([], [], max_window_s=1)['status'], 'not_evaluated')
        self.assertEqual(landmark_dispersion([])['status'], 'not_evaluated')

    def test_duplicate_missed_and_outside_events_separate(self):
        truth = [dict(id='a', lo_s=1, hi_s=1), dict(id='b', lo_s=3, hi_s=3)]
        predicted = [dict(id='p', time_s=1), dict(id='duplicate', time_s=1.01), dict(id='outside', time_s=6)]
        report = match_events(truth, predicted, max_window_s=.1)
        self.assertEqual(report['matched_count'], 1)
        self.assertEqual(report['missed_ids'], ['b'])
        self.assertEqual(report['duplicate_ids'], ['duplicate'])
        self.assertEqual(report['outside_window_ids'], ['outside'])
        self.assertEqual(report['unmatched_prediction_count'], 2)

    def test_matching_maximizes_cardinality_before_distance(self):
        truth = [dict(id='a', lo_s=0, hi_s=0), dict(id='b', lo_s=.15, hi_s=.15)]
        predicted = [dict(id='p', time_s=.09), dict(id='q', time_s=.24)]
        self.assertEqual(match_events(truth, predicted, max_window_s=.1)['matched_count'], 2)

    def test_error_is_midpoint_and_confirmation_delay_is_separate(self):
        report = match_events([dict(id='a', lo_s=1, hi_s=3)],
            [dict(id='p', time_s=1, confirmed_at_s=3)], max_window_s=2)
        pair = report['matches'][0]
        self.assertEqual(pair['absolute_error_s'], 1)
        self.assertEqual(pair['annotation_half_width_s'], 1)
        self.assertEqual(pair['confirmation_delay_s'], 2)

    def test_identical_landmarks_only_establish_dispersion(self):
        result = landmark_dispersion([dict(id='a', s=.25), dict(id='b', s=.25)])
        self.assertEqual(result['range_s'], 0)
        self.assertEqual(result['metric_accuracy'], 'not_evaluated')
        self.assertNotIn('error_m', result)

    def test_missing_readings_count_in_coverage_not_error(self):
        result = field_errors([10, 20, 30], [12, None, 26])
        self.assertEqual(result['denominator'], 3)
        self.assertEqual(result['measured_count'], 2)
        self.assertEqual(result['mae'], 3)
        self.assertAlmostEqual(result['coverage'], 2/3)

class ArtifactMeasurementTests(unittest.TestCase):
    def test_full_throttle_marker_is_never_five_percent_truth(self):
        from acc_telemetry.application.capture_validation import pedal_truth
        included, excluded = pedal_truth([dict(id='E16', kind='pedal_event',
            event_type='throttle_reaches_full', field='throttle', frame_lo=1, frame_hi=1)], [0,.1])
        self.assertFalse(included)
        self.assertEqual(excluded[0]['id'], 'E16')

    def test_first_visible_brake_needs_threshold_truth(self):
        from acc_telemetry.application.capture_validation import pedal_truth
        included, excluded = pedal_truth([dict(id='x', kind='pedal_event',
            event_type='first_visible_brake', field='brake', frame_lo=1, frame_hi=1)], [0,.1])
        self.assertFalse(included)
        self.assertTrue(excluded)

    def test_crossing_does_not_bridge_missing_or_held_readings(self):
        from acc_telemetry.application.capture_validation import fresh_crossings
        from acc_telemetry.domain.observations import FrameObservation, FieldObservation
        from acc_telemetry.domain.telemetry import QualityFlag as Q
        def row(i,v,q):
            return FrameObservation(i,i*.02,{'brake_pct':FieldObservation(v,q,v)})
        result=fresh_crossings([row(0,0,Q.OBSERVED),row(1,0,Q.HELD),row(2,10,Q.OBSERVED)],
            'brake_pct', threshold=5,max_gap_s=.1)
        self.assertEqual(result, [])
        result=fresh_crossings([row(0,0,Q.OBSERVED),row(1,10,Q.OBSERVED)],
            'brake_pct', threshold=5,max_gap_s=.1)
        self.assertEqual(result[0]['time_s'],.02)

    def test_gate_requires_all_six_checks(self):
        from acc_telemetry.application.capture_validation import gate_report
        report=gate_report({}, {})
        self.assertEqual(report['status'],'not_evaluated')
        self.assertFalse(report['coaching_eligible'])
        self.assertEqual(len(report['checks']),6)

class ValidatorIntegrationTests(unittest.TestCase):
    def make_evidence(self):
        import json
        from test_session_artifacts import TestSessionArtifacts
        fixture=TestSessionArtifacts(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        output=fixture.write()
        root=fixture.root
        source=fixture.before['sha256']
        capture={'source':fixture.before,'profile':'ps5_full_map_720p','capture':{
            'status':'pass','frame_count':1,'duration':.1,'timestamps':[0]}}
        labels={'schema_version':'capture-annotations-v1','source_sha256':source,
            'role':'development','annotator':'reviewer','reviewed':True,'windows':[],
            'frames':[],'passages':[],'visibility':[]}
        (root/'capture.json').write_text(json.dumps(capture))
        (root/'labels.json').write_text(json.dumps(labels))
        return output,root,labels

    def test_real_v2_reader_no_ocr_and_no_empty_truth_success(self):
        from unittest.mock import patch
        from acc_telemetry.application.capture_validation import evaluate_session
        output,root,_=self.make_evidence()
        with patch('subprocess.run',side_effect=AssertionError('must not run OCR or ffprobe')):
            report=evaluate_session(output,root/'labels.json',root/'capture.json')
        self.assertEqual(report['fields']['speed']['accuracy_status'],'not_evaluated')
        self.assertEqual(report['lap_events']['gate_status'],'not_evaluated')
        self.assertEqual(report['fields']['brake']['continuous_coverage']['denominator_frames'],0)
        self.assertFalse(report['coaching_eligible'])

    def test_held_speed_and_point_labels_cannot_become_continuous_coverage(self):
        import json
        from acc_telemetry.application.capture_validation import evaluate_session
        output,root,labels=self.make_evidence()
        labels['frames']=[dict(frame=0,time_s=0,reviewed=True,degraded=False,
            visibility=dict(speed=True,brake=True,throttle=True,gear=False,lap_number=False,steering=False),
            speed_text='100',gear_text=None,lap_text=None,brake_pct=0,throttle_pct=0,pedal_tolerance_pct=5)]
        (root/'labels.json').write_text(json.dumps(labels))
        report=evaluate_session(output,root/'labels.json',root/'capture.json')
        self.assertEqual(report['fields']['speed']['denominator'],1)
        self.assertEqual(report['fields']['speed']['measured_count'],0)
        self.assertEqual(report['fields']['brake']['continuous_coverage']['status'],'not_evaluated')

    def test_landmarks_read_normalized_s_from_v2_domain_sample(self):
        import json
        from acc_telemetry.application.capture_validation import evaluate_session
        output,root,labels=self.make_evidence()
        labels['passages']=[dict(id='p1',kind='landmark',landmark_id='stripe',
            frame_lo=0,frame_hi=0,reviewed=True)]
        (root/'labels.json').write_text(json.dumps(labels))
        report=evaluate_session(output,root/'labels.json',root/'capture.json')
        self.assertEqual(report['landmarks']['stripe']['denominator'],1)
        self.assertEqual(report['landmarks']['stripe']['metric_accuracy'],'not_evaluated')

    def test_visibility_reviewer_is_not_replaced_with_point_annotator(self):
        import json
        from acc_telemetry.application.capture_validation import evaluate_session
        output,root,labels=self.make_evidence()
        labels['visibility']=[dict(field='brake',start_s=0,end_s=.1,reviewed=True,reviewer='agent-reviewer')]
        (root/'labels.json').write_text(json.dumps(labels))
        report=evaluate_session(output,root/'labels.json',root/'capture.json')
        self.assertEqual(report['annotation_review']['visibility'][0]['reviewer'],'agent-reviewer')

    def test_explicit_target_segment_measures_speed_availability_without_invented_visibility(self):
        import json
        from acc_telemetry.application.capture_validation import evaluate_session
        output,root,labels=self.make_evidence()
        labels['evaluation_segments']=[dict(frame_lo=0,frame_hi=0)]
        (root/'labels.json').write_text(json.dumps(labels))
        report=evaluate_session(output,root/'labels.json',root/'capture.json')
        coverage=report['fields']['speed']['continuous_coverage']
        self.assertEqual(coverage['denominator_frames'],1)
        self.assertEqual(coverage['observed_frames'],0)
        self.assertEqual(coverage['reviewed_spans'],[])
        self.assertEqual(coverage['status'],'fail')

    def test_tampered_v2_payload_rejected(self):
        from acc_telemetry.application.capture_validation import evaluate_session
        output,root,_=self.make_evidence()
        (output/'observations.jsonl').write_text('{}\n')
        with self.assertRaisesRegex(ValueError,'integrity'):
            evaluate_session(output,root/'labels.json',root/'capture.json')

    def test_fingerprint_ignores_git_commit_but_detects_module_change(self):
        import json
        from acc_telemetry.application.capture_validation import measurement_fingerprint
        from acc_telemetry.application.validation_config import load_validation_settings
        output,root,_=self.make_evidence()
        manifest=json.loads((output/'manifest.json').read_text());settings=load_validation_settings()
        first=measurement_fingerprint(manifest,settings)
        manifest['code']['git_commit']='documentation-only-commit'
        self.assertEqual(first['sha256'],measurement_fingerprint(manifest,settings)['sha256'])
        manifest['code']['module_sha256']['src/acc_telemetry/application/lap_state.py']='changed'
        changed=measurement_fingerprint(manifest,settings)
        self.assertNotEqual(first['sha256'],changed['sha256'])
        self.assertFalse(changed['compatible_with_current_extractor'])

class MeasurementSafetyTests(unittest.TestCase):
    def test_landmark_range_wraps_the_start_finish_seam(self):
        self.assertAlmostEqual(landmark_dispersion([{'s':.99},{'s':.01}])['range_s'],.02)

    def test_nonfinite_or_duplicate_event_evidence_rejected(self):
        with self.assertRaises(ValueError):
            field_errors([1],[float('nan')])
        with self.assertRaises(ValueError):
            match_events([dict(id='a',lo_s=0,hi_s=0)]*2,[],max_window_s=1)

    def test_gate_cannot_pass_without_compatible_fingerprint(self):
        from acc_telemetry.application.capture_validation import gate_report,CHECKS
        checks={k:dict(status='pass',evidence=['synthetic']) for k in CHECKS}
        self.assertFalse(gate_report(checks,{})['coaching_eligible'])

class EventAvailabilityTests(unittest.TestCase):
    def test_fully_observable_but_missed_event_fails(self):
        from acc_telemetry.application.capture_validation import latency_status
        report=match_events([dict(id='t',lo_s=1,hi_s=1)],[],max_window_s=1)
        self.assertEqual(latency_status(report,observable_truth_count=1,max_error_s=.1),'fail')
        self.assertEqual(latency_status(report,observable_truth_count=0,max_error_s=.1),'not_evaluated')

class LapGateTests(unittest.TestCase):
    def test_known_missed_laps_fail_even_before_exhaustive_review(self):
        from acc_telemetry.application.capture_validation import lap_status
        result=match_events([dict(id='approved',lo_s=1,hi_s=1)],[],max_window_s=1)
        self.assertEqual(lap_status(result,complete_review=False,max_error_s=.1),'fail')
        result=match_events([],[],max_window_s=1)
        self.assertEqual(lap_status(result,complete_review=True,max_error_s=.1),'not_evaluated')
