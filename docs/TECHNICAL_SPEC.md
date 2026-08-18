# LaughStack — Technical Specification

Audience-response analytics for live comedy, sold as a recording-kit rental +
analysis service. This document is the engineering source of truth; the
decisions here are load-bearing — see CLAUDE.md for the short list a fresh
session must not "simplify" away.

## 1. Product shape

Two capture tiers feed one analysis pipeline:

1. **Kit tier (premium).** Our multi-mic rental package at the venue:
   comic/PA reference feed + 2–4 audience mics pointed away from the stage,
   cal tone at soundcheck, balloon-pop RT60 measurement at load-in.
   Deliverable: per-set report, per-bit table, laugh map, A/B comparisons
   across nights, clip candidates.
2. **YouTube/upload tier (entry).** Single-channel published video or a
   phone recording. Detection and within-video metrics only; clearly labeled
   as uncalibrated. Funnel to the kit tier.

## 2. Signal chain (kit tier)

```
comic mic / PA feed  ──┐
audience mic L ────────┼─→ multitrack recorder (48 kHz / 24-bit)
audience mic R ────────┤
[audience mic C/rear] ─┘
```

- **Cal tone**: 1 kHz sine through the PA at soundcheck, ≥ 2 s. Gives every
  mic a shared time origin and level reference (`dsp.detect_cal_tone`).
  Cross-mic and cross-night level comparisons are labeled "uncalibrated" if
  it's missing — never silently assumed.
- **RT60**: balloon pop (or swept sine) at load-in, per venue
  (`dsp.estimate_rt60`, Schroeder backward integration, T20 → RT60). Decay
  metrics are corrected by the room's contribution (`dsp.decay_time`), else
  we measure the venue, not the joke. Standard on the kit card: sixty
  seconds of crew time.
- **Mic alignment QC**: GCC-PHAT between mics (`dsp.gcc_phat`); PHAT
  whitening keys on timing, not loudness — robust in reverberant rooms.
- **Stage-bleed removal**: NLMS adaptive canceller per audience mic with the
  comic/PA feed as reference (`dsp.NLMSCanceller`). **Adaptation freezes
  during detected audience events** — otherwise the filter learns to cancel
  the laughter we're measuring. Two-pass offline: pass 1 detects events on
  the raw mic, pass 2 cancels with the freeze mask, pass 3 re-detects on the
  cleaned signal.
- **Room-wide vs local sounds**: magnitude-squared coherence between
  audience mics (`dsp.band_coherence`); a laugh is coherent across the room,
  one chatty table is not.

## 3. Ingest & QC gates (`ingest/`)

`run_qc` never raises on bad audio — it records findings and sets
`qc_passed`. Gates: clipping ratio, mid-file digital-silence dropouts,
noise floor (10th-percentile frame RMS), cal-tone presence. The crew runs
`laughstack qc <file>` **before leaving the venue**.

YouTube ingest (`ingest/youtube.py`): yt-dlp → bestaudio → ffmpeg → mono
16 kHz WAV, idempotent by video id, metadata sidecar JSON (`<id>.info.json`
including view/like counts for the social join). Optional `--start/--end`
to cut one comic's slot out of a long show (Kill Tony episodes). Source
type is marked `youtube` and normalization stays within-video.

## 4. Detection (`detect/`)

Backend-agnostic: every backend maps to `FrameScores` (laugh + applause
posteriors per frame); one shared event-merge stage (`detect_events`) does
hysteresis thresholding (on 0.5 / off 0.3), gap merging (0.4 s), and
per-event features. **Never duplicate the merge logic per backend.**

- **`heuristic` (default, shipped)**: band RMS elevation over a rolling
  noise floor × envelope-modulation ratio in 3–8 Hz (laughter syllable
  rate, `dsp.modulation_rate`) for laughs; × spectral flatness with *low*
  modulation for applause. Multiplicative cues — any cue can veto.
  Conservative by design: prefer missing a chuckle to crediting HVAC.
