# PS5 Telemetry Calibration Implementation Plan


**Goal:** Make full-map ACC PS5 recordings produce stable speed and 0-100% track-position telemetry.

**Architecture:** Add an isolated PS5 profile whose map thresholds and sampling count are passed into the existing tracker. Keep OCR and position behavior in their current classes, but correct speed page segmentation, lap-start anchoring, contour direction, and monotonic filtering. Verify unit behavior first and then run the supplied PS5 video as an integration test.

**Tech Stack:** Python 3.13, unittest, OpenCV, NumPy, tesserocr, PyYAML

---

### Task 1: Add the PS5 full-map profile

**Files:**
- Create: `tests/test_ps5_profile.py`
- Modify: `config/roi_config.yaml`

- [ ] **Step 1: Write the failing profile test**

```python
import unittest
from pathlib import Path

import yaml


class TestPS5Profile(unittest.TestCase):
    def test_full_map_profile_has_confirmed_detection_settings(self):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open() as config_file:
            profile = yaml.safe_load(config_file)["ps5_full_map_720p"]

        self.assertEqual(profile["track_map"], {
            "x": 3,
            "y": 215,
            "width": 269,
            "height": 183,
        })
        self.assertEqual(profile["position_tracking"]["white_lower"], [0, 0, 150])
        self.assertEqual(profile["position_tracking"]["white_upper"], [180, 100, 255])
        self.assertEqual(profile["position_tracking"]["sample_count"], 60)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `venv/bin/python -m unittest tests.test_ps5_profile -v`

Expected: `ERROR` with `KeyError: 'ps5_full_map_720p'`.

- [ ] **Step 3: Add the complete profile**

Append this profile to `config/roi_config.yaml`:

```yaml
ps5_full_map_720p:
  throttle:
    x: 1172
    y: 670
    width: 102
    height: 14
  brake:
    x: 1172
    y: 683
    width: 102
    height: 12
  steering:
    x: 1135
    y: 662
    width: 134
    height: 9
  lap_number:
    x: 237
    y: 71
    width: 47
    height: 37
  lap_number_training:
    x: 181
    y: 71
    width: 47
    height: 37
  last_lap_time:
    x: 119
    y: 87
    width: 87
    height: 20
  speed:
    x: 1177
    y: 621
    width: 54
    height: 32
  gear:
    x: 1124
    y: 591
    width: 47
    height: 72
  track_map:
    x: 3
    y: 215
    width: 269
    height: 183
  position_tracking:
    white_lower: [0, 0, 150]
    white_upper: [180, 100, 255]
    sample_count: 60
```

- [ ] **Step 4: Run the profile test and confirm GREEN**

Run: `venv/bin/python -m unittest tests.test_ps5_profile -v`

Expected: one passing test.

- [ ] **Step 5: Commit the profile**

```bash
git add config/roi_config.yaml tests/test_ps5_profile.py
git commit -m "feat: add PS5 full-map telemetry profile"
```

### Task 2: Correct speed OCR segmentation

**Files:**
- Create: `tests/test_speed_ocr_mode.py`
- Modify: `src/lap_detector.py`

- [ ] **Step 1: Write the failing OCR-mode test**

```python
import unittest

import numpy as np
import tesserocr

from src.lap_detector import LapDetector


class FakeTesseractAPI:
    def __init__(self):
        self.page_modes = []

    def SetPageSegMode(self, mode):
        self.page_modes.append(mode)

    def SetImage(self, image):
        self.image = image

    def GetUTF8Text(self):
        return "171"


class TestSpeedOCRMode(unittest.TestCase):
    def test_speed_uses_single_line_and_restores_single_word(self):
        detector = LapDetector.__new__(LapDetector)
        detector.speed_roi = {"x": 0, "y": 0, "width": 54, "height": 32}
        detector._tesserocr_api = FakeTesseractAPI()
        detector._speed_history = []
        detector._history_size = 15
        detector._last_valid_speed = None

        speed = detector.extract_speed(np.zeros((32, 54, 3), dtype=np.uint8))

        self.assertEqual(speed, 171)
        self.assertEqual(detector._tesserocr_api.page_modes, [
            tesserocr.PSM.SINGLE_LINE,
            tesserocr.PSM.SINGLE_WORD,
        ])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `TESSDATA_PREFIX="$PWD/tessdata" venv/bin/python -m unittest tests.test_speed_ocr_mode -v`

