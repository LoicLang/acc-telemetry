"""Only native 1920x1080 / exactly 60 fps enters video extraction."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import cv2
from acc_telemetry.extraction.video import VideoProcessor


class TestCaptureFormat(unittest.TestCase):
    def capture(self, width, height, fps):
        cap = Mock()
        cap.isOpened.return_value = True
        cap.get.side_effect = lambda key: {
            cv2.CAP_PROP_FRAME_WIDTH: width, cv2.CAP_PROP_FRAME_HEIGHT: height,
            cv2.CAP_PROP_FPS: fps, cv2.CAP_PROP_FRAME_COUNT: 3}.get(key, 0)
        cap.read.side_effect = AssertionError('no frame may be read during format admission')
        return cap

    def test_unsupported_dimensions_and_rates_rejected_before_frames(self):
        for width, height, fps in ((1280,720,60), (3840,2160,60), (1080,1920,60),
                                   (1920,1080,30), (1920,1080,60000/1001), (1920,1080,float('nan'))):
            with self.subTest(format=(width,height,fps)):
                cap = self.capture(width,height,fps)
                with patch('acc_telemetry.extraction.video.cv2.VideoCapture', return_value=cap), \
                     patch('acc_telemetry.extraction.video.subprocess.run') as probe:
                    with self.assertRaisesRegex(ValueError, '1920x1080.*60'):
                        VideoProcessor('source.mov', {}).open_video()
                cap.read.assert_not_called()
                cap.release.assert_called_once()
                probe.assert_not_called()

    def test_supported_format_checks_packet_cadence_without_decoding(self):
        cap = self.capture(1920,1080,60)
        stream = {'streams': [dict(width=1920,height=1080,avg_frame_rate='60/1',time_base='1/60000')]}
        packets = {'packets': [dict(pts_time=str(t),flags='_') for t in (0,.016667,.033333)]}
        responses = [SimpleNamespace(stdout=json.dumps(x),stderr='') for x in (stream,packets)]
        with patch('acc_telemetry.extraction.video.cv2.VideoCapture', return_value=cap), \
             patch('acc_telemetry.extraction.video.subprocess.run', side_effect=responses) as probe:
            self.assertTrue(VideoProcessor('source.mov', {}).open_video())
        self.assertEqual(probe.call_count, 2)
        cap.read.assert_not_called()

    def test_variable_or_unverifiable_timebase_refused_despite_60fps_header(self):
        for times in ((0,.016667,.05), (0,0,.016667)):
            cap = self.capture(1920,1080,60)
            raw = {'streams':[dict(width=1920,height=1080,avg_frame_rate='60/1',time_base='1/60000')]}
            packets = {'packets':[dict(pts_time=str(t),flags='_') for t in times]}
            with patch('acc_telemetry.extraction.video.cv2.VideoCapture', return_value=cap), \
                 patch('acc_telemetry.extraction.video.subprocess.run', side_effect=[
                     SimpleNamespace(stdout=json.dumps(x),stderr='') for x in (raw,packets)]):
                with self.assertRaises(ValueError):
                    VideoProcessor('source.mov', {}).open_video()
            cap.read.assert_not_called()
            cap.release.assert_called_once()
