---
summary: concrete resumption guide for accepted A6 inputs and remaining independent A7 evidence
read_when:
  - resuming coaching reliability after A6 corpus acceptance
  - consuming the accepted annotation corpus
  - implementing or evaluating A7
---

# Resume after A6 acceptance

Read AGENTS.md, run `./scripts/docs-list`, read `current-status.md` and the active
specification/plan, then inspect Git. All run paths below are under ignored
`data/lab/coaching-reliability/`. The user requested finishing A6 then discussing
the working method; A7 has not started. Do not repeat any accepted review.

## 1. Verify the accepted inputs

Use `run-007/processed/accepted-corpus-v4/index.json`, its three labels/capture/review
reports and `run-007/reports/a6-acceptance.json`. All configured A6 checks pass:
100 readable frames per target field, 20 degraded frames, 20 timed pedal windows,
six physical passages and three recordings with preserved development/holdout roles.
Missing local evidence must be reported rather than reconstructed from summaries.

`run-007/reports/approval.json` preserves the exact final user response and image
identities. Earlier approvals and v3 remain immutable. Do not blindly use the generic
`consolidate` command over mixed approval formats: it would lose the independently
resolved lineage and does not consume the final scoped review format. The one-time
migration is preserved as `run-007/accept_review.py`; publish fresh outputs for changes.

Development lineage is finished. `run-005/reports/development-lineage.json` verifies
all incident video packets against the original with +515 s PTS offset and the BMW
original SHA-256. Holdout reservation and lossless-prefix proof remain unchanged.
Never ask for those approvals or provenance again; never tune extraction on holdout.

## 2. Preserve the exact event and passage semantics

Six physical intervals were explicitly accepted from the run-006 viewer. Each defines
the near/lower transverse checker-stripe edge crossing fixed x=960, y=580 (BMW) or
600 (McLaren); original definitions, endpoints and image hashes are in v4.
They support normalized-progress dispersion, not meters or wheel-crossing timestamps.

E16 begins with roughly 60% throttle according to the user and reaches 100% at frame
30397 (506.616667 s). It is `throttle_reaches_full`, not a 5% onset. The rough initial
percentage is context only, without invented tolerance or extra accuracy label.
The frame is a discrete annotation with unknown timing uncertainty, not proof of
zero error. E16 counts toward the generic A6 timed-window minimum but is excluded
from A7's first-fresh-5%-crossing latency denominator. Report subtypes/exclusions and
obtain additional applicable events if needed. E01/E12 remain untimed descriptions.

Original point labels and continuous visibility spans are unchanged. Never extend
point approvals to entire windows. Automatic blips and the E17 causal hypothesis
retain the restrictions in `current-status.md`.

## 3. Execute A7 when work resumes

Follow every unchecked A7 step in `plans/2026-09-05-coaching-reliability.md`.
`scripts/validate_capture.py` and `tests/test_capture_validation.py` do not exist yet;
implement the plan, do not report an existing benchmark as independent validation.

- Test empty truth, identical bias, duplicate/missed/unmatched event cases first.
- Read telemetry-v2 artifacts without rerunning OCR in the validator. Measure field
  errors and coverage per source; publish denominators, exclusions and tolerances.
- Match events one-to-one; report annotation midpoint error, interval half-width,
  unmatched events and confirmation delay separately. Pedal latency concerns the
  first fresh 5% crossing, not the future B4 sustained coaching detector.
- Reviewed physical landmarks support repeated-passage dispersion of normalized `s`;
  they do not establish metric spatial error. Keep old replay counters diagnostic.
- Historical September 1 false-lap validation also needs independent annotation of
  **every real and suspect transition on the full capture**. Those annotations are
  not supplied by the recent A6 corpus. Prepare and obtain them if absent; do not
  substitute a clean clip or the detector's own output as truth.
- Recent clean/crash/BMW and reserved holdout evaluation must use the planned
  definitions. Existing approvals cover individual visibility readings; consolidated
  `visibility` spans are empty. Do not extend point approvals to entire clips.
  Obtain needed continuous-span review before claiming continuous control coverage.
- Preserve holdout reservation/fingerprint compatibility. Never fit extraction on it.
- Publish the six required `gate-a.json` checks and measurement fingerprint with
  evidence paths. Missing evidence is `not_evaluated`, not pass. All must pass for B.

Use the existing `.venv/bin/python`, FFmpeg and FFprobe. No new package/workflow is
required. Tests and small relevant media checks suffice while developing; do not
repeat expensive full replays without a changed component or unresolved failure.

## 4. Commit and hand off

Before each coherent commit: focused tests, full suite, `./scripts/docs-list`,
`git diff --check`. Keep the active plan checkboxes and current status synchronized.
Update `acc-ps5-plan.md` only if a stage gate or product direction changes. Commit
only code/tests/docs/config as appropriate; personal evidence stays ignored. Push
`codex/coaching-reliability` to origin; no merge to main is authorized by this task.