Expected: failure because `page_modes` is empty.

- [ ] **Step 3: Apply the minimal OCR fix**

Replace the tesserocr branch inside `LapDetector.extract_speed()` with:

```python
if self._tesserocr_api:
    self._tesserocr_api.SetPageSegMode(tesserocr.PSM.SINGLE_LINE)
    try:
        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(roi_rgb)
        self._tesserocr_api.SetImage(pil_image)
        text = self._tesserocr_api.GetUTF8Text()
    finally:
        self._tesserocr_api.SetPageSegMode(tesserocr.PSM.SINGLE_WORD)
```

- [ ] **Step 4: Run the OCR test and confirm GREEN**

Run: `TESSDATA_PREFIX="$PWD/tessdata" venv/bin/python -m unittest tests.test_speed_ocr_mode -v`

Expected: one passing test.

- [ ] **Step 5: Verify the known PS5 frames**

Run the diagnostic against frames 65, 70, 75, 85, 370, and 390 of `videos/acc-ps5-spa-lap-720p.mp4`.

Expected raw values: `171`, `172`, `174`, `178`, `82`, `98`.

- [ ] **Step 6: Commit the OCR fix**

```bash
git add src/lap_detector.py tests/test_speed_ocr_mode.py
git commit -m "fix: read ACC speed as a digit line"
```

### Task 3: Sample the full recording for map extraction

**Files:**
- Create: `tests/test_video_sampling.py`
- Modify: `src/video_processor.py`
- Modify: `main.py`
- Modify: `src/web/services/processing.py`

- [ ] **Step 1: Write failing tests for evenly spaced indices**

```python
import unittest

from src.video_processor import evenly_spaced_frame_indices


class TestVideoSampling(unittest.TestCase):
    def test_samples_entire_recording(self):
        self.assertEqual(evenly_spaced_frame_indices(100, 5), [0, 24, 49, 74, 99])

    def test_does_not_duplicate_when_request_exceeds_frames(self):
        self.assertEqual(evenly_spaced_frame_indices(3, 60), [0, 1, 2])

    def test_empty_video_has_no_samples(self):
        self.assertEqual(evenly_spaced_frame_indices(0, 60), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `venv/bin/python -m unittest tests.test_video_sampling -v`

Expected: import error because `evenly_spaced_frame_indices` does not exist.

- [ ] **Step 3: Implement the pure sampling helper**

Add to `src/video_processor.py`:

```python
def evenly_spaced_frame_indices(frame_count: int, sample_count: int) -> list[int]:
    if frame_count <= 0 or sample_count <= 0:
        return []

    actual_count = min(frame_count, sample_count)
    return np.linspace(0, frame_count - 1, actual_count, dtype=int).tolist()
```

- [ ] **Step 4: Run the sampling tests and confirm GREEN**

Run: `venv/bin/python -m unittest tests.test_video_sampling -v`

Expected: three passing tests.

- [ ] **Step 5: Wire profile settings into both processors**

In `main.py`, replace the existing video-processor import with:

```python
from src.video_processor import VideoProcessor, evenly_spaced_frame_indices
```

In `src/web/services/processing.py`, replace the existing video-processor import with:

```python
from src.video_processor import VideoProcessor, evenly_spaced_frame_indices
```

In both files, construct the tracker with the profile bounds and replace the fixed sample list:

```python
position_config = roi_config.get("position_tracking", {})
position_tracker = PositionTrackerV2(
    white_lower=position_config.get("white_lower"),
    white_upper=position_config.get("white_upper"),
)

