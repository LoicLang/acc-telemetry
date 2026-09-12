---
summary: telemetry-v2 session artifact layout, atomic publication, source/configuration provenance and validation limits
read_when:
  - exporting or reading versioned telemetry sessions
  - implementing A5 consumers or A6/A7 capture validation
  - resuming interrupted artifact generation
---

# Versioned session evidence

A4 adds an opt-in artifact directory to the existing CLI:

```bash
PYTHONPATH=src .venv/bin/python main.py INPUT.mov \
  --profile ps5_full_map_1080p \
  --output data/lab/example/reports \
  --visibility-json data/lab/example/visibility.json \
  --artifact-dir data/lab/example/processed/run-001
```

The paths are illustrative. Omit visibility when no reviewed annotations exist;
controls then remain missing. Supply `--clip-source-id PARENT_ID --clip-start-s 10`
only for a known derived clip. The source offset is caller-supplied provenance, not
an inferred synchronization. Without a parent, the input file identifies itself and
its time origin is zero. No video is copied or modified.

The directory contains exactly the initial evidence payloads:

- `observations.jsonl`: per-frame extraction observations, quality, raw values,
  reasons and last fresh observation times; lap labels are not confirmed here;
- `samples.jsonl`: normalized `TelemetrySample` values, confirmed lap quality,
  progress components, source values and immutable field-reason mappings on reload;
- `telemetry.csv`: the compatible pipeline records, including quality and reasons;
- `manifest.json`: `schema_version: telemetry-v2`, input SHA-256/size/path,
  source ID, profile, resolved settings and reviewed visibility spans with config
  hash, Git commit/dirty status, Python module hashes, clip origin, creation time,
  video metadata, confirmed transitions, payload hashes and validation status.

Both JSONL files carry schema/source/profile/frame/time envelopes. `time_s` is input
video-relative; `source_time_s` adds the declared parent clip offset. Source ID/hash
identify the actual input bytes; `clip_origin.source_id` identifies the declared
parent. Samples and observations remain distinct, so a held confirmed lap cannot be
mistaken for a fresh raw label.

`PipelineResult` retains its legacy records and now provides observations plus
normalized samples when explicit settings are supplied. CLI and web service supply
those settings. Old diagnostic constructors may omit them; such results cannot be
exported as modern sessions. The web service accepts optional `artifact_dir` and
`clip_origin` parameters; HTTP forms do not expose these options yet. Its OCR
thresholds now use the same resolved settings recorded in the artifact.

## Measurement mode provenance

New resolved configurations include `measurement_mode` (`reviewed` by default or
explicit `automatic`). Automatic extraction supplies no visibility annotation files;
unverified visibility remains in field reasons, and estimated progress carries
`automatic_measurements_unverified`. The mode is preserved on artifact reload;
`coaching_eligible` stays false. Numerical checks against annotations are a separate
step. Existing artifacts without this setting retain their historical semantics.

## Validation and publication

The adapter hashes the source before extraction. Export verifies it again, rejects
misaligned or mutated records, serializes without NaN/inf and hashes each payload.
Raw directories (including resolved symlinks), the source file and existing outputs
are refused. Legacy reports must stay outside the artifact directory.

Files are written in a temporary sibling directory and flushed before publication.
Publication uses kernel-enforced exclusive rename on macOS/Linux, so even an empty
destination created concurrently cannot be replaced. Unsupported platforms fail
closed. A handled interruption removes staging; a forced process kill can leave a
hidden staging directory, but never a partially published final directory. Resume
with a fresh run destination; do not treat a hidden staging directory as a session.
This is process-interruption safety, not a power-loss durability guarantee.

`read_session_artifacts(path)` requires schema v2, verifies payload/config hashes and
checks source/profile/frame/time envelopes before rebuilding typed immutable
observations/samples. Unknown versions and inconsistent files are refused. The source
video need not remain accessible just to read an existing artifact. A standalone CSV
is still readable with explicit normalization limits, but lacks modern evidence.

## Evidence limits

FFprobe examines all decoded video PTS. The timebase report requires strictly
increasing timestamps and a nominal-CFR residual within one stream time-base tick,
with no reported decoding errors. The tolerance is the stream's timestamp
quantization, not an empirically tuned accuracy threshold. Failure is recorded as
`fail`; unavailable FFprobe is `not_evaluated`. A temporary synthetic CFR video tests
this path; no private capture was replayed for A4.

`decode_coverage` and `gate_a` remain `not_evaluated`; `coaching_eligible` remains false
on export and reload, even when the timestamp check passes. A6 annotation preflight now verifies profile/resolution and presentation timestamps;
pipeline video metadata also carries decode status. A7 must still cross-check
artifact coverage/time alignment against those inputs, independent labels, measurement
errors and holdout performance. See `capture-annotations.md`. Hashes provide traceability and
integrity, not proof that the input annotations or measurements are correct.

These files support downstream analysis without repeating OCR. They do not contain
all visual candidates required to rerun the full progress fusion. The artifact
reader loads complete JSONL payloads in memory; large-session resource optimization
is not part of this milestone.
