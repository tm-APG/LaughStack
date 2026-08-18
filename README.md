# LaughStack

Audience-response analytics for live comedy: laughter detection, per-joke
metrics, and cross-set A/B comparison. Built to back a recording-kit rental +
analysis service; also ingests published YouTube sets for validation and
entry-tier analysis.

## What it does

- **Detects** audience laughter and applause in a recording (DSP heuristic
  by default — no model downloads; ML backends are pluggable).
- **Scores** every event against *that room that night* (median/MAD
  normalization), corrects decay times for room reverb (RT60), and credits
  stacked tags only with energy above the previous laugh's decay envelope.
- **Aligns** laughs to transcript segments (optional faster-whisper) so each
  joke gets its own numbers — including the jokes that got nothing.
- **Compares** the same joke across different performances on normalized
  scores, flagging set-position confounds.
- **Ranks** social clip candidates from the highest-scoring bits and can
  join published-clip engagement back to live-room data per bit.

## Install

```bash
pip install -e .            # core: numpy/scipy/soundfile/yt-dlp
pip install -e .[asr]       # + faster-whisper for per-joke alignment
# ffmpeg must be on PATH for YouTube ingest and clip cutting
```

## Quick start

```bash
# QC a kit recording before the crew leaves the venue
laughstack qc night1_audienceL.wav

# Analyze a kit recording
laughstack analyze night1_audienceL.wav --performer "Jane Doe" \
    --venue "The Cellar" --date 2026-08-15 --rt60 0.6 --transcribe

# Pull and analyze a published set
laughstack youtube "https://www.youtube.com/watch?v=..." --performer "Jane Doe"
# just one comic's slot inside a long show:
laughstack youtube "https://www.youtube.com/watch?v=..." --start 3720 --end 3900

# A/B the same jokes across two analyzed nights
laughstack compare reports/night1.session.json reports/night2.session.json

# Rank clip candidates for socials
laughstack clips reports/night1.session.json --media night1.mp4
```

Each command writes a Markdown report plus a JSON session file; JSON is the
archival format and reloads without re-running DSP.

## Repository map

```
src/laughstack/
  dsp.py           cal tone, GCC-PHAT, NLMS w/ freeze mask, modulation-rate
                   laughter cue, coherence, RT60, stacked-tag decomposition
  detect/          frame scoring (heuristic + ML backend slots) -> events
  ingest/          local files + QC gates; YouTube via yt-dlp/ffmpeg
  transcribe.py    optional faster-whisper wrapper
  align.py         laugh -> punchline attachment; stacked-tag marking
  metrics.py       robust normalization, PAR/LPM, set metrics
  compare.py       cross-set joke matching + A/B verdicts
  clips.py         clip candidates + engagement join-back
  report.py        Markdown/JSON deliverables, ASCII laugh map
  cli.py           laughstack {analyze,youtube,compare,clips,qc}
config/default.yaml   pipeline defaults (copy per engagement)
docs/TECHNICAL_SPEC.md   engineering source of truth
docs/CORPUS.md           verified multi-take sets on YouTube for validation
docs/COMPETITORS.md      competitor feature inventory + gap analysis
tests/                   39 tests on synthesized audio — `pytest`
```

## Non-negotiable analysis rules

See CLAUDE.md. Short version: freeze the NLMS during laughs, decompose
stacked tags, median/MAD not mean/SD, normalize within-room before
cross-room, silent punchlines stay in the tables.

## Confidentiality

Performer retains all rights to material. Recordings are access-controlled,
destroyed on schedule, never used for training. YouTube pulls are for
internal validation only — do not redistribute.
