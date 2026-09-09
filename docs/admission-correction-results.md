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

## C3: foreground-bound historical lap OCR

The mechanistic development comparison crosses full/foreground-bound thresholded
ROI with word/character segmentation. Exact H01–H05 endpoints: 5/10 full word,
8/10 full character, 10/10 bounded word, 9/10 bounded character.
`reports/history-ocr-experiment.json` preserves every result, actual input hashes,
exploration disclosure and limitations. The chosen operation keeps all surviving
foreground pixels plus a configured one-native-pixel margin; threshold 200, cubic
3x enlargement, LSTM engine and word mode remain unchanged.

Modern `observe_lap_number` uses the bounded input, preserves the parsed raw text
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
mapping was added. Full new-code historical event recall remains pending replay.

## C2: rejected global word-mode speed candidate

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
The single-line 162→4/177→7 defects remain open on reviewed visible frames.

## Remaining verification

Freeze final correction code/config before full development replays. Speed review
must be independently justified at its exact frame scope; old control spans do not
approve speed. Sparse speed visibility may leave calibration and `s` unavailable.
Publish that loss with denominators, not fabricated continuity. Full historical
event recall and fresh independent holdout acceptance remain separate checks.
