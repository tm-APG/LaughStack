# Feature backlog

Ranked by (revenue line it serves) × (nobody else has it) × (build cost).
Revenue lines reference docs/BUSINESS_MODEL.md; gaps reference
docs/COMPETITORS.md §7.

## Tier 1 — build next (each unlocks a paying use case)

1. **NLE marker export (Premiere/Resolve/FCP XML).** Export laugh events as
   timeline markers colored by intensity, plus the take-selection table for
   multi-night shoots. Serves the taping premium — the highest-margin line —
   and it's pure serialization over data we already have. An AV company
   deliverable no app company would think of.
2. **Longitudinal bit tracking.** Same bit_id across N sessions → trend
   line per joke (energy z over time, wording drift shown via transcript
   diff). "Is the new tag beating the old one" is the retention feature for
   comics on multi-night packages. Matching already exists in compare.py;
   needs a bits-over-time view and stable bit registry per performer.
3. **Multi-comic show segmentation.** Split a lineup show by performer
   (diarization or manual markers), per-comic mini-report + show-level
   comparison. This is the venue-residency product: lineup analytics,
   booking data. Whisper diarization or simple host-applause boundaries.
4. **Branded PDF report.** The client deliverable for the service business —
   the Markdown report styled for print with the laugh map rendered as a
   figure. Producers forward PDFs, not web links.

## Tier 2 — differentiating analytics (data we already compute, surfaced)

5. **Crowd-work meter.** Ratio of unaligned events (laughs with no scripted
   punchline) to aligned — quantifies improv-vs-material, a real comic
   question ("my crowd work out-earns my act").
6. **Room-heat baseline.** Score the room's responsiveness independent of
   the comic (opener-normalized, or first-5-minutes baseline) so "hot room"
   is a measured confound, not a vibe. Strengthens every A/B verdict.
7. **Tension-silence vs dead-silence.** Pre-punchline hush (falling noise
   floor before the laugh = attention) vs post-punchline flat (nothing
   landed). CEP lumps everything; nobody measures productive silence.
8. **Callback decay curves.** Same bit_id recurring within one set —
   response per repetition (habituation rate). Also covers the Westberry
   same-joke-all-set case in docs/CORPUS.md.
9. **Groan detection.** Negative-affect response class (EventKind.GROAN
   already exists in the model) — for dark material, a groan-then-laugh is
   a different signal than silence.

## Tier 3 — platform / integration

10. **Engagement auto-join.** YouTube Analytics API (own-channel) pull of
    per-clip retention/views joined to bit_id, replacing manual
    ClipEngagement entry. TikTok/IG APIs where available.
11. **Live mode.** Real-time laugh meter on a tablet side-stage / in the
    booth during residency shows; post-show report auto-delivered. Streams
    the same FrameScores; the detector is already causal-friendly at 0.25 s
    hop.
12. **ML detection backend.** SenseVoice or Whisper-AT scoring behind the
    existing FrameScores interface, validated against the heuristic on the
    docs/CORPUS.md corpus before switching defaults.
13. **Cloud transcription.** Move the analyzer to Cloud Run with a baked
    faster-whisper model so per-bit tables work for web uploads without a
    local run.
14. **Setlist import.** Paste a setlist → seed bit_ids and expected order,
    improving alignment and enabling planned-vs-performed comparison.

## Deliberately not building

- Auto-posting to social platforms (performer owns publication — spec §10).
- Joke-writing AI tools (different product, poisons the confidentiality story).
- Generated laugh tracks / response synthesis.
- Selling or pooling cross-client audience data.
