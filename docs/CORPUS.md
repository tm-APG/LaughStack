# Validation Corpus — Multi-Take Comedy Sets on YouTube

Purpose: publicly available recordings where the **same comedian performs the
same material in multiple recordings**, for validating the detector and the
A/B comparison logic before any client kit recording exists. Fame is
irrelevant; what matters is same material, ideally same venue, audible crowd.

Research date: 2026-08-18. Method: web-search verification; YouTube page loads
were blocked in the research environment, so URLs come from search-indexed
titles. **Confidence key:** HIGH = multiple independent sources confirm the
video exists and its content matches; MEDIUM = existence confirmed, content
overlap inferred; LEAD = plausible, unverified — check before citing.

Ingest with:

```bash
laughstack youtube "<url>" --performer "<name>" --venue "<venue>"
# for one comic's slot inside a long show:
laughstack youtube "<url>" --start 3720 --end 3900 --performer "Kam Patterson"
```

Copyright note: pulls are for internal detector validation only. Same
retention and access rules as client recordings; never redistribute.

---

## 1. Kam Patterson — Kill Tony (Comedy Mothership, Austin) — BEST OVERALL

**Gold standard: same venue, same mic chain, weeks apart, and the repetition
is documented by name** — a minor fan controversy (Jan–Feb 2024) arose
specifically because he repeated jokes across episodes, which he acknowledged
on tape.

- Overlapping material: the "I Like Rocks" bit (a recurring routine across his
  appearances) plus bucket-pull-era jokes re-told across late-2023/early-2024
  episodes.
- Videos (existence HIGH confidence):
  - "I Like Rocks" fan clip: https://www.youtube.com/watch?v=JgvIjXxmICg
    (one telling attributed to Kill Tony ep. 616).
  - Kam's own response clip "Y'all mad at me for repeating jokes?":
    https://www.youtube.com/watch?v=VyDmKf3azvA (Feb 2024) — first-party
    confirmation the repeats exist on tape.
  - Full episodes: official Kill Tony channel, playlist "KILL TONY AUSTIN
    (COMEDY MOTHERSHIP)":
    https://www.youtube.com/playlist?list=PLD8Xk89jYzqQ49ifzf2TMdihF5Ym4gOzI
  - To pin exact repeat pairs: search `Kam Patterson Kill Tony 616`,
    `Kam Patterson repeated jokes which episodes`; killarchives.com indexes
    every comedian's appearances per episode.
- Same venue across takes: **YES** (Comedy Mothership, weekly since Mar 2023).
- Why it's a good A/B pair: venue, mic chain, host, audience type constant;
  varies: specific crowd, weeks-apart timing, delivery refinement.
  Professional multi-cam audio with clearly audible laughs.

## 2. Matt Ruby — "Substance" (same set four times, one week apart)

**Gold standard for controlled same-material comparison — repetition is the
premise of the film.** Ruby performs the same set on four nights: high,
drunk, on psilocybin, and sober. Directed by Matthew Salacuse; released free
on his YouTube channel (2023).

- Full special: "Matt Ruby: SUBSTANCE (2023) - FULL SPECIAL"
  https://www.youtube.com/watch?v=2Ak5CQSVVvI (MEDIUM-HIGH; if dead, search
  `Matt Ruby Substance full special` — it's on the "Matt Ruby" channel).
- Trailer: https://www.youtube.com/watch?v=lod28ZVtkfI (HIGH)
- Per-condition clips (pre-cut A/B segments): sober set
  https://www.youtube.com/watch?v=Hyr3Z7ZmCC8; shrooms
  https://www.youtube.com/watch?v=ZeXEBT0CnCY; "True Crime (Sober)"
  https://www.youtube.com/watch?v=WnP34rzltyQ; drunk
  https://www.youtube.com/watch?v=RYBQcK4cK4E
- Same venue: very likely one NYC club across the four nights but
  **unconfirmed** — verify from the film's credits.
- Caveats: it's an edited film; some tellings appear only partially. The
  four raw full sets are not published separately.

## 3. Hans Kim / William Montgomery — Kill Tony longitudinal

**Huge N, same venue per era; exact repeat pairs need transcript diffing.**

