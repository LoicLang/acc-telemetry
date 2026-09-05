# PS5 Telemetry Calibration Design

## Goal

Make ACC PS5 recordings with the HUD track map set to `Full` produce reliable speed and track-position telemetry while preserving the existing extraction workflow.

## Confirmed causes

1. Speed OCR uses Tesseract `SINGLE_WORD`, which misreads ACC values such as `171` as `17` and `82` as `682`. The same frames read correctly with `SINGLE_LINE`.
2. The full-map line is semi-transparent. The current HSV range (`S <= 30`, `V >= 210`) retains only 263 pixels from the PS5 recording and fragments the path.
3. The documentation recommends 50 or more map samples, while the CLI and web processor use 11 fixed early frames.
4. Geometric start-line detection selects the upper-right portion of Spa rather than the actual start/finish line.
5. Position validation is currently disabled by a raw-pass-through implementation, although the existing tests expect monotonic filtering and jump control.

## Scope

### Included

- Add a PS5 full-map 720p profile without changing the existing Twitch and Go Setups profiles.
- Make map-detection thresholds configurable per profile.
- Sample 60 frames evenly over the complete recording for map extraction.
- Read speed with Tesseract's single-line mode and restore the shared OCR mode afterward.
- Anchor position zero to the red dot observed immediately after a detected lap transition.
- Determine travel direction from the first forward movement after that transition.
- Restore monotonic position validation and maximum-jump protection.
- Add focused unit tests and verify the result on the supplied PS5 recording.

### Excluded

- Determining whether a lap is valid under ACC sporting rules.
- Supporting the zoomed, scrolling minimap.
- Replacing video telemetry with native PC telemetry.
- General automatic HUD detection for arbitrary layouts.

## Configuration

`config/roi_config.yaml` will gain a `ps5_full_map_720p` profile. Its throttle, brake, steering, lap, speed, gear, and full-map coordinates will match the supplied 1280x720 conversion. A nested `position_tracking` section will contain:

- white HSV lower bound `[0, 0, 150]`;
- white HSV upper bound `[180, 100, 255]`;
- `sample_count: 60`.

The existing profiles retain their present settings and behavior.

## Processing design

### Speed OCR

`LapDetector.extract_speed()` will temporarily set the shared Tesseract API to `PSM.SINGLE_LINE`, perform digit-only recognition, and restore `PSM.SINGLE_WORD` in a `finally` block. This prevents speed-specific settings from leaking into lap-number and gear OCR.

### Map extraction

`PositionTrackerV2` will accept optional white HSV bounds. The PS5 profile will supply the relaxed bounds confirmed by the diagnostic run. The CLI and web processor will replace the fixed frame list with 60 evenly spaced frame indices based on the video's frame count.

### Start anchoring and direction

Geometric start-line detection may remain useful for diagnostics but will not be authoritative after a lap transition. `reset_for_new_lap()` will mark the next valid red-dot observation as the actual zero point. The following meaningful movement will establish whether the contour must be traversed in its stored or reverse direction, choosing the direction that represents the smaller forward movement from zero.

### Position validation

After direction is established, position values will be monotonic within a lap. Small backward detections will hold the last value, implausible forward jumps will be clamped to `max_jump_per_frame`, and the normal 99-to-0 transition will remain allowed when a new lap is detected.

## Tests

1. A speed OCR test will prove that the detector selects single-line mode and restores single-word mode.
2. Existing reset tests will verify that every lap transition captures a fresh red-dot start anchor.
3. Direction tests will cover contours stored in both driving directions.
4. Position validation tests will cover jitter, backward movement, large jumps, and lap wraparound.
5. A profile test will verify the PS5 HSV bounds and 60-sample setting.
6. The supplied full-map PS5 video will provide the final integration check without being committed to the repository.

## Acceptance criteria

- The full Spa path is extracted and validated with at least 300 contour points.
- A complete detected lap starts near 0%, progresses without backward jumps, and reaches at least 95% before the next lap transition.
- Speed values contain no single-frame OCR jumps larger than 20 km/h unless adjacent frames support the change.
- Known sample frames read `171`, `172`, `174`, `178`, `82`, and `98` correctly.
- Lap transitions and the measured lap duration remain correct.
- No user recording or large binary fixture is committed.

