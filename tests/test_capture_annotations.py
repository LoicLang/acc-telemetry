"""Independent annotation inputs: never use predictions as ground truth."""
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def capture():
    return dict(status='pass', fps=10., frame_count=3, width=32, height=32,
                timestamps=[0., .1, .2], duration=.3)


def labels():
    return dict(schema_version='capture-annotations-v1', source_sha256='a'*64,
        role='development', annotator='reviewer', reviewed=True, frames=[], passages=[],
        windows=[], visibility=[])


class TestCaptureAnnotations(unittest.TestCase):
    def setUp(self):
        self.validation = importlib.import_module('acc_telemetry.analysis.validation')

    def test_empty_ground_truth_is_not_evaluated(self):
        result = self.validation.validate_annotations(labels(), capture(), source_sha256='a'*64)
        self.assertEqual(result['status'], 'not_evaluated')
        self.assertIsNone(result['error'])

    def test_unreviewed_outside_and_reversed_annotations_are_refused(self):
        invalid = [dict(reviewed=False), dict(source_sha256='b'*64),
                   dict(windows=[dict(frame_lo=2,frame_hi=1)]),
                   dict(passages=[dict(id='p',kind='landmark',frame_lo=0,frame_hi=3,reviewed=True)])]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validation.validate_annotations(dict(labels(), **changes), capture(), source_sha256='a'*64)

    def test_frame_time_and_nonfinite_pedal_annotation_are_refused(self):
        row = dict(frame=1,time_s=.1,speed_text='100',gear_text='3',lap_text='1',
            throttle_pct=0.,brake_pct=20.,pedal_tolerance_pct=5.,
            visibility=dict(speed=True,gear=True,lap_number=True,throttle=True,brake=True,steering=False),
            degraded=False,reviewed=True)
        for changes in (dict(frame=3),dict(time_s=.2),dict(brake_pct=float('nan')),dict(reviewed=False)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validation.validate_annotations(dict(labels(),frames=[dict(row,**changes)]), capture(), source_sha256='a'*64)
        result = self.validation.validate_annotations(dict(labels(),frames=[row]), capture(), source_sha256='a'*64)
        self.assertEqual(result['readable_frames']['speed'], 1)

    def test_readable_speed_requires_numeric_text_and_visibility(self):
        row=dict(frame=1,time_s=.1,speed_text='',gear_text=None,lap_text=None,
            throttle_pct=None,brake_pct=None,pedal_tolerance_pct=None,
            visibility=dict(speed=True,gear=False,lap_number=False,throttle=False,brake=False,steering=False),
            degraded=False,reviewed=True)
        for text in ('', 'NaN', '?'):
            with self.assertRaises(ValueError):
                self.validation.validate_annotations(dict(labels(),frames=[dict(row,speed_text=text)]),
                    capture(),source_sha256='a'*64)

    def test_visibility_span_cannot_override_reviewed_occlusion(self):
        row=dict(frame=1,time_s=.1,speed_text=None,gear_text=None,lap_text=None,
            throttle_pct=None,brake_pct=None,pedal_tolerance_pct=None,
            visibility={f:False for f in ('speed','gear','lap_number','throttle','brake','steering')},
            degraded=True,reviewed=True)
        annotated=dict(labels(),frames=[row],visibility=[dict(field='throttle',start_s=0,end_s=.2,reviewed=True)])
        with self.assertRaises(ValueError):
            self.validation.validate_annotations(annotated,capture(),source_sha256='a'*64)

    def test_validation_config_rejects_nonfinite_limits(self):
        import yaml
        module = importlib.import_module('acc_telemetry.application.validation_config')
        settings = module.load_validation_settings()
        self.assertEqual(settings.speed_mae_kmh,2)
        self.assertEqual(settings.min_coverage,.95)
        base = yaml.safe_load(Path('config/validation.yaml').read_text())
        for key in ('speed_mae_kmh','event_p95_s','min_coverage','selection_step_s'):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'validation.yaml'
                path.write_text(yaml.safe_dump(dict(base,**{key:float('nan')})))
                with self.assertRaises(ValueError):
                    module.load_validation_settings(path)

    def test_corpus_rejects_same_source_in_development_and_holdout(self):
        settings = importlib.import_module('acc_telemetry.application.validation_config').load_validation_settings()
        entries = [dict(labels(),source_sha256='a'*64,role=role) for role in ('development','holdout')]
        with self.assertRaises(ValueError):
            self.validation.corpus_readiness(entries, settings)

    def test_different_clips_from_same_recording_cannot_cross_roles(self):
        settings=importlib.import_module('acc_telemetry.application.validation_config').load_validation_settings()
        entries=[dict(labels(),source_sha256=letter*64,recording_id='same-parent',role=role)
                 for letter,role in (('a','development'),('b','holdout'))]
        with self.assertRaises(ValueError):
            self.validation.corpus_readiness(entries,settings)


class TestSyntheticAnnotationPreparation(unittest.TestCase):
    def test_two_pass_prepare_preserves_existing_labels_and_exports_every_selected_frame(self):
        import cv2
        import numpy as np
        module = importlib.import_module('acc_telemetry.application.capture_annotations')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            video=root/'synthetic.avi'
            writer=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*'MJPG'),60.,(1920,1080))
            for i in range(6):
                writer.write(np.full((1080,1920,3),i*20,np.uint8))
            writer.release()
            from acc_telemetry.application.validation_config import load_validation_settings
            from dataclasses import replace
            settings=replace(load_validation_settings(), resolutions={'synthetic':(1920,1080)})
            output=root/'processed'/'annotations'
            module.prepare_annotations(video,'synthetic',output,settings=settings)
            label_path=output/'labels.json'
            original=label_path.read_bytes()
            self.assertFalse(json.loads(original)['reviewed'])
            selection=output/'selection.json'
            selection.write_text(json.dumps({'windows':[{'frame_lo':1,'frame_hi':3}]}))
            result=module.prepare_annotations(video,'synthetic',output,settings=settings,selection=selection)
            self.assertEqual(len(list((result/'frames').glob('*.png'))),3)
            self.assertEqual(label_path.read_bytes(),original)
            self.assertEqual(json.loads((result/'labels.json').read_text())['frames'][0]['frame'],1)
            with self.assertRaises(ValueError):
                module.validate_annotation_file(label_path)
            reviewed=json.loads((result/'labels.json').read_text())
            reviewed.update(reviewed=True,annotator='reviewer')
            for row in reviewed['frames']:
                row.update(reviewed=True,degraded=True,
                    visibility={k:(k=='throttle' and row['time_s']<3/60) for k in row['visibility']})
            reviewed['visibility']=[dict(field='throttle',start_s=1/60,end_s=3/60,reviewed=True)]
            (result/'labels.json').write_text(json.dumps(reviewed))
            report=module.validate_annotation_file(result/'labels.json')
            self.assertEqual(report['status'],'pass')
            exported=json.loads((result/'visibility.json').read_text())
            self.assertEqual(exported[0]['reviewer'],'reviewer')
            with self.assertRaises(FileExistsError):
                module.validate_annotation_file(result/'labels.json')
