---
summary: exhaustive 1247-frame development speed visibility review and scoped current-code admission results, with unresolved segment and Gate A limits
read_when:
  - assessing continuous speed visibility or run-014 coverage evidence
  - preparing complete calibration-lap visibility after the short-segment review
---

# Continuous speed visibility — 10 September 2026

All **32 frozen development segments / 1,247 frame cells** from the run-011
`reports/speed-continuous-review-dossier.json` were visually reviewed. Every cell
has a readable lower-right speed HUD: **1,247 visible, zero absent, zero unknown**
inside this scope. Outside these segments remains unknown in these standalone files.
This establishes readability, not numerical OCR accuracy or full-lap coverage.

New private evidence is exclusively under ignored
`data/lab/coaching-reliability/run-014/`. BMW review is attributed to
`OpenAI Codex / gpt-6-astra / root`; incidents review to `gpt-5.6-sol`.
Neither is user approval. Existing reviews and approvals remain unchanged.

## Review and source integrity

The reviewers inspected every cell in 39 sequential sheets (18 BMW, 21 incidents)
and all 64 first/last scene contexts (28 BMW, 36 incidents). No OCR outputs supplied
visibility truth. Per-frame identities, timestamps, decisions, reviewer names and
media hashes are in `reports/{bmw,crash}-visual-review.json`.

`reports/integrity-report.json` verifies 1,382 source/media references, their byte
sizes and SHA-256, and all frame intervals. Both sources pass 1920×1080, exactly
60 fps metadata and constant presentation cadence checks separately:

| Source | Source SHA-256 | Bytes | Presented frames |
| --- | --- | ---: | ---: |
| BMW | `76859897055ddbac6bb52f6299dc7b86a6daf36bb3182b8d64d3da6c9aae378d` | 1,119,948,389 | 47,589 |
| Incidents | `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124` | 453,613,415 | 29,402 |

Consumed source-bound reviews are `processed/bmw-speed-visibility.json` and
`processed/crash-speed-visibility-canonical.json`. Intervals are half-open, bounded
by `frame_lo/60` and `(frame_hi+1)/60`; all following frame timestamps are unknown.
The original incidents export computed one end as `frame_hi/60 + 1/60`, one float
ULP above the following timestamp. Strict validation caught that extra admission
at frame 40. The canonical derivative fixes only the bound and keeps Sol's authorship.
The original file, initial diagnostic replay and derivation record
`reports/crash-boundary-canonicalization.json` are preserved.

## Actual scoped measurement

After successful 16-frame BMW and 40-frame incidents smoke checks, the replay decoded
all target frames from the original sources, requiring pixel-identical review crops.
It invoked current `LapDetector.observe_speed`, `SpeedAdmission` and `normalize_row`
with the unchanged 1080p profile, 100 m/s² envelope and 0.25 s maximum gap.
Each reviewed interval resets causal support; no preceding unreviewed speed is inferred.
The measured value remains fresh or null, with raw text and reasons preserved.

This is a **selected-frame speed-path replay**, not a full `TelemetryPipeline` run
or telemetry-v2 artifact validation. Complete sessions were unnecessary to measure
this tranche's scoped admission. Old full-session acceptance fingerprints are not
transferred: the comparison explicitly identifies changed `extraction/video.py`.
No old fingerprints were rewritten. Fresh source decoding supplies the new proof.

| Source | Frames | Visible / absent / unknown | Admitted | Abstentions | Coverage | Frozen run-011 availability |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| BMW | 564 | 564 / 0 / 0 | 564 | 0 | 100% | 39/564 |
| Incidents | 683 | 683 / 0 / 0 | 679 | 4 | 99.4143% | 40/683 |

The scoped gain is **525 BMW and 639 incidents observations**, compared descriptively
with the frozen sparse-review results. Every BMW segment exceeds 95%; incidents
**V-CRASH-15 (20985–21015) is 28/31 = 90.3226%**, below the unchanged target.
The other 17 incidents segments exceed 95%. Aggregates must not hide this failure.

| Incidents frame | Raw OCR | Published | Reason | Pixel review |
| --- | --- | --- | --- | --- |
| 20895 | 698 | null | `speed_out_of_range` | HUD 98 |
| 20988 | 4 | null | `speed_rate_exceeded` | HUD 71 |
| 20992 | 39 | null | `speed_rate_exceeded` | HUD 39, after HUD 66 at 20991 |
| 21004 | 638 | null | `speed_out_of_range` | HUD 38 |

The separate root review of these four output-selected abstentions plus four nearby
context crops is diagnostic, not independent acceptance:
`reports/crash-abstention-visual-review.json`. Three misreads are rejected; one
correct fresh reading is rejected during a real displayed abrupt drop. The policy
was not adjusted. It is a plausibility rule, not a demonstrated vehicle model.

Source-bound preserved numerical labels yield **19/19 BMW and 21/21 incidents exact**,
MAE/P95 0/0 km/h, no point abstentions or exclusions. Their hashes match the original
dossier and their user attribution is retained. Errors on the other 545 BMW and 662
incidents frames are not generally evaluated; the four diagnostic rejected frames
above are separately identified. Readability never supplies their numerical truth.
The historical 86-frame comparison is not reasserted as a new measurement here.

## Reproduction, verification and limits

Local scripts: `integrity_verify.py`, `replay_segments.py`, `publish_scope.py`.
Authoritative replay evidence:

- `reports/bmw-final-{freeze,replay}.json`;
- `reports/crash-final-v2-{freeze,replay}.json`;
- `reports/scoped-results.json`, including per-segment denominators, numerical pairs,
  exclusions, input hashes and old-code compatibility differences.

Freezes record source, review, settings, all package module hashes, script, Git,
OpenCV/Tesseract versions and OCR asset hash. No code/configuration changed.
Results fingerprint: `fdd4aea0b533d8f6c6419d89eb1d59530c6ee09572967f027aae96e4834df8ad`.
Preservation evidence covers 1,518 prior-run files and 108 tracked code/config files;
final checks and log hashes are recorded in `reports/final-verification.json`.

**Gate A remains FAIL; B remains blocked.** One short segment still falls below
95%. Full current-code telemetry-v2 gate evaluation, exhaustive native 1080p lap-event
truth, complete calibration-lap visibility and distinct pre-reserved independent
validation are still missing. Calibration and `s` remain unavailable and were not
recomputed. Pedal, latency and spatial evidence were not extended. No holdout review,
720p processing, R, B or research implementation was performed.

No user intervention is required to resolve these reviewed images. The subsequent
complete BMW lap review and full-source replay are now published in
[calibration-lap-results.md](calibration-lap-results.md). The run-014 results and
fingerprints above remain frozen; the later artifact owns its new calibration evidence.
