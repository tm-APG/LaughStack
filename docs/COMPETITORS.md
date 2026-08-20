# Laugh Data Landscape

**Competitor feature inventory for a comedy-performance-analytics product** (audience laughter detection, per-joke metrics, set comparison — sold as a recording-kit rental + analysis service by an AV production company).
Research date: 2026-08-18.

> **Access note (competitive intel in itself):** the research environment's egress proxy blocked direct fetches of `standappcomedy.com`, `comedymetric.app`, `comedyevaluatorpro.com`, `apps.apple.com`, `play.google.com`, `thebits.club`, and `web.archive.org`. All findings below come from search-engine-indexed content of those pages plus third-party coverage. Where a claim could not be confirmed, it is marked **unverified** or **unknown** rather than guessed. Notably, *none* of the three core competitors have meaningful third-party press, review coverage, or visible Reddit discussion — these are tiny, low-awareness products, which is itself a market signal.

---

## 1. Core competitors (direct laugh-analytics products)

### 1.1 StandApp Comedy — standappcomedy.com

Site tagline: "Set Analysis & LPM Tracking for [comedians]."

**Features (everything confirmable from indexed site copy):**
- **Upload-based analysis:** "Drop in a recording of your set and instantly track your Laughs Per Minute (LPM)" — i.e., post-hoc upload of an audio file, not live capture. Recording device is whatever the comic used (in practice a phone in the pocket or a voice-memo app).
- **Automatic laughter detection / LPM:** shows "where laughs hit and which bits need work before your next gig" — a per-set laugh timeline (effectively a laugh map, though the indexed copy doesn't use that word).
- **Automatic bit segmentation:** "transcribes your set and splits it into bits so you can review each section clearly instead of digging through one long recording."
- **Transcription:** full-set speech-to-text, in **90+ languages** (English, Hindi, Arabic, Spanish, French, German, Portuguese named).
- **Library/organization:** "keep every set and bit organized with dates, tags, and stats" — implies longitudinal stats per bit, which is a weak form of set comparison, but **no evidence of true side-by-side set or joke A/B comparison**.
- **Set comparison, laugh map visualization specifics, export options, social/sharing features: not found in any indexed content.** Unknown, likely absent or minimal.

**Pricing:** not indexed anywhere; **unknown**. No pricing page surfaced in any query.
**Platform:** presents as a web app ("drop in a recording"); no confirmed iOS/Android listing for *this* product. Caution: an AppStorio page lists an iPhone/iPad app called "StandApp Comedy" categorized as *Social Networking* ("record and upload your funny jokes… see how many likes you can get") — that appears to be an older, unrelated app sharing the name; do not conflate.
**Target user:** working open-mic / club comics prepping their next set.
**Data captured:** user-uploaded audio, transcript, laugh timestamps, bit tags/dates.
**User complaints:** zero Reddit/forum discussion surfaced — the product has essentially no public footprint.

Sources: [standappcomedy.com](https://standappcomedy.com/) (via search snippets), [AppStorio listing](https://appstor.io/app/standapp-comedy).

### 1.2 Comedy Metric — comedymetric.app

Site tagline: "Made by Comics, For Comics | Stand-Up Comedy Performance Platform."

**Features (all that is publicly indexed):**
- "Track laughs per minute" — LPM tracking (method — manual tap vs. audio analysis — **not disclosed** in indexed content).
- "Analyze sets."
- "Time your acts" — act/set timing.
- "Manage shows, and book gigs" — show management + booking layer, which the other two core competitors lack; positions it as a career-management platform, not just analytics.

**Pricing:** not indexed; **unknown**.
**Platform:** no App Store or Google Play listing surfaced under this name; presumably web (`.app` domain) — **unverified**.
**Target user:** stand-up comics managing both craft and bookings.
**Sharing/social/export:** nothing indexed.
**User complaints/reviews:** none found anywhere (no Reddit, no Product Hunt, no press). Extremely low public footprint.

Source: [comedymetric.app](https://comedymetric.app/) (via search snippets).

### 1.3 Comedy Evaluator Pro (CEP) — comedyevaluatorpro.com

Steve Roye's evaluation tool, tied to his "Killer Stand-up Online Course" ecosystem (realfirststeps.com / killerstandup.com).

**Methodology — fully manual, human-timed:**
- While listening to a **recorded or live** performance, the user holds/taps a Record button at the start of each **PAR event** (Positive Audience Response = laughter, cheering, or applause — deliberately lumped together) and releases at its end. Mobile: tap; desktop: hover or space bar.
- **PAR Score** = percentage of performing time filled with laughter/cheering/applause, per minute and for the whole set.
- **PAR frequency**: number of response episodes per performing minute.
- **PAR duration**: seconds per individual response event.
- **Benchmarks:** headliner standard = average **≥18 seconds of laughter per performing minute** (PAR ≈ 30%); "comedy star" level = **24+ sec/min** (PAR 40+). Roye explicitly argues raw laugh *counts* (LPM) are inferior to laughter *duration* measurement.
- **Reports:** "CEP User Reports"; shareable externally-linkable evaluation reports exist (`/cep-external/?id=…` pages are public), so results can be sent to coaches/peers.

**Pricing:** first trial 7 consecutive days, fully functional, no sign-up; references to a 21-day free-trial window; after that **two on-demand payment options** (pay-as-needed, explicitly **no recurring subscription**) — exact dollar amounts not indexed. 1 year of CEP access bundled free with Killer Stand-up Online Course membership.
**Platform:** web-based, responsive ("nothing to download or update"); works on phone/tablet/desktop.
**Recording method:** none — CEP does not record or store audio; the user supplies/plays their own recording and *manually* times responses against it.
**Target user:** comedians **and professional speakers** (explicitly marketed to speaking pros).
**Notable gaps/complaints:** entirely manual (attention-intensive, subjective start/stop, can't be done while performing without a helper); no transcript, no bit segmentation, no audio storage, no automation; the PAR construct cannot distinguish laughs from applause **by design**. Site content is heavily SEO-blog driven; product appears dated (long-standing tool, minimal evolution).

Sources: [comedyevaluatorpro.com](https://www.comedyevaluatorpro.com/), [CEP overview](https://www.comedyevaluatorpro.com/235/comedy-evaluator-pro/), [CEP user reports](https://www.comedyevaluatorpro.com/cep-user-reports/), [external report example](https://www.comedyevaluatorpro.com/cep-external/?id=2102), [benchmark discussion](https://www.realfirststeps.com/1029/stand-up-comedy-performance-levels/), [LPM critique](https://www.realfirststeps.com/13528/stand-up-comedy-laughs-per-minute/).

---

## 2. Adjacent competitors: setlist / joke-management apps with recording

These don't do automated laugh analytics, but they own the comic's daily workflow (writing → setlist → record → review), so they're the incumbent habit your product must slot into or replace.

| App | Platform / price | Recording | Analytics-adjacent features | Notes |
|---|---|---|---|---|
| **Standup Studio** ([iOS](https://apps.apple.com/ca/app/standup-studio/id6744249349), [Android](https://play.google.com/store/apps/details?id=ca.studio117.jokebook&hl=en_US)) | iOS + Android; price unverified | In-app audio while viewing setlist; on-stage timer | Log every mic/show, attach setlist, post-show self-rating + private notes, cloud sync of jokes/sets/shows/recordings | "By comedians for comedians"; review-by-listening only, no laugh detection |
| **Jokely** ([site](https://jokelyapp.com/), [iOS](https://apps.apple.com/us/app/jokely-stand-up-comedy/id6744562322), [Android](https://play.google.com/store/apps/details?id=com.jokely.Jokely&hl=en_US)) | iOS/Android; free (per App Store snippet) | Stage Mode auto-records; distraction-free view, timer | Claims "analyze audience reactions," "track laugh-metrics over time," performance history | Depth of the "laugh-metrics" claim unverified — likely manual ratings, not audio analysis |
| **Bits** ([thebits.club](https://www.thebits.club/), [iOS](https://apps.apple.com/us/app/bits-stand-up-writing/id1481029465)) | iOS | "On Stage" mode records sets against setlist | Performance tracking per bit; help-center article on using On Stage mode to improve | Got [Fast Company coverage (2019)](https://www.fastcompany.com/90328816/move-over-tiktok-bits-is-the-new-app-that-wants-to-launch-comedy-stars) as a comedy social platform; site fetch blocked, feature depth unverified |
| **The Comedy Companion** ([iOS](https://apps.apple.com/us/app/the-comedy-companion/id1245335115), [Android](https://play.google.com/store/apps/details?id=com.comedycompanion&hl=en_US)) | iOS/Android; freeware | Record show audio or full-screen timer | Bit notes, drag-drop setlists with duration estimates, venue log, iCloud backup, **email export of jokes/setlists** | Open-source React Native origin ([GitHub](https://github.com/dereksweet/ComedyCompanion)); last version 1.4 (2024) |
| **Set List: Standup Manager** ([iOS](https://apps.apple.com/app/id6747993417)) | iOS/iPad; **$9.99** one-time | Records while displaying setlist; screen never locks | Performance counts + per-bit ratings, tag-based venue-appropriate set building, time estimates, cross-device sync | Manual ratings, no audio analysis |
| **Show Your Bits** ([iOS](https://apps.apple.com/us/app/show-your-bits/id6744169742)) | iOS | Setlist timer | "Bit Assist" — instant feedback on timing, structure, **and laughs-per-minute**; practice mode (word counts, streaks); Idea Bank; **Comedy Feed** social sharing of bits/memes/clips | One of the only apps pairing an LPM concept with a social feed; mechanism of its LPM feedback unverified |
| **BitBinder** ([iOS](https://apps.apple.com/hn/app/bitbinder/id6753145615)) | iOS | "High-quality audio" recording of performances | Joke library, setlists, notes on what works | New (2025-era), tiny footprint |
| **Joktor** ([iOS](https://apps.apple.com/ca/app/joktor/id6520393668)) | iOS; free | Record directly from setlist page | Jokes + setlists, replay to refine delivery | Minimal |
| **Comedy OS** ([iOS](https://apps.apple.com/us/app/comedy-os/id6765978741)) | iOS | — | "Capture jokes, build structured sets, track gigs, measure progress" | New entrant, details thin |
| **Standup Writer: Comedy & Sets** ([Android](https://play.google.com/store/apps/details?id=com.KalromSystems.standup_writer&hl=en_US), [web](https://stand.app/en)) | Android + web sync (iOS listing exists as "Stand Up Writer: Jokes & Shows") | — | Joke database, post-show bit ratings ("shows what's landing") | Writing-first |

**Pattern across all of these:** phone-mic recording (if any), manual self-rating, zero signal processing, zero audience-response automation, single-performance review. None normalize across rooms; none compare the same joke across nights except by eyeballing manual ratings.

---

## 3. Manual-timing lineage and transcription services

- **Rev** markets human/AI transcription of stand-up routines to comedians for repurposing material and captioning clips ([rev.com blog](https://www.rev.com/blog/how-to-get-transcripts-of-your-stand-up-comedy-routines-to-grow-your-following)). Transcript only — no laugh data.
- The **realfirststeps.com / topcomedysecrets.com** content network (same author as CEP) has spent a decade seeding the "18 seconds of laughter per minute" benchmark ([source](https://www.realfirststeps.com/1029/stand-up-comedy-performance-levels/), [source](https://www.realfirststeps.com/995/performance-improvement-basics-comedians/)) — useful: the market already has a vocabulary for laughter-duration-per-minute that your product can measure *automatically and objectively*.

---

## 4. Social-clip tools comedians actually use

These are the strongest *budget competitors* — a comic with $30/mo is likelier spending it here than on analytics.

### Reap (reap.video) — the only clip tool explicitly marketing to comedians
- Blog: "AI for Comedians: Turn Every Show Into 20 Viral Moments" ([reap.video/blog/ai-for-comedians](https://reap.video/blog/ai-for-comedians)).
- Claims multi-signal detection of **punchline peaks, crowd reactions, heckler spikes, emotional shifts, audience laughter patterns, delivery timing** — i.e., real laugh detection, but pointed exclusively at *clip selection*, not performance metrics.
- Yield claims: 10-min set → 4–8 clips; club night → 10–15; special → 20–40.
- Prompt-first clipping, animated captions (100+ languages), dubbing (80+ languages), API/CLI.
- **Pricing:** free plan (1 hr AI clipping, 720p); paid from **$9.99/mo billed yearly** (1080p/4K, all features). ([reap.video](https://reap.video/), [pricing per aitools.inc/seofai listings](https://aitools.inc/tools/reap))

### OpusClip (opus.pro)
- Long video → 10+ vertical clips; **Virality Score 0–99** (Hook / Flow / Value model) ([help.opus.pro](https://help.opus.pro/docs/article/virality-score)); auto-reframe, captions, direct scheduling to TikTok/Reels/Shorts; ClipAnything handles non-podcast footage (stage-wide shots).
- Free tier + paid plans. Known complaint: roughly **40% of generated clips are discarded** by testers — the score is a *prediction*, never reconciled against actual post performance ([BIGVU test](https://bigvu.tv/blog/opus-clip-tested-2026-where-ai-wins-40-percent-discard/)).

### Vizard (vizard.ai)
- Creator plan from **$29/mo**; transcript-based editing (delete text → trims footage); auto clip scoring; auto speaker tracking/reframing. Tuned to **webinars/corporate talks, not entertainment peaks** — a documented weakness for comedy ([Ssemble comparison](https://www.ssemble.com/blog/vizard-vs-opus-clip-vs-ssemble), [pixelpanda review](https://pixelpanda.ai/review/vizard-ai)).

### Munch (getmunch)
- ~**$49/mo**, most expensive of the cohort; GPT+OCR+NLP scoring against *currently trending topics*; complaints: slow processing, premium not justified ([Choppity roundup](https://www.choppity.com/blog/best-opus-clip-alternatives/)).

### ClipSpeed
- Publishes a comedy-specific clipping guide; detects "emotional peaks"/biggest laughs from audio waveforms + audience reactions; notes crowd-work clips are the highest-performing comedy format on TikTok/Shorts ([clipspeed.ai guide](https://www.clipspeed.ai/blog/comedy-standup-clips-tiktok-shorts.html)).

### Descript
- Text-based video/audio editing (edit transcript → edits media), Studio Sound cleanup, captions, publishes comedy-editing guidance ("bad sound can ruin a punchline") ([Descript comedy-clip guide](https://www.descript.com/blog/article/learn-how-to-edit-a-comedy-clip-and-make-your-jokes-land), [pricing page](https://www.descript.com/pricing) — free to start, paid tiers). General-purpose; no laugh metrics.

**Key observation:** every clip tool *predicts* virality pre-publish. **None ingests actual TikTok/Shorts/Reels engagement (views, likes, retention curves) after publishing, and none joins social engagement back to live-room laughter data.** The closest thing is OpusClip's static Virality Score, which testers show is wrong ~40% of the time.

---

## 5. B2B / venue-side and production-service players

### Datavault AI × Rodney's Comedy Club — the only venue-analytics move found
- Nov 2025 press release: "industry-first **Laugh Index**" — AI agents in the club "recording each joke as told along with the laughter generated throughout the joke and the punchline of each joke," plus **live joke copyrighting**, **Joke Token** (blockchain fan rewards), **VerifyU** performer credentials, and **ADIO** data-over-sound audience interaction ([GlobeNewswire](https://www.globenewswire.com/news-release/2025/11/06/3183022/0/en/Datavault-AI-Partners-with-Rodney-s-Comedy-Club-to-Bring-Digital-Innovation-to-the-Live-Entertainment-Scene-with-Live-Joke-Copyrighting-and-Industry-First-Laugh-Index.html), [Datavault IR](https://ir.datavaultsite.com/news-events/press-releases/detail/377/datavault-ai-partners-with-rodneys-comedy-club-to-bring)).
- **No published methodology, no product page, no pricing, single venue, buried in blockchain/Web3 framing.** Reads as a press-release pilot, not a product — but it validates the venue-analytics thesis and could become a mover.

### Production/taping services (closest analogues to the recording-kit-rental model)
- **Henri Rapp — production sound for comedy specials** ([henrirapp.com/comedy-recording](https://henrirapp.com/comedy-recording/)): professional multi-mic capture (performer + isolated audience mics) for specials. Pure AV service — no analytics deliverable.
- **Church of Satire comedy club "Record Your Comedy Special" package** ([site](https://www.churchofsatirecomedyclub.com/general-8-1)): 3-camera shoot, pro lighting, **isolated audio for mic and audience**, edited up-to-1-hour special. Venue-bundled taping — again no analytics.
- DIY norms: comedy-scene guides put self-taping audio rigs at **$600–$1,250** and specials at **$5k+** professionally shot ([comedymemphis.com](https://www.comedymemphis.com/post/how-to-create-stand-up-comedy-special), [comedyhouston.com](https://comedyhouston.com/how-to-film-stand-up-comedy/)); standard advice is "a $200 recorder on the board feed beats a camera upgrade."

**Nobody found bundles professional capture + analytics as one service.** The AV world stops at deliverable video/audio; the analytics world starts from a phone recording.

### Research/tech context (defensibility watch)
- Academic pipelines already exist for automated comedy analysis: **TIC-TALK** (text+audio+laughter+kinesics segmentation of specials, [ACL 2026](https://aclanthology.org/2026.chum-1.2/)), **ManzaiSet** viewer-response dataset ([arXiv](https://arxiv.org/pdf/2510.18014)), Whisper-AT laughter detection at ~0.8s precision, and a granted US patent on a **laughter analysis device** for online shows ([USPTO 12489946](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12489946)) — worth a freedom-to-operate check.

---

## 6. Feature comparison table

Legend: ● = confirmed, ◐ = partial/weak, ○ = claimed but unverified, — = absent/no evidence, ? = unknown (info unavailable).

| Capability | StandApp | Comedy Metric | Comedy Evaluator Pro | Setlist apps (best-of) | Reap | OpusClip / Vizard / Munch | Datavault Laugh Index |
|---|---|---|---|---|---|---|---|
| Automated laughter detection | ● | ? | — (manual tap) | — | ● (for clipping) | ◐ (generic "engaging moments") | ○ |
| LPM / laughter-duration metric | ● LPM | ● LPM | ● PAR sec/min | ◐ (Show Your Bits "Bit Assist") | — | — | ○ |
| Per-joke / bit segmentation | ● (auto, via transcript) | ? | — (per-minute only) | ◐ (manual setlist mapping) | ◐ (clip boundaries) | ◐ | ○ (per-joke claimed) |
| Transcript | ● (90+ languages) | ? | — | — | ● | ● | ? |
| Laugh map / timeline visualization | ◐ ("where laughs hit") | ? | ◐ (per-minute report) | — | — | — | ? |
| Set-over-set comparison | ◐ (dates/tags/stats) | ◐ ("analyze sets") | ◐ (compare report PDFs by hand) | ◐ (manual ratings history) | — | — | ? |
| Same-joke A/B across performances | — | — | — | — | — | — | — |
| Applause vs laugh discrimination | ? | ? | — (lumped by design) | — | ◐ (crowd reaction types, for clips) | — | ? |
| Silence/tension metrics | — | — | — | — | — | — | — |
| Room calibration / venue normalization | — | — | — | — | — | — | — |
| Multi-mic professional capture | — (upload phone audio) | — | — (no capture) | — (phone mic) | — (any video) | — (any video) | ◐ (in-venue mics, unclear) |
| Auto clip generation for socials | — | — | — | — | ● | ● | — |
| Post-publish social engagement loop | — | — | — | — | — | — | — |
| Show/booking management | — | ● | — | ● | — | — | — |
| Venue/producer-facing analytics | — | — | — | — | — | — | ○ |
| Sharing/social features | ? | ? | ● (external report links) | ◐ (Show Your Bits feed; email export) | ● (direct publish) | ● (scheduling) | ● (fan tokens) |
| Pricing transparency | — (unknown) | — (unknown) | ◐ (trial + on-demand, amounts unpublished) | ● ($0–$9.99) | ● ($0–$9.99/mo+) | ● ($15–$49/mo) | — |
| Platform | Web (likely) | Web (likely) | Web (responsive) | iOS/Android | Web + API | Web | Venue install |

---

## 7. Gap analysis — what NONE of them do

Candidate differentiators, hardest-to-copy first:

1. **Multi-mic professional capture as the data source.** Every analytics competitor ingests a single phone/voice-memo recording; every clip tool ingests whatever video exists. Nobody controls the capture chain (performer mic + distributed audience mics + board feed). A rental kit + service model owns signal quality end-to-end — which is precisely what makes the next four items *possible at all* on your side and *impossible* on theirs.
2. **Room calibration / RT60 correction / cross-venue normalization.** Zero evidence anyone corrects for room acoustics, crowd size, or mic placement. Today a comic literally cannot tell "this room was hot" from "this joke got funnier." A normalized laugh score valid across venues is an unclaimed, defensible metric — and the reverb/decay physics require calibrated capture (see #1).
3. **True A/B of the same joke across performances.** Closest anyone gets is manual per-bit star ratings (Set List, Standup Writer) or StandApp's per-bit stats over time. Nobody does transcript-aligned matching of the same bit across nights with overlaid laugh curves. This is the single most requested-feeling workflow ("did the new tag work?") and it's absent everywhere.
4. **Stacked-tag decomposition.** Detecting a tag that lands on a still-ringing laugh and attributing incremental response to it does not exist in any product found. CEP can't (manual, per-minute); StandApp segments bits but shows no evidence of laugh-onset overlap analysis. Requires clean audio separation of performer vs audience — again gated on capture quality.
5. **Silence/tension and applause-vs-laugh discrimination.** CEP *explicitly merges* laughter/cheer/applause into one PAR bucket. No product measures productive silence (tension before a dark punchline), groans, or applause breaks as distinct signals. Academic tooling (Whisper-AT-class audio tagging) proves feasibility; no one has productized it.
6. **Closing the social loop: live laughs → clip candidates → actual engagement → back to the set.** Two half-products exist and no bridge: (a) Reap/OpusClip/ClipSpeed detect laugh peaks to *generate* clips and predict virality — but never reconcile predictions with real TikTok/Shorts/Reels performance (OpusClip testers discard ~40% of "high-virality" clips); (b) no analytics product ingests platform engagement at all. A product that ranks clip candidates by *measured in-room laugh intensity*, then joins post-publish views/likes/retention back onto the same bit's live data ("kills in the room, dies online" vs "flat live, viral online") would be first and alone. This is also the feature most likely to make comics pay, since clips are already where their money goes.
7. **B2B venue/producer analytics.** Only Datavault AI has gestured at club-side laugh analytics (one venue, Nov 2025, blockchain-wrapped, no methodology or pricing published). Nothing exists for: producer-facing show reports, comparative lineup analytics, booking decisions backed by response data, or festival/competition scoring. An AV company already embedded in venues has distribution the app-makers lack. Adjacent validation: comedy clubs already buy software (ticketing — TicketFairy, Mighty Tix, Open Comedy), so a venue-facing analytics report line-item is a familiar purchase motion.
8. **Service, not app.** All direct competitors are self-serve DIY tools priced (where known) between free and ~$10/mo one-time-$9.99. The market has *no* premium "we record your set properly and hand you a per-joke report" offering — the production-service side (Henri Rapp, club taping packages) delivers media, never metrics. The rental-kit + analysis-report model has no incumbent.

**Where differentiation is weakest (don't lead with these):** LPM as a headline number (StandApp, Comedy Metric, Show Your Bits all claim it; CEP's author has spent years arguing it's a bad metric); transcription (commodity — StandApp does 90+ languages already); setlist management (a dozen free/cheap apps own it; integrate or import, don't compete).

**Threat watch:** Reap is one pivot away from comedy analytics (it already detects punchline peaks and crowd reactions and markets to comedians); Datavault has venue relationships and a press machine; StandApp has the most complete auto-analysis pipeline of the small players (detection + transcript + bit segmentation) but no visible traction, no public pricing, and no capture-quality story.

---

## 8. Source index

- StandApp Comedy: https://standappcomedy.com/ · https://appstor.io/app/standapp-comedy
- Comedy Metric: https://comedymetric.app/
- Comedy Evaluator Pro: https://www.comedyevaluatorpro.com/ · https://www.comedyevaluatorpro.com/235/comedy-evaluator-pro/ · https://www.comedyevaluatorpro.com/cep-user-reports/ · https://www.comedyevaluatorpro.com/cep-external/?id=2102 · https://www.realfirststeps.com/1029/stand-up-comedy-performance-levels/ · https://www.realfirststeps.com/13528/stand-up-comedy-laughs-per-minute/
- Setlist/joke apps: Standup Studio https://play.google.com/store/apps/details?id=ca.studio117.jokebook · Jokely https://jokelyapp.com/ , https://apps.apple.com/us/app/jokely-stand-up-comedy/id6744562322 · Bits https://www.thebits.club/ , https://www.fastcompany.com/90328816/move-over-tiktok-bits-is-the-new-app-that-wants-to-launch-comedy-stars · The Comedy Companion https://apps.apple.com/us/app/the-comedy-companion/id1245335115 · Set List: Standup Manager https://apps.apple.com/app/id6747993417 · Show Your Bits https://apps.apple.com/us/app/show-your-bits/id6744169742 · BitBinder https://apps.apple.com/hn/app/bitbinder/id6753145615 · Joktor https://apps.apple.com/ca/app/joktor/id6520393668 · Comedy OS https://apps.apple.com/us/app/comedy-os/id6765978741 · Standup Writer https://play.google.com/store/apps/details?id=com.KalromSystems.standup_writer
- Clip tools: Reap https://reap.video/ , https://reap.video/blog/ai-for-comedians · OpusClip https://help.opus.pro/docs/article/virality-score , https://bigvu.tv/blog/opus-clip-tested-2026-where-ai-wins-40-percent-discard/ · Vizard/Munch comparisons https://www.ssemble.com/blog/vizard-vs-opus-clip-vs-ssemble , https://www.choppity.com/blog/best-opus-clip-alternatives/ · ClipSpeed https://www.clipspeed.ai/blog/comedy-standup-clips-tiktok-shorts.html · Descript https://www.descript.com/blog/article/learn-how-to-edit-a-comedy-clip-and-make-your-jokes-land , https://www.descript.com/pricing
- B2B/venue & services: Datavault AI × Rodney's https://www.globenewswire.com/news-release/2025/11/06/3183022/0/en/Datavault-AI-Partners-with-Rodney-s-Comedy-Club-to-Bring-Digital-Innovation-to-the-Live-Entertainment-Scene-with-Live-Joke-Copyrighting-and-Industry-First-Laugh-Index.html , https://ir.datavaultsite.com/news-events/press-releases/detail/377/datavault-ai-partners-with-rodneys-comedy-club-to-bring · Henri Rapp https://henrirapp.com/comedy-recording/ · Church of Satire taping package https://www.churchofsatirecomedyclub.com/general-8-1 · DIY norms https://www.comedymemphis.com/post/how-to-create-stand-up-comedy-special , https://comedyhouston.com/how-to-film-stand-up-comedy/
- Research context: TIC-TALK https://aclanthology.org/2026.chum-1.2/ · ManzaiSet https://arxiv.org/pdf/2510.18014 · laughter-analysis patent https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12489946 · "Can AI read the room?" https://www.tandfonline.com/doi/full/10.1080/2040610X.2025.2544414
- Transcription: https://www.rev.com/blog/how-to-get-transcripts-of-your-stand-up-comedy-routines-to-grow-your-following

---

## 9. Who's behind the three core competitors (researched 2026-08-20)

### StandApp Comedy — creator unidentifiable; every signal says solo AI-assisted build
No founder, company entity, or individual name surfaces anywhere in
search-indexed content. Hosted on **Vercel** (default deploy target for
Next.js/AI-assisted indie builds). The domain is **recycled** — it appears in
expired-domain drop lists for 2014, 2017, and April 2022, so the current
product re-registered it after April 2022, likely launching 2024–2026. The
"90+ languages" transcription claim almost certainly means a thin wrapper
over off-the-shelf ASR (Whisper or a commercial STT API). No Product Hunt or
Indie Hackers launch, no Reddit threads, no social accounts, no app-store
listing, no press; only trace of promotion is comment threads on a comedy
Substack. **Beware name collisions**: a deadpooled 2018 stand-up streaming
app "StandApp" (founder Rudi Azank, per Tracxn), a Brazilian comedy-ticketing
app, and an old iOS joke-sharing app all share the name — none are this
product.

### Comedy Metric — creator unidentifiable; slightly more ambitious, equally anonymous
DNS resolves to a Google Cloud load balancer (typical Firebase/Flutter-web
build); .app TLD bounds launch to post-2018, indexing depth suggests
2024–2026. "Made by Comics, For Comics" implies comedian founders, but no
comic's name is attached anywhere search engines can see — notable for a
product whose whole pitch is comedian credibility. Booking/show management
scope suggests a real roadmap, but: no founders, no entity, no launch posts,
no press, no store listing, no indexed pricing.

### Comedy Evaluator Pro — Steve Roye (confirmed), ~23-year-old info-product
Former headlining comedian turned comedy educator; author of the "Killer
Stand-up Comedy System" (sold 20+ countries since ~2001), operator of an
interlinked site ecosystem (killerstandup.com, realfirststeps.com,
topcomedysecrets.com, sayitfunny.com). Invented CEP in **2003** ("patent
pending" per his own bio — no granted patent verified; treat as marketing).
Featured in the documentary "I Am Comic" (Slamdance 2010). Business model is
info-marketing funnel, not SaaS: trials → time-boxed one-time payments →
course upsell (CEP free for a year with course membership). Hostinger shared
hosting, WordPress-era SEO content. Heavily self-referential ecosystem
including a self-published "scam?" rebuttal page on his own domain. Solo,
maintained-but-dated; 2025–2026 development activity unverifiable.

### Implication
None of the three is a funded company, a team, or a capture-quality threat.
The two modern ones are anonymous indie builds with no visible traction; the
credible one is a 2003-era manual tool attached to a comedy course. The
serious threat vector remains a pivot by a funded adjacent player (Reap,
Datavault) — not these three.
