# LaughStack — project instructions

Audience-response analytics for live comedy (kit rental + analysis service).
Python 3.10+, numpy/scipy core, optional faster-whisper. Layout: src/
packaging; docs/TECHNICAL_SPEC.md is the engineering source of truth.

## Commands

```bash
pip install -e .[dev]     # install
pytest                    # tests (synthesized audio, no fixtures needed)
laughstack --help         # CLI: analyze | youtube | compare | clips | qc
```

## Decisions that must survive every session

These look like over-engineering to a fresh eye; each one prevents a silent
data-corruption failure, not an error:

1. **Freeze NLMS adaptation during laughs** (`dsp.NLMSCanceller` freeze
   mask). An adapting canceller learns to cancel the laughter we measure.
2. **Decompose stacked tags** (`dsp.decompose_stacked`): a tag on a
   still-ringing laugh gets only energy above the parent's extrapolated
   decay, else every tag scores as a killer.
3. **median/MAD, never mean/SD** (`metrics.robust_z`). One applause break
   otherwise skews every z-score in the set.
4. **Normalize within-session before any cross-session comparison.** Raw dB
   across venues measures the PA, not the joke.
5. **Silent punchlines are data.** Bits with no events stay in every table
   and report; never filter them out.
6. **RT60-correct decay times** when a room measurement exists, and label
   numbers "uncalibrated" when the cal tone is missing — never silently
   assume calibration.
7. **One event-merge implementation** (`detect.detect_events`). Detection
   backends emit FrameScores only; never duplicate hysteresis/merge logic
   per backend.
8. **QC never raises on bad audio** — it records findings and sets
   `qc_passed`; the analyst decides what's fatal.

## Conventions

- Times in seconds on the session timeline (t=0 at cal-tone onset for kit
  recordings); levels in dBFS.
- Session JSON is the archival format — keep `models.py` serialization
  backward-compatible; additive changes only.
- YouTube sources: `source_type="youtube"`, within-video normalization
  only, provenance kept in AudioMeta. Pulled audio is internal-only
  (confidentiality terms in the spec §10).
- Tests synthesize audio in `tests/conftest.py`; no binary fixtures in git.