- **ML backends (integration points, optional extras)**: `yamnet`
  (AudioSet laughter/applause classes), `sensevoice` (FunASR — detects
  laughter and applause as separate events, solving applause
  discrimination), `whisper-at` (TIC-TALK, 2026, runs it at 0.8 s stride
  high-recall and merges contiguous positive windows — same merge logic as
  ours). Validate all against the heuristic on the corpus in
  docs/CORPUS.md and hand-labeled Phase-0 sets.

Per-event features: duration, peak dBFS, integrated energy, −20 dB decay
time (RT60-corrected), kind (laugh/applause/mixed), confidence.

## 5. Alignment (`align.py`, `transcribe.py`)

faster-whisper with word timestamps (optional extra). A laugh belongs to
the last transcript segment ending before its onset (≤ 3 s latency window);
beyond that it's an *unaligned* event (crowd work, physical bit) — kept,
not dropped. **Silent punchlines are data**: bits that drew nothing stay in
every table.

**Stacked tags** (`align.mark_stacked` + `dsp.decompose_stacked`): a tag
landing within 1.5 s of a previous event's end is linked to its parent.
Its credited energy is only what exceeds the parent's extrapolated
exponential decay envelope. Without this, every tag on a still-ringing room
scores as a killer and the report flatters the comic. (StandUp4AI hit the
same failure: multiple laughs within one sentence break the
punchline-at-end framing.)

## 6. Metrics (`metrics.py`)

House rules — violating any silently corrupts output:

1. **median/MAD, never mean/SD** (`robust_z`). One applause break otherwise
   drags every z-score.
2. **Normalize within the session first.** A laugh is judged against *that
   room that night*; cross-session comparison happens on normalized numbers.
   Raw dB across venues measures the PA.
3. **Stacked tags get excess energy, not raw energy.**
4. **Silence is data** — longest-silence metric, silent bits in tables.

Set-level: LPM, laugh-seconds/min, PAR score (% of stage time laughing;
18 s/min = PAR 30 = Comedy Evaluator Pro's headliner benchmark), applause
breaks, median laugh duration, longest silence.

## 7. Comparison (`compare.py`)

The differentiator no competitor ships (see docs/COMPETITORS.md): A/B of
the same joke across nights, controlled for the room. Jokes match across
sessions by token-set Jaccard on setup+punchline (≥ 0.5) because wording
drifts night to night. `ab_compare` reports Δ on normalized scores and
**flags the set-position confound** when the joke moved > 25% of the set.

## 8. Clips & social loop (`clips.py`)

Live-room data ranks clip candidates (top normalized-energy bits, setup
start → last laugh end, platform-clamped duration) → JSON manifest +
ffmpeg commands. We never auto-post; the performer owns publication.
Phase 2: `ClipEngagement` joins platform stats (views, likes, completion)
back to the live score per `bit_id` — two independent audience reads on
the same material; divergence is signal (kills live / dies online =
room-context-dependent; travels online / mid live = under-set-up).

## 9. Deliverables (`report.py`)

Markdown + JSON per session (report never hides dead bits), A/B comparison
tables, clip manifests. JSON is the archival format: sessions reload
without re-running DSP.

## 10. Privacy & material confidentiality (gating, not boilerplate)

Performer retains all rights to material. Recordings live in an
access-controlled bucket, destroyed on a stated schedule, never used for
model training. Transcripts are the comic's property. YouTube pulls are
internal validation only. This is a referral business; these terms are the
selling point over consumer apps with vague terms.

## 11. Roadmap

- **Phase 0 (validation, no capex)**: record three real sets (packed,
  sparse, corporate), hand-label in Audacity, check the report tells a good
  producer something new. Plus corpus validation per docs/CORPUS.md.
- **Phase 1**: ingest + QC gates hardened; session-log format for crews.
- **Phase 2**: ML detection backend validated vs heuristic; transcription
  + alignment in production.
- **Phase 3**: A/B comparison deliverable; clip candidates.
- **Phase 4**: engagement join-back; venue/producer analytics (booking
  decisions, show-level trends — a B2B lane nobody occupies, see
  COMPETITORS.md gap analysis).