sample_count = int(position_config.get("sample_count", 11))
sample_frames = evenly_spaced_frame_indices(video_info["frame_count"], sample_count)
```

Existing profiles therefore keep 11 samples and default thresholds; the PS5 profile uses 60.

- [ ] **Step 6: Run import and sampling checks**

Run: `venv/bin/python -m compileall -q main.py src && venv/bin/python -m unittest tests.test_video_sampling -v`

Expected: compilation succeeds and all sampling tests pass.

- [ ] **Step 7: Commit sampling support**

```bash
git add src/video_processor.py main.py src/web/services/processing.py tests/test_video_sampling.py
git commit -m "fix: sample full videos for map extraction"
```

### Task 4: Anchor and stabilize track position

**Files:**
- Modify: `src/position_tracker_v2.py`
- Modify: `tests/test_position_tracker_v2.py`
- Modify: `tests/test_position_smoothing.py`

- [ ] **Step 1: Add failing constructor and direction tests**

Add these tests to `tests/test_position_tracker_v2.py`:

```python
from unittest.mock import patch

def test_custom_white_bounds(self):
    tracker = PositionTrackerV2(
        white_lower=[0, 0, 150],
        white_upper=[180, 100, 255],
    )
    np.testing.assert_array_equal(tracker.white_lower, [0, 0, 150])
    np.testing.assert_array_equal(tracker.white_upper, [180, 100, 255])

def test_direction_uses_small_forward_distance(self):
    self.tracker.total_track_length = 100.0
    self.tracker.start_idx = 10
    self.tracker.start_position = (10, 0)
    self.tracker.travel_direction = None

    with patch.object(self.tracker, "_calculate_path_distance", return_value=2.0):
        forward = self.tracker._position_from_closest_index(12)
    self.assertAlmostEqual(forward, 2.0)
    self.assertEqual(self.tracker.travel_direction, 1)

    self.tracker.travel_direction = None
    with patch.object(self.tracker, "_calculate_path_distance", return_value=98.0):
        reverse = self.tracker._position_from_closest_index(8)
    self.assertAlmostEqual(reverse, 2.0)
    self.assertEqual(self.tracker.travel_direction, -1)
```

- [ ] **Step 2: Run position tests and confirm RED**

Run: `venv/bin/python -m unittest tests.test_position_tracker_v2 tests.test_position_smoothing -v`

Expected: failures for constructor arguments, missing direction helper, reset behavior, smoothing, and spike removal.

- [ ] **Step 3: Accept configurable white bounds**

Change the constructor signature and white-bound initialization:

```python
def __init__(
    self,
    fps: float = 30.0,
    max_jump_per_frame: float = 1.0,
    white_lower: Optional[List[int]] = None,
    white_upper: Optional[List[int]] = None,
):
    self.travel_direction: Optional[int] = None
    self.white_lower = np.array(white_lower or [0, 0, 210])
    self.white_upper = np.array(white_upper or [180, 30, 255])
```

- [ ] **Step 4: Add contour-direction calculation**

Add this helper and call it from `calculate_position()` after finding `closest_idx`:

```python
def _position_from_closest_index(self, closest_idx: int) -> float:
    if self.total_track_length <= 0:
        return 0.0

    forward_distance = self._calculate_path_distance(self.start_idx, closest_idx)
    forward_position = (forward_distance / self.total_track_length) * 100.0
    reverse_position = 0.0 if forward_position == 0.0 else 100.0 - forward_position

    if self.travel_direction is None:
        smallest_movement = min(forward_position, reverse_position)
        if 0.02 < smallest_movement <= 5.0:
            self.travel_direction = 1 if forward_position <= reverse_position else -1
        else:
            return 0.0

    return forward_position if self.travel_direction == 1 else reverse_position
```

Replace the manual arc-length block in `calculate_position()` with:

```python
position = self._position_from_closest_index(closest_idx)
```

- [ ] **Step 5: Always anchor zero from the lap transition**

Replace `reset_for_new_lap()` with:

```python
def reset_for_new_lap(self) -> None:
    self.last_position = 0.0
    self.travel_direction = None
    self.lap_just_started = True
    print("      🏁 Lap reset triggered - will capture start position on next frame")
```

The existing first-frame branch in `extract_position()` already records the red dot and nearest `start_idx`.

- [ ] **Step 6: Restore monotonic validation**

Replace `_validate_position()` with:

```python
def _validate_position(self, raw_position: Optional[float]) -> float:
    if raw_position is None:
        return self.last_position

    if self.last_position > 95.0 and raw_position < 5.0:
        self.last_position = raw_position
        return raw_position

    if raw_position < self.last_position:
        return self.last_position

    jump = raw_position - self.last_position
    if jump > self.max_jump_per_frame:
        result = self.last_position + self.max_jump_per_frame
    else:
        result = 0.3 * raw_position + 0.7 * self.last_position
        if raw_position - result > 0.5:
            result = raw_position - 0.2

    self.last_position = result
    return result
