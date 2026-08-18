"""Social clip candidates: turn the scored set into a ranked shortlist of
cut points for TikTok/Reels/Shorts.

This is the social-media bridge: the live-room data picks the clip, the
platform's engagement data on that clip (views, completion, likes) can be
logged back per bit_id, giving a second response signal per joke —
live room + online audience. See docs/COMPETITORS.md for how competitors
handle (or don't handle) this.

Selection heuristic:
* rank jokes by normalized energy (rel), tie-break on total laugh seconds
* clip = setup start (padded) → end of last laugh (padded); duration
  clamped to the platform window
* skip unaligned events (no transcript = no setup = clip starts mid-laugh)

Output: JSON manifest + ready-to-run ffmpeg commands. We do not auto-post;
the performer owns publication (see confidentiality terms in the spec).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from .models import Session
from .metrics import joke_score


@dataclass
class ClipCandidate:
    rank: int
    bit_id: str
    start_s: float
    end_s: float
    duration_s: float
    punchline: str
    score: float
    total_laugh_s: float
    ffmpeg_cmd: str


def clip_candidates(session: Session, source_media: str,
                    max_clips: int = 5,
                    min_duration_s: float = 8.0,
                    max_duration_s: float = 90.0,
                    pre_pad_s: float = 1.0,
                    post_pad_s: float = 1.5) -> list[ClipCandidate]:
    scored = []
    for ji in session.jokes:
        if not ji.events or not ji.punchline_text:
            continue
        s = joke_score(ji)
        rank_key = (s["energy_rel"] if s["energy_rel"] is not None else -99.0,
                    s["total_laugh_s"])
        scored.append((rank_key, ji, s))
    scored.sort(key=lambda t: t[0], reverse=True)

    out: list[ClipCandidate] = []
    for rank, (key, ji, s) in enumerate(scored[:max_clips], start=1):
        first_ev = min(ji.events, key=lambda e: e.start_s)
        last_ev = max(ji.events, key=lambda e: e.end_s)
        # start at the setup if we can estimate it: back off from the
        # punchline by a rough spoken-duration of the setup text
        setup_words = len(ji.setup_text.split())
        setup_dur = min(30.0, setup_words / 2.5)  # ~150 wpm
        start = max(0.0, ji.punchline_end_s - setup_dur - pre_pad_s)
        end = last_ev.end_s + post_pad_s
        if end - start > max_duration_s:
            start = max(0.0, end - max_duration_s)
        if end - start < min_duration_s:
            end = start + min_duration_s
        clip_name = f"clip_{rank:02d}_{ji.bit_id}.mp4"
        cmd = (f"ffmpeg -y -ss {start:.2f} -to {end:.2f} -i {source_media!r} "
               f"-c:v libx264 -c:a aac -movflags +faststart {clip_name!r}")
        out.append(ClipCandidate(
            rank=rank, bit_id=ji.bit_id, start_s=round(start, 2),
            end_s=round(end, 2), duration_s=round(end - start, 2),
            punchline=ji.punchline_text[:120],
            score=s["energy_rel"] if s["energy_rel"] is not None else 0.0,
            total_laugh_s=round(ji.total_laugh_s, 2),
            ffmpeg_cmd=cmd,
        ))
    return out


def write_manifest(clips: list[ClipCandidate], path: str | Path) -> None:
    Path(path).write_text(json.dumps([asdict(c) for c in clips], indent=2))


# --------------------------------------------------------------------------
# Engagement join-back (phase 2 of the social bridge)
# --------------------------------------------------------------------------

@dataclass
class ClipEngagement:
    """Platform stats for one published clip, keyed to the bit it came from.

    Entered manually (or via platform APIs later). Joining this to the
    live-room score per bit_id gives two independent audience reads on the
    same material. Divergence is signal: a bit that kills live but dies
    online often depends on room context; a bit that travels online but is
    mid live may be under-set-up in the room.
    """
    bit_id: str
    platform: str            # tiktok | youtube_shorts | instagram_reels
    url: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    avg_watch_ratio: Optional[float] = None   # completion rate, 0..1
    posted_date: str = ""


def engagement_report(session: Session,
                      engagements: list[ClipEngagement]) -> list[dict]:
    """Join live scores with online engagement per bit."""
    live = {}
    for ji in session.jokes:
        s = joke_score(ji)
        live[ji.bit_id] = {
            "punchline": ji.punchline_text[:80],
            "live_energy_rel": s["energy_rel"],
            "live_total_laugh_s": s["total_laugh_s"],
        }
    rows = []
    for e in engagements:
        row = {"bit_id": e.bit_id, "platform": e.platform,
               "views": e.views, "likes": e.likes,
               "avg_watch_ratio": e.avg_watch_ratio,
               **live.get(e.bit_id, {"punchline": "(bit not in session)",
                                     "live_energy_rel": None,
                                     "live_total_laugh_s": None})}
        rows.append(row)
    return rows
