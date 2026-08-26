"""Align laugh events to the transcript: build JokeInstances.

Model: a laugh is caused by the last thing said before it started. We walk
events in time order; for each event, the transcript segment whose end is
closest *before* (or slightly overlapping) the laugh onset is the
punchline. Preceding segments back to the previous laugh (bounded) are the
setup.

Two things standard punchline-at-end framing gets wrong, handled here:

* Stacked tags — a new laugh starting while the previous one still rings.
  Detection may emit them merged or separate; ``mark_stacked`` links
  events that begin within ``stack_window_s`` of a previous event's end
  (or overlap it) so metrics can run the decay-envelope decomposition.
  (StandUp4AI hit the same issue: multiple laughs within one sentence,
  sometimes consecutive, break the one-punchline-per-sequence framing.)

* Silent punchlines — transcript segments that *look* like punchlines
  (followed by a pause, no laugh) are emitted as unscored JokeInstances
  when a set list is provided. A joke that died is a data point, not a
  gap in the data.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from .models import JokeInstance, LaughEvent, TranscriptSegment


def mark_stacked(events: list[LaughEvent], stack_window_s: float = 1.5) -> None:
    """Link each event to the previous one it landed on (in place).

    An event is 'stacked' when it starts before the previous event's
    acoustic tail has plausibly finished: within ``stack_window_s`` after
    the previous event's end, or overlapping it.
    """
    for i in range(1, len(events)):
        prev, cur = events[i - 1], events[i]
        if cur.start_s <= prev.end_s + stack_window_s:
            cur.parent_index = i - 1


def bit_id_for(text: str) -> str:
    """Stable id for a bit from its (normalized) punchline text."""
    norm = " ".join(text.lower().split())
    return hashlib.sha1(norm.encode()).hexdigest()[:12]


def find_silent_punchlines(events: list[LaughEvent],
                           transcript: list[TranscriptSegment],
                           min_pause_s: float = 2.0,
                           max_latency_s: float = 3.0) -> list[TranscriptSegment]:
    """Segments where the comic left room for a laugh and none came.

    A silent punchline is a segment followed by a speech pause of at least
    ``min_pause_s`` (the comic waited) with no event starting within
    ``max_latency_s`` of its end. Requires reasonably contiguous transcript
    segments (Whisper-style), where a gap means the comic stopped talking.
    """
    out: list[TranscriptSegment] = []
    for i, seg in enumerate(transcript):
        nxt = transcript[i + 1] if i + 1 < len(transcript) else None
        pause = (nxt.start_s - seg.end_s) if nxt else min_pause_s + 1.0
        if pause < min_pause_s:
            continue
        if any(seg.end_s - 0.25 <= e.start_s <= seg.end_s + max_latency_s
               for e in events):
            continue
        out.append(seg)
    return out


def align(events: list[LaughEvent],
          transcript: list[TranscriptSegment],
          set_duration_s: Optional[float] = None,
          max_latency_s: float = 3.0,
          min_pause_s: float = 2.0) -> list[JokeInstance]:
    """Attach each laugh event to its causing transcript segment.

    Events with no transcript segment ending within ``max_latency_s``
    before onset (crowd work off-mic, physical bits) still become
    JokeInstances with empty text — they happened; we just can't say why.

    Silent punchlines (a beat left for a laugh, none came) are emitted as
    unscored JokeInstances — they stay in every table (house rule 5).
    """
    jokes: list[JokeInstance] = []
    if not transcript and not events:
        return jokes

    mark_stacked(events)
    silent_segs = find_silent_punchlines(events, transcript,
                                         min_pause_s=min_pause_s,
                                         max_latency_s=max_latency_s)
    silent_ends = [s.end_s for s in silent_segs]

    used_events: set[int] = set()
    for ei, ev in enumerate(events):
        # find punchline: latest segment ending at/just before laugh onset
        punch: Optional[TranscriptSegment] = None
        for seg in transcript:
            if seg.end_s <= ev.start_s + 0.25:  # allow slight overlap
                if punch is None or seg.end_s > punch.end_s:
                    punch = seg
        if punch is not None and (ev.start_s - punch.end_s) > max_latency_s:
            punch = None

        if punch is None:
            jokes.append(JokeInstance(
                bit_id=f"unaligned-{ei}", setup_text="", punchline_text="",
                punchline_end_s=ev.start_s, events=[ev], latency_s=None,
                position_in_set=_position(ev.start_s, set_duration_s),
            ))
            used_events.add(ei)
            continue

        setup = _setup_text(transcript, punch, events, ei, silent_ends)
        ji = JokeInstance(
            bit_id=bit_id_for(punch.text),
            setup_text=setup,
            punchline_text=punch.text,
            punchline_end_s=punch.end_s,
            events=[ev],
            latency_s=max(0.0, ev.start_s - punch.end_s),
            position_in_set=_position(punch.end_s, set_duration_s),
        )
        # fold stacked children of this event into the same instance
        j = ei + 1
        while j < len(events) and events[j].parent_index == j - 1:
            # only fold if no new transcript segment intervenes
            if any(punch.end_s < s.end_s <= events[j].start_s for s in transcript):
                break
            ji.events.append(events[j])
            used_events.add(j)
            j += 1
        used_events.add(ei)
        jokes.append(ji)

    # de-duplicate: an event may appear in only one instance
    seen: set[int] = set()
    deduped: list[JokeInstance] = []
    for ji in jokes:
        fresh = [e for e in ji.events if id(e) not in seen]
        for e in fresh:
            seen.add(id(e))
        if fresh:
            ji.events = fresh
            deduped.append(ji)

    # silent punchlines: unscored instances, kept in every table
    scored_punchlines = {ji.punchline_end_s for ji in deduped}
    for seg in silent_segs:
        if seg.end_s in scored_punchlines:
            continue
        # setup bounded by the previous response boundary (laugh end or
        # another punchline) so a neighboring joke's text never leaks in
        boundary = max(
            [e.end_s for e in events if e.end_s <= seg.start_s] +
            [p for p in scored_punchlines if p < seg.start_s] + [0.0])
        setup = " ".join(s.text for s in transcript
                         if boundary <= s.start_s and s.end_s <= seg.start_s)
        deduped.append(JokeInstance(
            bit_id=bit_id_for(seg.text), setup_text=setup,
            punchline_text=seg.text, punchline_end_s=seg.end_s,
            events=[], latency_s=None,
            position_in_set=_position(seg.end_s, set_duration_s),
        ))
    deduped.sort(key=lambda ji: ji.punchline_end_s)
    return deduped


def _setup_text(transcript: list[TranscriptSegment],
                punch: TranscriptSegment,
                events: list[LaughEvent], ei: int,
                silent_ends: list[float] = (),
                max_setup_segments: int = 4) -> str:
    """Segments between the previous response boundary and the punchline.

    The boundary is the previous laugh's end OR the end of the latest
    silent punchline before this one — so a bit that died doesn't leak its
    text into the next joke's setup."""
    prev_end = events[ei - 1].end_s if ei > 0 else 0.0
    for t in silent_ends:
        if prev_end < t < punch.end_s - 0.01:
            prev_end = t
    parts = [s.text for s in transcript
             if prev_end <= s.start_s and s.end_s < punch.end_s]
    return " ".join(parts[-max_setup_segments:])


def _position(t: float, duration: Optional[float]) -> Optional[float]:
    if not duration or duration <= 0:
        return None
    return min(1.0, max(0.0, t / duration))
