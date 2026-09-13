---
summary: exhaustive native 1080p BMW and incidents counter-media preparation, preserved prior annotations and separately observed timer/counter timing
read_when:
  - reviewing every native 1080p lap-counter image for Gate A
  - interpreting the L2 timer-reset and counter-increment distinction
---

> Historical evidence only — archived13 September2026. Old instructions, gates and next actions below are not current. Follow [current status](../../current-status.md).

# Exhaustive lap-counter dossier — 11 September 2026

**Preparation is complete; exhaustive visual event review is not complete.**
New private outputs are under ignored `data/lab/coaching-reliability/run-016/`.
Entry point: `START_HERE.md`, then `reports/lap-counter-review-dossier.json`.
No new OCR, telemetry replay, extractor change or acceptance-threshold change occurred.

## Complete source coverage

Both sources passed fresh source SHA/size, native 1920×1080, exactly 60 fps and
constant presentation-cadence checks before decoding. Each complete source was
then decoded in order through its final presentation frame, with early/extra EOF
refused. Discarded coded packets do not become presented-frame denominators.

| Source | Presented frames | Ordered sheets | Native crop files | Scene contexts |
| --- | ---: | ---: | ---: | ---: |
| BMW | 47,589 | 496 | 35,546 | 81 |
| Incidents | 29,402 | 307 | 27,318 | 51 |
| Total | **76,991** | **803** | **62,864** | **132** |

BMW source SHA-256:
`76859897055ddbac6bb52f6299dc7b86a6daf36bb3182b8d64d3da6c9aae378d`,
1,119,948,389 bytes. Incidents source SHA-256:
`b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`,
453,613,415 bytes. Exact original paths are in `reports/source-preflight.json`.

The counter crop is native `(x=245, y=80, width=110, height=105)`, including the
numeric counter and its TOURS label. A sheet holds up to 96 sequential cells,
eight columns, with frame/time labels and 2× nearest-neighbour display enlargement.
Original crop pixels remain separately available. No source video is rescaled or
resampled. First-32-frame previews on both sources verified the layout before the
full preparation; this is layout QA, not exhaustive annotation.

Only byte-identical native crop pixels share a stored PNG. **Every source frame
still has its own index row and its own sheet cell**, even when its crop repeats.
This is storage deduplication, never a sampling or review shortcut. Context images
at fixed 600-frame intervals and source endpoints support scene identification;
previous exact contexts are reused after hash/pixel checks when available.

`processed/{bmw,crash}-full/frames.jsonl` contains every frame index, video-relative
time, actual packet PTS, crop SHA/size, native pixel SHA, sheet and cell position.
`reports/{bmw,crash}-full-dossier.json` binds those indexes and every sheet/context.
All index labels remain `reviewed: false`, reviewer null, `lap_text: null`,
visibility unknown. Preparation does not silently assert continuous HUD visibility.

The script, package modules, configuration, source, preflight and layout are frozen
in `reports/{bmw,crash}-full-freeze.json`. Per-source integrity reports verify **all
76,991 cells** against the native crops, exact ordered index coverage, actual
presentation PTS, every media SHA/size, EOF counts and unchanged code/configuration.
This is structural/pixel integrity, not semantic correctness of counter readings.

## Preserved boundaries and the L2 channel distinction

`reports/prior-boundaries.json` inventories three original user-reviewed intervals
(BMW L1/L3 and incidents L2) and two separate run-015 root counter reviews. It verifies
source/annotation binding and preserves authorship. `reports/prior-boundary-links.json`
links each unchanged interval to the new sheet numbers. Overlapping approvals remain
separate records; no authority extends to surrounding frames. Existing 42 BMW
boundary crops and two sheets are referenced rather than replaced. Eight old landmark
endpoint images are explicitly identified as landmark context, not counter truth.

The incidents preview exposed a **channel difference**, checked by root from all
12 native timer/counter contexts at frames 8–19:

| Display change | Last previous frame | First new frame |
| --- | ---: | ---: |
| Current lap timer resets | 10 | 11 |
| Numeric counter changes 3→4 | 14 | 15 |

The counter update follows the timer reset by **four displayed frames (0.066667 s)**.
The old L2 `reported_lap_start` annotation at 10–11 coincides with the timer reset.
It remains unchanged; it must not be silently reused as numeric-counter transition
truth. Root's separate targeted counter review at 14–15 is not user approval, and
neither display change proves a physical line-crossing instant.

Proof: `reports/crash-L2-channel-review.json` and the bound full-frame contexts in
`processed/crash-L2-context/`. This targeted finding does not establish that every
other event has the same display offset. No annotation, old measurement fingerprint
or frozen gate was rewritten.

## Verification and remaining work

Local reproducible helpers: `prepare_counters.py`, `validate_counters.py`,
`inventory_prior_boundaries.py`, `publish_dossier.py`. Full preparation took about
172 s BMW / 114 s incidents; both sources were processed concurrently.
`reports/final-verification.json` records old run-015 preservation, source/input
integrity, focused/full tests, docs discovery and diff check. Generated media and
reports remain local and ignored; no source or application code changed.

Dossier fingerprint:
`25a480e5659895ffa171fc3701436a88a8dbe2e521b4ba751562b0a4cacd053e`.

**Gate A remains FAIL; B remains blocked.** The 803 sheets still require a complete
visual counter review with reviewer identity, literal values/uncertainty, omissions,
resets and initial/final partial-lap handling. Timer resets and numeric-counter events
must remain separate. Current compatible event measurements follow that review;
preparation alone cannot supply event recall or false-positive counts. Independent
validation and other previously recorded coverage/accuracy limits also remain open.

Next action: review all 496 BMW and 307 incidents sheets in order, publishing a new
source-bound counter-event review with uncertainty, while preserving the original
L2 interval and its separately established timer/counter distinction.

## Interrupted review attempt — run-017

The owner requested shutdown during review. No job remains active. Reusable technical
checks and extraction are saved in `run-017/START_HERE.md` and
`reports/pause-checkpoint.json`; the original run-016 dossier is unchanged.

Exploratory BMW/incident reviewer checkpoints failed root native-pixel QA: some
claimed absent/unknown counters are clearly visible. The incidents individual
reinspection (`run-017/reports/crash-review/audit-v2.json`) confirms two wrong labels.
The cause is not established. These exploratory labels must not be used as truth or
counted as completed exhaustive review. Validate a reliable display/reading method
on the disputed crops and sheets before restarting in new report files.

Current-code BMW artifact compatibility passed. Fresh source-complete incidents
reads from the counter-only path (29,402 frames) are saved, with a passing40-frame
comparison against the actual pipeline. Neither operation establishes visual event
truth; no new lap-event gate verdict was published.

Subsequent recovery attempts and targeted verification of the eight published events
are documented in [counter-review-recovery.md](counter-review-recovery.md). Exhaustive
review remains unqualified; failed run-018 ledgers must not supply annotation truth.
