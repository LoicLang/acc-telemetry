"""Tests for video frame sampling helpers."""

import unittest

from src.video_processor import evenly_spaced_frame_indices


class TestEvenlySpacedFrameIndices(unittest.TestCase):
    def test_samples_full_video_range(self):
        self.assertEqual(
            evenly_spaced_frame_indices(100, 5),
            [0, 24, 49, 74, 99],
        )

    def test_limits_samples_to_available_frames(self):
        self.assertEqual(evenly_spaced_frame_indices(3, 60), [0, 1, 2])

    def test_returns_empty_list_for_empty_video(self):
        self.assertEqual(evenly_spaced_frame_indices(0, 60), [])


if __name__ == "__main__":
    unittest.main()

class TestCapturePreflight(unittest.TestCase):
    def test_bad_resolution_nonmonotonic_pts_and_variable_rate_are_rejected(self):
        from acc_telemetry.extraction import video
        raw=dict(streams=[dict(width=32,height=32,avg_frame_rate='10/1',time_base='1/1000',nb_frames='3')],
                 frames=[{'best_effort_timestamp_time':str(t)} for t in (0,.1,.2)])
        self.assertEqual(video.validate_capture_probe(raw,expected_resolution=(32,32))['status'],'pass')
        with self.assertRaisesRegex(ValueError,'resolution'):
            video.validate_capture_probe(raw,expected_resolution=(64,64))
        for times in ((0,0,.2),(0,.1,.4)):
            invalid=dict(raw,frames=[{'best_effort_timestamp_time':str(t)} for t in times])
            with self.assertRaisesRegex(ValueError,'unsupported_timebase'):
                video.validate_capture_probe(invalid,expected_resolution=(32,32))

    def test_incomplete_decode_cannot_finish_successfully(self):
        from unittest.mock import Mock
        from acc_telemetry.extraction.video import VideoProcessor
        processor=VideoProcessor('synthetic',{})
        processor.cap=Mock()
        processor.cap.read.return_value=(False,None)
        processor.fps=30.
        processor.frame_count=2
        with self.assertRaisesRegex(ValueError,'incomplete_decode'):
            list(processor.process_frames())
        self.assertEqual(processor.decode_status['status'],'fail')

    def test_discarded_coded_packets_are_not_missing_presentation_frames(self):
        from acc_telemetry.extraction.video import validate_capture_probe
        raw=dict(streams=[dict(width=32,height=32,avg_frame_rate='10/1',time_base='1/1000',nb_frames='4')],
            frames=[dict(best_effort_timestamp_time=str(t)) for t in (0,.1,.2)],
            packets=[dict(pts_time=str(t),flags=flag) for t,flag in ((0,'K_'),(.1,'__'),(.2,'__'),(.3,'_D'))])
        self.assertEqual(validate_capture_probe(raw,expected_resolution=(32,32))['frame_count'],3)
        raw['packets'][-1]['flags']='__'
        with self.assertRaisesRegex(ValueError,'incomplete_decode'):
            validate_capture_probe(raw,expected_resolution=(32,32))
