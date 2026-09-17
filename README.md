# ACC Telemetry — PS5 video research handoff

**Community handoff · 17 September 2026.** This repository preserves the work on
extracting driving observations from Assetto Corsa Competizione gameplay video.
The original maintainer is moving to a separate PC-based project using directly
available telemetry. Further video/model development here is paused; this snapshot
is available for anyone interested in studying or continuing the approach.

The PC successor is **not implemented in this repository**. This is a video extraction
and analysis prototype, not a validated coaching product or a metric trajectory tracker.

## What is included

- Native **1920x1080 at exactly 60 fps CFR** input validation and frame/time provenance.
- Fresh HUD speed, brake/throttle, gear and lap-counter observations, with missing
  values, field quality and reasons preserved.
- Calibrated native pedal geometry and rejection of disconnected HUD text fragments.
- Brake/throttle episodes: candidate/confirmation times, truncations, gaps, observed
  peaks, temporal descriptors, resumption relations and candidate overlaps.
- Versioned `telemetry-v2` artifacts, annotations/validation tools, tests and an
  inherited local web viewer.
- Estimated normalized progress (`s` in 0–1), with explicit limits.

Physical steering angle, metric lateral position/trajectory, vehicle dynamics,
TC/ABS interventions and reliable automatic coaching are **not supplied**.
See [capability audit](docs/video-data-audit.md), [pedal/episode contract](docs/control-episodes.md)
and [spatial feasibility results](docs/spatial-feasibility.md).

## Start without a private recording

Use Python 3.12+; the handoff was checked locally with Python 3.13.2.

```bash
python3 -m venv .venv
source .venv/bin/activate
PYTHONPATH=src python scripts/demo_control_episodes.py
```

The demo uses entirely synthetic controls and only the Python standard library; it
requires no video or OCR. The test suite
uses small fixtures/mocked or generated inputs; personal research captures are not needed.
The `PYTHONPATH=src` prefix is for a POSIX shell. In PowerShell set
`$env:PYTHONPATH = 'src'` before invoking Python.

For the full test suite and extraction, install FFmpeg/FFprobe and Tesseract first. Examples:

```bash
# macOS
brew install ffmpeg tesseract pkg-config
# Debian/Ubuntu (also supplies headers when tesserocr must be built)
sudo apt-get install ffmpeg tesseract-ocr libtesseract-dev libleptonica-dev pkg-config g++ libgl1
```

Then install the Python dependencies and run the tests:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests
```

Install the system dependencies before Python requirements if building `tesserocr`
from source. Exact package installation depends on the host; no private OCR assets
are included.

## Process your own compatible capture

The `ps5_full_map_1080p` profile describes a specific HUD layout. A matching resolution
alone does not guarantee matching geometry. The native input restriction is intentional:
no upscaling or resampling to bypass it; 59.94 fps is not accepted.

```bash
PYTHONPATH=src python main.py \
  data/sessions/example/raw/session-1080p60.mov \
  --profile ps5_full_map_1080p --measurement-mode automatic \
  --output data/sessions/example/reports \
  --artifact-dir data/sessions/example/processed/session

PYTHONPATH=src python scripts/control_episodes.py \
  data/sessions/example/processed/session \
  data/sessions/example/processed/episodes
```

Use a new output folder each time. `automatic` reads without input review annotations,
while retaining unverified-visibility reasons. The historical default `reviewed` mode
requires reviewed visibility. Neither mode makes its readings ground truth.

[Signal treatment](docs/signal-treatment.md) · [Artifact schema and pedal-only refresh](docs/session-artifacts.md).

## Public code versus local research evidence

**No personal captures, complete telemetry exports, OCR assets or generated research
reports/models are distributed.** References to `data/lab/.../run-024` through `run-034`
in the documentation are historical local experiment identifiers, not downloadable
bundled datasets. Their result summaries and limitations are retained. Reproducing
those exact runs needs the original inputs, which are not part of this release.

The final local control baseline was run-033. Run-034 only trained a tiny experimental
appearance classifier; no production segmentation or metric trajectory model resulted.
Its private labels/checkpoint/scripts are not required to use the published extraction
and episode code. Start with the synthetic demo, tests, and your own compatible capture.

## Continuing this work

1. Read [the handoff](docs/current-status.md) and [contribution guide](CONTRIBUTING.md).
2. Use [the frozen roadmap](docs/plans/video-to-agent-platform.md) as context, not an
   instruction to restart paused experiments automatically.
3. Preserve raw inputs, missing values, configuration and source/field provenance.
4. Choose a bounded capability, reproduce its limitation, and validate it on separate
   evidence. Existing per-frame checks do not certify all driving episodes.

Architecture: `capture → extraction → normalization → domain → analysis → visualization`.
Run `./scripts/docs-list` to discover the technical documentation
(or `python scripts/docs_list.py` in PowerShell).

## Origin and licensing status

This work builds on [KubaC701/acc-telemetry](https://github.com/KubaC701/acc-telemetry).
The Git history retains the original and subsequent contributions. No project license
was found in the inherited repository; no replacement license has been invented here.
See [NOTICE.md](NOTICE.md) before planning reuse or redistribution. Dependency licenses
remain those of their respective projects.