- Scale: Hans Kim ~164 episodes (2016 → at least KT #743); William Montgomery
  weekly regular since ~ep 296 (2020). Kill Tony Archives
  (killarchives.com/comedian/52/hans-kim) indexes appearances per episode.
- Venue eras (pick pairs within one era): Comedy Store LA (→ ~2021), Vulcan
  Gas Company Austin (2021–Mar 2023), Comedy Mothership (Mar 2023 →).
- Fan compilations pre-segment the data (existence HIGH):
  - Hans Kim appearances in order, Parts 1–5:
    https://www.youtube.com/watch?v=Rt6vqLZfBHA ·
    https://www.youtube.com/watch?v=upktgZY8EvY ·
    https://www.youtube.com/watch?v=PY1qvxlWIwg ·
    https://www.youtube.com/watch?v=oO-N2y8WHGc ·
    https://www.youtube.com/watch?v=ML2NjtbEO2E
    (playlist: https://www.youtube.com/playlist?list=PLfb3RDdLYQX8m2EwL-EGwZdpPxMOsaP5R)
  - William Montgomery per-episode-range compilations:
    https://www.youtube.com/watch?v=JLRk1cyRxsM (first two appearances),
    https://www.youtube.com/watch?v=ihUG2wNnf3s (eps 296–315),
    https://www.youtube.com/watch?v=KEM3YIcm2lk (631–635),
    https://www.youtube.com/watch?v=PCA0jo-v0XU (636–640),
    https://www.youtube.com/watch?v=13xUx-C9K8g (706–710),
    https://www.youtube.com/watch?v=2JXIenEmZDs (716–720)
- Caveat (MEDIUM): specific verbatim repeat pairs not verified by search
  alone; episode transcripts exist (podscripts.co, happyscribe) so pairs can
  be found by transcript diffing — exactly what `laughstack compare` does.
  David Lucas and Casey Rocket have equivalent compilations (LEAD).

## 4. Sam Morril — "Up on the Roof" (2020)

**Same jokes across multiple rooftop shows; venue varies, audio noisy.**

- Self-produced pandemic special filmed across many NYC rooftop shows and
  edited by stitching different performances of the same hour together;
  reviewers note the released film itself contains repeated jokes across
  cuts, and cut boundaries are visually obvious (different rooftops).
- Full special (HIGH — official free release, Nov 25 2020):
  https://www.youtube.com/watch?v=M0qDTYmaT-Y ·
  trailer https://www.youtube.com/watch?v=UxWGF2MmwOo
- Same venue: NO (multiple rooftops, similar outdoor conditions).
- Caveat: outdoor audio; laughter SNR is poor — a good stress test for the
  detector, a bad source for calibration claims.

## 5. Aaron Westberry — same joke, one set (honorable mention)

- One open-mic set telling the same "red light" joke repeatedly with
  escalating callbacks: https://www.youtube.com/watch?v=DPIoje1nfCQ
  (~May 2026; covered by Boing Boing May 18 2026).
- Within-performance repetition, not multiple recordings: useful for
  habituation/callback-decay analysis, not crowd A/B.

---

## Leads investigated but NOT verified (do not cite as fact)

- **Late-night set vs. special** (Bargatze, Jeselnik): overlap is
  industry-standard practice but no specific joke-for-joke pair verified,
  and most specials aren't freely on YouTube. Verify via transcript diffing
  (scrapsfromtheloft.com hosts special transcripts).
- **Don't Tell Comedy repeats** (e.g., Ralph Barbosa's viral DTC set vs.
  Netflix "Cowabunga"): plausible, unverified; Netflix side not on YouTube.
- **Joe List / Ari Shaffir / Stavros own-channel multi-set uploads**: LEAD.
- **Hari Kondabolu "New Material Night" Vol. 2**: real, multiple
  performances at one venue (Eclectic Theater, Seattle) — but audio-only on
  Bandcamp, not YouTube. Adjacent resource.

## StandUp4AI (arXiv 2505.18903)

Verified: 3,617 videos, 7 languages, 334 hours, ~130k automatic laughter
labels, from official Comedy Central channels (repo:
https://github.com/Standup4AI/dataset). It does **not** flag multi-take
comedians (possible duplicate material is an unflagged confound), but its
laughter-alignment pipeline is directly reusable for validating our
detector at scale.

## Recommended first pass

1. Kam Patterson Kill Tony repeats (same venue, documented, pro audio)
2. Matt Ruby "Substance" (same set ×4, one deliberately varied variable)
3. Hans Kim / William Montgomery longitudinal (transcript-diff to find pairs)
4. Sam Morril "Up on the Roof" (detector stress test)
