# Temporal Centerline Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Identify a circuit from pixels that persist across sampled frames and from one uniquely valid long closed cycle, without circuit templates or car-specific cropping.

**Architecture:** Keep the broad profile ROI. Raise the configured temporal occupancy gate from 0.45 to 0.60, then evaluate connected white components independently. Accept exactly one component whose pruned skeleton yields a cycle longer than the existing ROI-relative minimum; preserve explicit ambiguity and topology errors otherwise.

**Tech Stack:** Python 3.13, NumPy, OpenCV, `unittest`, existing ignored video replay diagnostics.

---

### Task 1: Encode temporal persistence and component selection in RED tests

**Files:**
- Modify: `tests/test_configuration.py`
- Modify: `tests/test_map_progress.py`

- [ ] Change the expected production frequency threshold from `0.45` to `0.60`; run `PYTHONPATH=src .venv/bin/python -m unittest tests.test_configuration -v` and confirm RED against the current configuration.
- [ ] Add `test_selects_the_only_long_closed_component_even_when_a_distractor_is_larger`: construct a 500×500 mask containing a thin 460×460 closed track plus a larger disconnected compact component with two holes. Assert `_build(mask)` returns a centerline longer than the ROI-relative minimum and follows the outer track.
- [ ] Run `PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress.TestCenterline -v` and confirm RED because the current area-dominance rule chooses or rejects the distractor.

### Task 2: Implement the minimal generic correction

**Files:**
- Modify: `config/telemetry.yaml`
- Modify: `src/acc_telemetry/extraction/map_progress.py`

- [ ] Set `position.frequency_threshold` to `0.60`; do not change the ROI.
- [ ] In `build_centerline`, split the thresholded mask into connected components. For each component, thin it, prune short branches, order its dominant cycle, and measure the ordered cycle against `min_cycle_diagonal_fraction * ROI diagonal`.
- [ ] Accept exactly one long valid cycle. Raise `multiple_cycles` for multiple long cycles; preserve `discontinuous_path`, `no_closed_cycle`, `excessive_branches`, and `implausibly_short_path` for the existing characterized cases.
- [ ] Run `PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress tests.test_configuration -v`, then the full suite. Commit only after GREEN.

### Task 3: Validate real captures and record evidence

**Files:**
- Modify: `docs/current-status.md`
- Modify: `docs/acc-ps5-plan.md`

- [ ] Replay the new BMW session with `ps5_full_map_1080p`; require successful centerline extraction, three calibration laps, four confirmed boundaries, zero premature completions, and zero unconfirmed resets.
- [ ] Replay the previously passing clean and crash representative clips; require both to retain successful centerline extraction and their existing safety gates.
- [ ] Record source counts, effective length, checkpoint spread, unavailable duration, and any rejected laps. Do not commit videos, traces, screenshots, or JSON reports.
- [ ] Run `./scripts/docs-list`, Python compilation, the full suite, `git diff --check`, and the circuit-specific-rule search before the final documentation commit.
