---
summary: A9 source-bound speed admission and historical OCR correction evidence, rejected numerical candidate and remaining gate limitations
read_when:
  - assessing A9 corrections or resuming their development replays
  - choosing further speed admission work without tuning on holdout
---

# A9 correction evidence

Baseline `b5eb04c`; outputs are exclusively under ignored
`data/lab/coaching-reliability/run-011/`. Prior A6/A7/A8 sources, annotations,
reviewer identities and gates remain frozen. `reports/preserved-before.json`
verifies 207 files, including A8 artifacts and images. No acceptance target changes.
Gate A stays blocked; no R or B.

## C1: reviewed HUD admission

Implemented in `97960e9`; contract in `speed-visibility.md`. Two real RED failures
prove unreviewed numbers previously became observations and odometry inputs.
The modern default now abstains with raw text. Only source-bound reviewed visible
intervals admit numeric readings; black/empty ROI abstains even within them.
Export/reload reject a speed review belonging to another source. Legacy behavior
and old artifacts retain their original quality. Five focused and 303 full-suite
tests pass; logs are `c1-focused-final.txt` and `c1-full-final.txt` in `reports/`.
This does not create an automatic detector or whole-video visibility truth.
The new service argument is appended after existing artifact/origin arguments;
their positional calling contract is protected by a separate RED/GREEN regression.

## C3: foreground-bound historical lap OCR

The mechanistic development comparison crosses full/foreground-bound thresholded
ROI with word/character segmentation. Exact H01–H05 endpoints: 5/10 full word,
8/10 full character, 10/10 bounded word, 9/10 bounded character.
`reports/history-ocr-experiment.json` preserves every result, actual input hashes,
exploration disclosure and limitations. The chosen operation keeps all surviving
foreground pixels plus a configured one-native-pixel margin; threshold 200, cubic
3x enlargement, LSTM engine and word mode remain unchanged.

Modern `observe_lap_number` uses the bounded input only when the validated profile
flag `lap_foreground_bounds` is true; it is enabled for `ps5_full_map_720p` only.
Other profiles retain their full ROI. It preserves the parsed raw text
and restores shared OCR word mode on success/failure. Blank thresholded ROI abstains.
Explicit legacy extraction retains its original full ROI. The margin is validated
as a nonnegative integer under `ocr.lap_foreground_margin_px`.

RED: three preprocessing tests fail in `reports/lap-red.txt`; the real detector
reads 5/10 correctly in `lap-real-red.json`. GREEN: the real detector reads 10/10
in `lap-real-green.json`. Four focused preprocessing/config tests and 307 full-suite
tests pass (`c3-focused.txt`, `c3-full.txt`). The image fixtures remain private and
checksum-verified; portable unit tests use synthetic pixels and controlled text.

Synthetic multi-digit composites preserve all components, but OCR reads constructed
12 as 1. These composites are not genuine ACC multi-digit layout truth; true counters
≥10 and population accuracy remain unvalidated. No one-digit assumption or output
mapping was added. Full new-code historical event results follow below.

The full historical replay now passes the reviewed event check: **5/5 matches,
five predictions, no misses, duplicates or unmatched predictions** across 56,246
frames. P95 midpoint error is 0.0083335 s; confirmation delay is 0.066667 s.
The existing exhaustive H01–H05 review remains unchanged. This is current-code
development evidence about counter increments, not physical line-crossing accuracy
or a new independent recording. `reports/historical-evaluation.json` contains
every match, uncertainty and source/configuration fingerprint.

The first full replay exposed a 1080p regression from enabling the crop globally:
BMW missed one of two approved events (the 1→2 confirmation was delayed).
That failed replay is preserved in `bmw-evaluation.json`. A subsequent RED verifies
that unconfigured profiles keep the original full ROI. The correction is now scoped
to the historical 720p profile and all sources are being replayed into new `-v2`
outputs. Earlier gates are diagnostic snapshots, not current acceptance proof.

## C2: rejected segmentation candidates and explicit rate admission

Word mode fixes both known truncations on the six output-selected frames, but fails
the expanded fixed development comparison. Accounting: 40 approved points + 44 agent
reviewed points + 6 output-selected points − 4 overlaps = **86 unique frames**.

| Mode | Exact | Abstained | Wrong admitted |
| --- | ---: | ---: | ---: |
| Existing single line | 83 | 1 | 2 |
| Candidate single word | 78 | 5 | 3 |

On the original 40 points, word mode has 36 exact and four out-of-range abstentions.
It also introduces 39→139 twice and 1→7 in the extra reviewed windows. It is rejected;
speed mode stays unchanged. `reports/speed-word-development-check.json` retains raw
text, range admission, all disagreements, scope/review attribution and source hashes.
No second OCR pass, temporal smoothing or tuned rejection threshold is introduced.
Without the admission below, single-line 162→4/177→7 defects remain on visible frames.

RAW_LINE was also rejected after the same fixed 86-frame check: its results match
word mode (78 exact, five abstentions, three admitted errors). No further mode sweep
was performed. Proof: `reports/speed-raw-line-development-check.json`.

The retained correction keeps single-line OCR and adds causal admission in the
application layer before records, observations and odometry. Its predeclared policy
is in `reports/speed-admission-policy.json`: a broad 100 m/s² absolute acceleration
envelope (approximately ten g), applied only across at most 0.25 s in the same
reviewed context. This is an admission policy, not an empirically validated vehicle
model. Real high-impact changes exceeding it may abstain. No acceptance target was
changed, and the envelope was not fitted to the holdout or adjusted after evaluation.

An excessive change becomes ANOMALOUS/null with `speed_rate_exceeded` and the original
raw text. A rejection clears temporal support, so the next fresh observation starts
a new baseline. Missing/anomalous/held reads, context changes, invalid timestamps
and long gaps also reset support. Sustained plausible wrong readings can still survive.
No median, interpolation or held number replaces the rejected measurement. Internal
odometry interpolation retains its separate provenance. Pedals remain unchanged.

RED on the real pipeline reproduces both admitted digit dropouts; GREEN returns
162/null/163 and 177/null/175, with one OCR read per frame. Five rate tests cover
exact boundaries, valid abrupt changes, invalid settings, gaps/context resets and
recovery. The 30 fps 255→246 freshness regression remains exact. The CSV/API test
uses an in-envelope 249→246 step at 60 fps while retaining exact 1/60 timestamps.

`reports/speed-admission-development.json` replays the cached single-line reads for
the same 86 unique reviewed frames: **83 exact, three abstentions, zero admitted
errors**. The two newly rejected errors preserve raw 4/7; the previous 638 rejection
remains. This is cached-read development evaluation, not new full-video OCR or
independent acceptance. It also documents the derivation of source-bound visibility
for these 86 frame cells only, preserving user and agent reviewers. No old pedal
span or unreviewed frame is expanded into speed truth. 312 full-suite tests pass.

## Remaining verification

Freeze final correction code/config before full development replays. Speed review
must be independently justified at its exact frame scope; old control spans do not
approve speed. Sparse speed visibility may leave calibration and `s` unavailable.
Publish that loss with denominators, not fabricated continuity. Full historical
event recall and fresh independent holdout acceptance remain separate checks.
