"""Cross-session comparison: match the same joke across performances and
compare deliveries on within-room-normalized numbers.

This is the piece no consumer app does: A/B of the same joke across
nights, controlled for the room. Matching is text-based (the same bit is
rarely word-identical night to night — comics tighten wording), so we use
token-set similarity with a threshold rather than exact bit_id equality.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import JokeInstance, Session
from .metrics import joke_score

_WORD_RE = re.compile(r"[a-z']+")
_STOPWORDS = frozenset(
    "the a an and or but so i you he she it we they to of in on at is was "
    "are were be been am do did done have has had my your his her its our "
    "their this that these those with for not no yes just like know gonna "
    "got get".split()
)


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower())
            if w not in _STOPWORDS and len(w) > 1}


def joke_similarity(a: str, b: str) -> float:
    """Jaccard similarity on content tokens of setup+punchline text."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class MatchedJoke:
    """One joke tracked across n sessions."""
    canonical_text: str
    instances: list[tuple[str, JokeInstance]] = field(default_factory=list)
    # (session_id, instance) pairs

    def table(self) -> list[dict]:
        rows = []
        for sid, ji in self.instances:
            row = {"session_id": sid,
                   "punchline": ji.punchline_text[:80],
                   **joke_score(ji)}
            rows.append(row)
        return rows


def match_jokes(sessions: list[Session],
                min_similarity: float = 0.5) -> list[MatchedJoke]:
    """Greedy cross-session matching of joke instances by text similarity.

    Instances from different sessions whose setup+punchline token sets
    overlap ≥ ``min_similarity`` are the same joke. Greedy from the
    longest text down; good enough for tens of jokes per set — replace
    with proper clustering if sets get pathological.
    """
    pool: list[tuple[str, JokeInstance, str]] = []
    for s in sessions:
        for ji in s.jokes:
            text = f"{ji.setup_text} {ji.punchline_text}".strip()
            if _tokens(text):
                pool.append((s.session_id, ji, text))

    pool.sort(key=lambda t: -len(t[2]))
    matched: list[MatchedJoke] = []
    taken = [False] * len(pool)
    for i, (sid, ji, text) in enumerate(pool):
        if taken[i]:
            continue
        taken[i] = True
        group = MatchedJoke(canonical_text=text, instances=[(sid, ji)])
        for j in range(i + 1, len(pool)):
            if taken[j]:
                continue
            sid2, ji2, text2 = pool[j]
            # allow same-session matches too (repeated callback) but
            # prioritize cross-session pairs by not requiring distinct sids
            if joke_similarity(text, text2) >= min_similarity:
                taken[j] = True
                group.instances.append((sid2, ji2))
        if len(group.instances) > 1:
            matched.append(group)
    return matched


@dataclass
class ABResult:
    joke_text: str
    a_session: str
    b_session: str
    delta_total_laugh_s: float
    delta_peak_rel: Optional[float]
    delta_energy_rel: Optional[float]
    delta_latency_s: Optional[float]
    position_confound: Optional[float]   # |pos_a - pos_b|; > ~0.25 = beware
    verdict: str


def ab_compare(m: MatchedJoke, a_session: str, b_session: str) -> Optional[ABResult]:
    """Head-to-head of one joke between two sessions, on normalized numbers.

    The comparison uses rel_* (within-room robust z), so "B beat A" means
    the joke did better *relative to its own room* — the only fair basis
    when Friday-late and Tuesday-mic rooms differ.
    """
    a = _pick_instance(m, a_session)
    b = _pick_instance(m, b_session)
    if a is None or b is None:
        return None
    sa, sb = joke_score(a), joke_score(b)

    d_peak = _delta(sa["peak_rel"], sb["peak_rel"])
    d_energy = _delta(sa["energy_rel"], sb["energy_rel"])
    d_latency = _delta(sa["latency_s"], sb["latency_s"])
    d_total = sb["total_laugh_s"] - sa["total_laugh_s"]
    pos_conf = None
    if sa["position"] is not None and sb["position"] is not None:
        pos_conf = abs(sa["position"] - sb["position"])

    if d_energy is None:
        verdict = "insufficient data"
    elif abs(d_energy) < 0.5:
        verdict = "no meaningful difference"
    else:
        better = b_session if d_energy > 0 else a_session
        verdict = f"{better} delivery stronger (Δ energy z = {d_energy:+.2f})"
        if pos_conf is not None and pos_conf > 0.25:
            verdict += " — CAUTION: set-position differs materially"
    return ABResult(
        joke_text=m.canonical_text[:120],
        a_session=a_session, b_session=b_session,
        delta_total_laugh_s=d_total,
        delta_peak_rel=d_peak, delta_energy_rel=d_energy,
        delta_latency_s=d_latency,
        position_confound=pos_conf, verdict=verdict,
    )


def _pick_instance(m: MatchedJoke, session_id: str) -> Optional[JokeInstance]:
    """The session's best instance in a group: a scored one over a silent
    one (a group can hold both when matching folds neighbors together)."""
    candidates = [ji for sid, ji in m.instances if sid == session_id]
    if not candidates:
        return None
    scored = [ji for ji in candidates if ji.events]
    return scored[0] if scored else candidates[0]


def _delta(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    return b - a
