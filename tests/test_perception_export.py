"""Source/clock and publication boundaries of the local perception package."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np

from acc_telemetry.application.perception import render_lap_video, frame_sequence, load_event_settings
from acc_telemetry.extraction.video import probe_supported_capture


class TestPerceptionMedia(unittest.TestCase):
    def test_trim_keeps_exact_presented_frame_range_and_cadence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.mp4';target=root/'lap.mp4'
            writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'mp4v'),60,(1920,1080))
            self.assertTrue(writer.isOpened())
            for i in range(12):writer.write(np.full((1080,1920,3),(30+i*12,40,80),np.uint8))
            writer.release()
            render_lap_video(source,target,2,10,60)
            probe=probe_supported_capture(target)
            self.assertEqual(probe['presentation_frames'],8)
            a=cv2.VideoCapture(str(source));b=cv2.VideoCapture(str(target))
            try:
                a.set(cv2.CAP_PROP_POS_FRAMES,2)
                for _ in range(8):
                    ok,original=a.read();good,trimmed=b.read()
                    self.assertTrue(ok and good)
                    self.assertLess(np.abs(original.astype(float).mean((0,1))-trimmed.astype(float).mean((0,1))).max(),5)
                self.assertFalse(b.read()[0])
            finally:a.release();b.release()

    def test_frame_selection_is_native_unique_and_bounded(self):
        self.assertEqual(frame_sequence(49,51,.1,60,19,8785),list(range(2940,3061,6)))
        for args in [(-1,1,.1,60,19,8785),(49,51,0,60,19,8785),(49,51,.001,60,19,8785),(145,150,.1,60,19,8785)]:
            with self.assertRaises(ValueError):frame_sequence(*args)

    def test_detail_window_records_actual_native_bounds(self):
        from acc_telemetry.application.perception import window_frames
        self.assertEqual(window_frames(.021,.119,60,0,10),(2,8))
        with self.assertRaises(ValueError):window_frames(.021,.022,60,0,10)
        with self.assertRaises(ValueError):frame_sequence(.021,.022,.1,60,0,10)

    def test_event_configuration_rejects_unknown_and_invalid_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'settings.yaml'
            for text in ('events: {on_pct: 2, off_pct: 5}','events: {on_pct: 5, surprise: 9}'):
                p.write_text(text)
                with self.assertRaises(ValueError):load_event_settings(p)

class TestPerceptionPublication(unittest.TestCase):
    def fixture(self,root):
        import json
        from types import SimpleNamespace
        from acc_telemetry.application.session_artifacts import source_identity
        from acc_telemetry.application.session_report import sha256
        from test_perception import sample
        source=root/'source.mov';source.write_bytes(b'synthetic source, never decoded')
        session=root/'session';session.mkdir();(session/'samples.jsonl').write_text('fixture')
        (session/'manifest.json').write_text('{}')
        manifest=dict(source=source_identity(source),files={'samples.jsonl':sha256(session/'samples.jsonl')},
            timebase={'status':'pass','fps':60},video_info={'width':1920,'height':1080},
            lap_transitions=[dict(to_lap=4,frame=0,confirmed_at_s=0),dict(to_lap=5,frame=8,confirmed_at_s=8/60)],
            clip_origin={'start_s':0},gate_a='not_evaluated')
        spec=dict(schema_version='perception-zones-v1',source_sha256=manifest['source']['sha256'],
            source_size_bytes=manifest['source']['size_bytes'],lap_number=4,
            review={'author':'fixture','limits':'synthetic'},zones=[dict(id='all',label='all',start_frame=0,end_frame=8)])
        zones=root/'zones.json';zones.write_text(json.dumps(spec))
        return session,zones,SimpleNamespace(manifest=manifest,samples=[sample(i) for i in range(8)])

    def test_existing_and_artifact_destinations_are_rejected(self):
        from acc_telemetry.application.perception import write_perception
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);session,zones,loaded=self.fixture(root)
            (root/'existing').mkdir()
            with patch('acc_telemetry.application.perception.read_session_artifacts',return_value=loaded),patch('acc_telemetry.application.perception.probe_supported_capture') as probe:
                for target in (root/'existing',session/'new-report'):
                    with self.assertRaises((ValueError,FileExistsError)):write_perception(session,zones,target)
                probe.assert_not_called()

    def test_wrong_source_review_is_rejected_before_new_decode(self):
        import json
        from acc_telemetry.application.perception import write_perception
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);session,zones,loaded=self.fixture(root)
            data=json.loads(zones.read_text());data['source_sha256']='a'*64;zones.write_text(json.dumps(data))
            with patch('acc_telemetry.application.perception.read_session_artifacts',return_value=loaded),patch('acc_telemetry.application.perception.probe_supported_capture') as probe:
                with self.assertRaisesRegex(ValueError,'zones do not match'):write_perception(session,zones,root/'output')
                probe.assert_not_called()

    def test_failed_media_render_leaves_no_published_or_staged_package(self):
        from acc_telemetry.application.perception import write_perception
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);session,zones,loaded=self.fixture(root)
            with patch('acc_telemetry.application.perception.read_session_artifacts',return_value=loaded),patch('acc_telemetry.application.perception.probe_supported_capture',return_value={'status':'pass'}),patch('acc_telemetry.application.perception.render_lap_video',side_effect=ValueError('render failed')):
                with self.assertRaisesRegex(ValueError,'render failed'):
                    write_perception(session,zones,root/'output',detail_start_s=0,detail_end_s=.1,
                        sequence_start_s=0,sequence_end_s=.05,sequence_step_s=1/60)
            self.assertFalse((root/'output').exists())
            self.assertEqual(list(root.glob('.perception-*')),[])
            self.assertEqual((root/'source.mov').read_bytes(),b'synthetic source, never decoded')

    def test_viewer_treats_labels_as_data_not_executable_markup(self):
        from acc_telemetry.visualization.perception import render_viewer
        data={k:{} for k in ('lap','zones','summary','samples','detail','event_settings')}
        data['zones']={'label':'</script><script>bad()</script>'}
        text=render_viewer(data)
        self.assertNotIn('</script><script>bad()',text)
        self.assertIn('\\u003c/script>',text)