```

- [ ] **Step 7: Restore spike removal required by the existing test**

Add a private `_remove_path_spikes()` helper that removes a loop when the ordered contour returns within one pixel of a point visited more than `window` positions earlier:

```python
def _remove_path_spikes(
    self,
    path: List[Tuple[int, int]],
    window: int = 5,
    angle_threshold: float = 60.0,
) -> List[Tuple[int, int]]:
    del angle_threshold
    cleaned = []
    index = 0

    while index < len(path):
        cleaned.append(path[index])
        reconnect_at = None
        for candidate in range(len(path) - 1, index + window, -1):
            dx = path[candidate][0] - path[index][0]
            dy = path[candidate][1] - path[index][1]
            if dx * dx + dy * dy <= 1:
                reconnect_at = candidate
                break

        index = reconnect_at + 1 if reconnect_at is not None else index + 1

    return cleaned
```

- [ ] **Step 8: Run all position tests and confirm GREEN**

Run: `venv/bin/python -m unittest tests.test_position_tracker_v2 tests.test_position_smoothing -v`

Expected: all position tests pass.

- [ ] **Step 9: Commit position stabilization**

```bash
git add src/position_tracker_v2.py tests/test_position_tracker_v2.py tests/test_position_smoothing.py
git commit -m "fix: anchor and stabilize minimap position"
```

### Task 5: Run the complete verification and PS5 integration test

**Files:**
- Verify: all Python source and tests
- Generate: `data/output/telemetry_*.csv`
- Generate: `data/output/telemetry_interactive_*.html`

- [ ] **Step 1: Run dependency, compilation, and unit checks**

```bash
venv/bin/python -m pip check
venv/bin/python -m compileall -q main.py src tests
TESSDATA_PREFIX="$PWD/tessdata" venv/bin/python -m unittest discover -s tests -v
```

Expected: no broken requirements, compilation exit 0, and all tests pass.

- [ ] **Step 2: Convert the full-map PS5 recording**

```bash
ffmpeg -hide_banner -loglevel error \
  -i "/Users/loiclang/Downloads/1a0545129bc45-master_playlist.MP4" \
  -vf "scale=1280:720:flags=lanczos,fps=30000/1001" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -an \
  -movflags +faststart videos/acc-ps5-full-map-720p.mp4 -y
```

Expected: H.264, 1280x720, 29.97 FPS output contained inside the working directory.

- [ ] **Step 3: Run `main.py` with the PS5 profile**

The current isolated working directory contains two earlier test videos. The converted full-map video is therefore selection 3, and the appended PS5 profile is selection 3. Run:

```bash
printf '3\n3\n' | \
  env BROWSER=true TESSDATA_PREFIX="$PWD/tessdata" venv/bin/python main.py
```

Expected: successful map extraction with at least 300 path points and a generated CSV/HTML pair.

- [ ] **Step 4: Validate the resulting lap data**

Use the bundled workspace Python with pandas to assert:

```python
assert complete_lap["track_position"].notna().all()
assert complete_lap["track_position"].iloc[0] <= 1.0
assert complete_lap["track_position"].max() >= 95.0
assert (complete_lap["track_position"].diff().dropna() >= -0.01).all()
assert complete_lap["speed"].between(0, 320).all()
assert complete_lap["speed"].diff().abs().max() <= 20
```

Also reconcile the detected lap duration with the ACC HUD value.

- [ ] **Step 5: Copy verified deliverables to the conversation output folder**

Copy the verified CSV and interactive HTML to:

```text
/Users/loiclang/Documents/Codex/2026-08-30/referenced-chatgpt-conversation-this-is-an/outputs/
```

Use descriptive filenames containing `acc-ps5-full-map`.

- [ ] **Step 6: Inspect final repository state**

Run: `git status --short && git log -5 --oneline`

Expected: only known ignored runtime artifacts and the pre-existing local `tessdata/` and `work_frames/` directories remain untracked; implementation commits are present.
