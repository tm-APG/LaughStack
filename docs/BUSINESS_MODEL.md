# LaughStack — Business Model

Drafted 2026-08-20. Prices are hypotheses to validate in Phase 0/1, anchored
to observed market prices (docs/COMPETITORS.md): DIY taping rigs $600–1,250,
professional specials $5k+, comic-facing apps $0–10/mo, clip tools $15–49/mo.

## Shape: service-led, software as the moat

Not a SaaS startup. The software is the margin engine and defensibility for
an AV company's existing rental + production operation. The market evidence
says standalone comedy-analytics apps don't get traction (three attempts,
~25 combined years, zero visible users); nobody has ever offered
capture + analytics as one service. Distribution is venue relationships and
comic referral — assets an app developer can't buy.

## Revenue lines (funnel order, low → high touch)

### 1. Upload / YouTube analysis — the funnel, not the business
Self-serve: comic sends a recording or a YouTube link, gets the set report
(laugh map, per-bit table, PAR/LPM) labeled "uncalibrated."
- Price hypothesis: $19–39/set, or 3-set bundle. Could be free-first-set.
- Purpose: lead generation and detector training data, not margin. Every
  report footer sells the kit tier ("these numbers can't be compared across
  rooms — here's the version that can").

### 2. Kit night — the core unit
Kit (2–4 audience mics, recorder, cal-tone source, balloon) rented per
night, self-serve pickup like existing gear rental, or crew-dropped.
QC gate run before the room empties; report delivered within 48h.
- Price hypothesis: $250–450/night self-serve incl. analysis;
  +$150–250 crew-delivered/struck.
- Marginal cost once mature: analyst QC ~30–60 min/set + trivial compute.
- Kit BOM ~$2–4k from stock we largely already own → payback in 5–10 nights.

### 3. Multi-night A/B package — the differentiator productized
Same hour recorded 3–5 nights (same room or across rooms), delivering the
cross-night joke-level comparison no one else can make: which tag is
working, what the new closer does in a cold room, position-confound flags.
- Price hypothesis: $900–1,500 for 3 nights + comparison report.
- Target: comics prepping a taping or a Netflix/late-night submission —
  the moment they already spend money.

### 4. Taping premium — highest-margin line item
Analytics added to special/showcase shoots (ours or partner producers').
Killer deliverable: multi-night shoots get a take-selection report — which
night's telling of each joke to use in the edit, currently decided by ear
on deadline. Sold to the producer, not the comic.
- Price hypothesis: $750–1,500 on a $5k+ production; near-pure margin.

### 5. Venue residency — the recurring revenue nobody occupies
Mics permanently installed; every show analyzed automatically. Producer
dashboard: lineup analytics, booking decisions backed by response data,
show-over-show trends, competition/festival scoring. Clubs already buy
software (ticketing), so the purchase motion exists.
- Price hypothesis: $300–800/mo per room, annual contract; install fee
  covers hardware.
- This is the line that turns the business from gigs into ARR, and the
  moat compounds: every resident room is exclusive data + a switching cost.

### 6. Clip pipeline — attach to where comics' money already goes
Clip candidates ranked by measured room response; optional in-house edit
(we're an AV company); engagement join-back report (live score vs
TikTok/Shorts performance per bit).
- Price hypothesis: $150–300/set for ranked+cut clips, or bundle into
  packages 3–5. Competes with $15–49/mo predictors that are wrong ~40% of
  the time — we cut from measurement, not prediction.

## Cost structure

- Fixed: pipeline development (sunk), kit capex (mostly existing stock).
- Variable: analyst time (the real COGS — target <1h/set via QC gates and
  report automation), crew time only on delivered engagements, storage
  (bounded by the retention schedule that confidentiality terms require
  anyway).
- No model-API costs in the core path (heuristic detector is local; Whisper
  runs on our hardware).

## Acquisition

Referral-first: comedy scenes are small and comics copy each other's prep.
The confidentiality terms (performer owns material, destruction schedule,
no training use) are the referral-enabling feature, not legal boilerplate.
Producer/venue side: we already have the relationships; the taping premium
is the wedge into residencies.

## What would kill it

- Phase 0 fails: the report doesn't tell a good producer anything they
  didn't already know. (Cheapest possible test — run it first.)
- Analyst time doesn't compress below ~1h/set → service doesn't scale past
  a side offering.
- A funded adjacent player (Reap, Datavault) ships venue analytics first —
  mitigations: move on residencies early, keep DSP as trade secret
  (docs/PATENTS.md).

## Deliberately not doing

- Monthly app subscription for comics (the graveyard: three competitors).
- Auto-posting clips (performer owns publication).
- Selling/licensing audience data (kills the referral engine).
