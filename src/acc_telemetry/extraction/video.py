"""
Video processing module for extracting frames and ROI regions from ACC gameplay videos.
"""

import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np
from typing import Generator, Dict, Tuple


def evenly_spaced_frame_indices(frame_count: int, sample_count: int) -> list[int]:
    """Return evenly spaced frame indices spanning the available video."""
    if frame_count <= 0 or sample_count <= 0:
        return []

    actual_count = min(frame_count, sample_count)
    return np.linspace(0, frame_count - 1, actual_count, dtype=int).tolist()


def validate_capture_probe(raw, *, expected_resolution):
    """Require compatible CFR PTS and dimensions; no VFR approximation."""
    try:
        stream = raw['streams'][0]
        width, height = int(stream['width']), int(stream['height'])
        if (width,height) != tuple(expected_resolution):
            raise ValueError('unsupported_resolution')
        fps = float(Fraction(stream['avg_frame_rate']))
        tick = float(Fraction(stream['time_base']))
        times = np.asarray([float(f['best_effort_timestamp_time']) for f in raw['frames']])
        if len(times)<2 or not np.isfinite(times).all() or not math.isfinite(fps) or fps<=0 or tick<=0:
            raise ValueError('unsupported_timebase')
        # FFprobe emits seconds rounded to six decimals, independently of stream ticks.
        rounding_s = 10 ** -6
        if (not np.all(np.diff(times)>0)
                or np.any(np.abs(np.diff(times)-1/fps)>tick+rounding_s)
                or np.max(np.abs((times-times[0])-np.arange(len(times))/fps))>1/fps):
            raise ValueError('unsupported_timebase')
        expected = stream.get('nb_frames')
        if 'packets' in raw:
            presented = sorted(float(p['pts_time']) for p in raw['packets'] if 'D' not in p['flags'])
            expected = len(presented)
            if len(presented)!=len(times) or not np.allclose(presented,times,rtol=0,atol=rounding_s):
                raise ValueError(f'incomplete_decode: {len(presented)} presentation packets, {len(times)} decoded frames')
        if expected not in (None,'N/A') and int(expected)!=len(times):
            raise ValueError(f'incomplete_decode: stream announces {expected}, FFprobe decoded {len(times)}')
        return dict(status='pass',fps=fps,frame_count=len(times),width=width,height=height,
                    duration=len(times)/fps,timestamps=(times-times[0]).tolist(),
                    first_pts_s=float(times[0]),time_base_s=tick,
                    coded_frame_count=stream.get('nb_frames'),
                    discarded_packets=sum('D' in p['flags'] for p in raw.get('packets',[])))
    except (KeyError, IndexError, ZeroDivisionError, TypeError) as error:
        raise ValueError('unsupported_timebase') from error


def presentation_packets(path):
    result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_packets',
        '-show_entries','packet=pts_time,flags','-of','json',str(path)],
        capture_output=True,text=True,check=True)
    if result.stderr.strip():
        raise ValueError('incomplete_decode: packet probe errors')
    return json.loads(result.stdout)['packets']


def preflight_capture(path, *, expected_resolution):
    command=['ffprobe','-v','error','-select_streams','v:0','-show_frames',
        '-show_entries','stream=width,height,avg_frame_rate,time_base,nb_frames:frame=best_effort_timestamp_time',
        '-of','json',str(path)]
    result=subprocess.run(command,capture_output=True,text=True,check=True)
    if result.stderr.strip():
        raise ValueError('incomplete_decode: FFprobe reported errors')
    raw=json.loads(result.stdout)
    raw['packets']=presentation_packets(path)
    try:
        return raw, validate_capture_probe(raw, expected_resolution=expected_resolution)
    except ValueError as error:
        error.raw_probe = raw
        raise


class VideoProcessor:
    """Handles video loading and frame extraction."""
    
    def __init__(self, video_path: str, roi_config: Dict):
        """
        Initialize video processor.
        
        Args:
            video_path: Path to the input video file
            roi_config: Dictionary containing ROI coordinates for throttle, brake, steering
        """
        self.video_path = video_path
        self.roi_config = roi_config
        self.cap = None
        self.fps = None
        self.frame_count = None
        self.decode_status = {'status': 'not_evaluated', 'decoded_frames': 0}
        self.current_frame = None  # Store current frame for lap detector access
        
    def open_video(self) -> bool:
        """
        Open the video file and extract metadata.
        
        Returns:
            True if video opened successfully, False otherwise
        """
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            return False
            
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        return True
    
    def extract_roi(self, frame: np.ndarray, roi_name: str) -> np.ndarray:
        """
        Extract a specific ROI from a frame.
        
        Args:
            frame: Full video frame
            roi_name: Name of ROI (throttle, brake, steering)
            
        Returns:
            Cropped ROI region
        """
        roi = self.roi_config[roi_name]
        x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
        return frame[y:y+h, x:x+w]
    
    def process_frames(self) -> Generator[Tuple[int, float, Dict[str, np.ndarray]], None, None]:
        """
        Generator that yields frame data with ROI regions.
        
        Yields:
            Tuple of (frame_number, timestamp, roi_dict)
            where roi_dict contains {'throttle': roi_img, 'brake': roi_img, 'steering': roi_img, 'track_map': roi_img}
        """
        if self.cap is None:
            raise RuntimeError("Video not opened. Call open_video() first.")
        
        frame_num = 0
        self.decode_status = {'status': 'running', 'decoded_frames': 0}
        
        while True:
            ret, frame = self.cap.read()
            
            if not ret:
                expected=self.frame_count
                if frame_num != expected and Path(self.video_path).is_file():
                    # MOV edit lists may count coded preroll/discard samples in nb_frames.
                    expected=sum('D' not in p['flags'] for p in presentation_packets(self.video_path))
                    self.decode_status['presentation_frames']=expected
                if frame_num != expected:
                    self.decode_status['status'] = 'fail'
                    raise ValueError(f'incomplete_decode: {frame_num}/{self.frame_count} frames')
                self.decode_status['status'] = 'pass'
                break
            
            # Store current frame for lap detector access
            self.current_frame = frame
            
            timestamp = frame_num / self.fps
            
            # Extract all ROIs
            roi_dict = {
                'throttle': self.extract_roi(frame, 'throttle'),
                'brake': self.extract_roi(frame, 'brake'),
                'steering': self.extract_roi(frame, 'steering')
            }
            
            # Add track_map ROI if available in config
            if 'track_map' in self.roi_config:
                roi_dict['track_map'] = self.extract_roi(frame, 'track_map')
            
            self.decode_status['decoded_frames'] = frame_num + 1
            yield frame_num, timestamp, roi_dict
            frame_num += 1
    
    def close(self):
        """Release video capture resources."""
        if self.cap is not None:
            self.cap.release()
    
    def get_video_info(self) -> Dict:
        """
        Get video metadata.
        
        Returns:
            Dictionary with fps, frame_count, duration
        """
        return {
            'fps': self.fps,
            'frame_count': self.frame_count,
            'duration': self.frame_count / self.fps if self.fps else 0,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if self.cap else 0,
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if self.cap else 0
        }
