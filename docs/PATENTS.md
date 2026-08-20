# Patent Landscape — Audience-Response / Laughter Analytics

Research date: 2026-08-20. Method: web-search extraction of patent documents
(patent full-text hosts were blocked in the research environment, so numbers
and titles are solid but no claim was read verbatim end-to-end). **This is
research, not legal advice** — an FTO opinion needs counsel reading actual
claims.

## The headline patent is not a threat

**US 12,489,946 — "Online show rendition system, laughter analysis device,
and laughter analysis method"** (granted ~Nov 2025–Feb 2026; assignee
unconfirmed, likely Japanese applicant). It covers **per-viewer facial-video**
laughter analysis (zygomaticus major feature tracking → "laughter energy" via
a dynamic model) for **online/streamed shows**, driving automatic staging
effects. Orthogonal to our pipeline (room mics, acoustic events, no per-viewer
cameras, no automated show rendition). Revisit only if we ever add per-viewer
webcam scoring for livestreams.
PDF: https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12489946

## Prior-art map by pipeline element

| Element | Verdict | Key prior art |
|---|---|---|
| Laugh detection + LPM / per-joke scores | **Anticipated** | Sony US7889073B2 (2008, laugh detector time-referenced to media; expires ~2028); US8571853B2 (laughter = burst-structure detection, expiring ~2027-8); Comedy Evaluator Pro (commercial, longstanding); clap-o-meter lineage (1956) |
| Freeze-masked NLMS preserving the measured signal | **Weak** | Identical mechanism to double-talk detection (Geigel detector, 1970s AT&T; EP1783923B1 "freezes or slows the AEC adaptation"). Same freeze, same trigger, different intent → §103 obviousness |
| RT60-corrected laugh decay cross-venue | **Weak** | Textbook use of RT60 (ISO 3382, Schroeder); US10403300 (room-parameter estimation) |
| Live-room ↔ online clip engagement join per joke | **Weak** | §101 abstract-idea territory (*Electric Power Group*); Nielsen US9003457 (second-screen reactions timestamp-correlated to program moments); YouTube retention heatmaps |
| **Stacked-tag decomposition** (credit a tag only with energy above the parent laugh's extrapolated decay envelope) | **Only plausible candidate** | Nothing on point found. Nearest: polyphonic sound-event detection, envelope subtraction. A narrow method claim could be argued non-obvious — but scope is narrow, design-arounds easy, and infringement happens server-side where it can't be detected |

## Freedom to operate

**Low risk overall** for the described product (multi-mic kit, acoustic
detection, robust per-joke stats, cross-show normalized comparison) — nothing
found reads on the combination. For a professional read, prioritize:

1. **US12413813** — "real-time generation of live event audience analytics"
   from live audio (recent; claims unread).
2. **US12262082B1** — ML laughter extraction from ambient venue mics (but
   directed at *generating* reactive content).
3. **US7889073** (Sony) — only if scoring playback of recorded media against
   its timeline; expires ~2028.
4. Nielsen portfolio — relevant only if drifting into broadcast ratings; note
   *Nielsen v. TVision* (Fed. Cir. Aug 2026) affirmed PTAB invalidation of a
   Nielsen audience-measurement patent — this space is being thinned.

## Strategy recommendation

- §101 reality: "measure audio, compute statistics, compare" is abstract-idea
  territory; survivable claims must anchor in concrete capture-chain steps,
  which shrinks them to near-unenforceable scope.
- Everything valuable executes inside our service — competitor infringement
  would be undetectable. A patent whose infringement you can't detect is a
  published recipe.
- **Primary strategy: trade secret** (the Laff Box playbook — Charley
  Douglass dominated TV laughter for two decades by guarding the box):
  keep DSP internals server-side and out of marketing copy; NDAs on kit
  rental and analysis contracts.
- Cheap optionality: one micro/small-entity **provisional on stacked-tag
  decomposition only** (~$65–130 filing + drafting; $2–5k with attorney),
  decide within 12 months. Alternative: **defensively publish** the method to
  guarantee FTO against later filers, at the cost of secrecy.

Costs if pursued to utility: ~$10–25k+ through prosecution, 2–4 years.
