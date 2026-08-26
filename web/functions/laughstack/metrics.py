"""Scoring: per-event normalization, stacked-tag energy attribution,
and whole-set metrics.

House rules (violating any of these silently corrupts output):

* median/MAD, never mean/SD — one applause break otherwise drags every
  z-score in the set.
* normalize within the session first — a laugh is judged against *that
  room that night*. Raw dB across venues is measuring the PA, not the
  joke. Cross-session comparison happens on the normalized numbers.
* stacked tags get excess energy, not raw energy — a tag landing on a
  still-ringing laugh inherits the parent's energy and would otherwise
  always score as a killer.
* silence is data — set metrics report the longest silence and jokes
  with no events stay in the per-bit tables.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .dsp import decompose_stacked
from .models import LaughEvent, JokeInstance, SetMetrics, EventKind


def robust_z(values: np.ndarray) -> np.ndarray:
    """(x - median) / (1.4826 * MAD). Zero-MAD degrades to zeros."""
    values = np.asarray(values, dtype=np.float64)
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    if mad == 0:
        return np.zeros_like(values)
    return (values - med) / (1.4826 * mad)


def attribute_stacked(events: list[LaughEvent], env: np.ndarray,
                      sr_env: float) -> None:
    """Fill ``excess_energy`` for stacked events (in place).

    ``env`` is the session amplitude envelope at ``sr_env`` Hz (50 Hz is
    plenty). Events must already have ``parent_index`` set (align.mark_stacked).
    Non-stacked events get excess_energy = energy.
    """
    for i, ev in enumerate(events):
        if ev.parent_index is None:
            ev.excess_energy = ev.energy
            continue
        parent = events[ev.parent_index]
        p_peak = int(np.clip(_peak_index(env, sr_env, parent), 0, len(env) - 1))
        a = int(ev.start_s * sr_env)
        b = min(int(ev.end_s * sr_env), len(env))
        if b <= a or a <= p_peak:
            ev.excess_energy = ev.energy
            continue
        d = decompose_stacked(env, sr_env, p_peak, a, b)
        # scale the event's calibrated energy by the excess ratio, so the
        # attribution logic (envelope domain) and the energy metric
        # (waveform domain) stay consistent
        ev.excess_energy = ev.energy * d.excess_ratio


def _peak_index(env: np.ndarray, sr_env: float, ev: LaughEvent) -> int:
    a = int(ev.start_s * sr_env)
    b = max(a + 1, min(int(ev.end_s * sr_env), len(env)))
    return a + int(np.argmax(env[a:b]))


def normalize_events(events: list[LaughEvent]) -> None:
    """Robust-z each event's peak and (excess) energy against the session
    (in place). This is the number that travels across venues."""
    if not events:
        return
    peaks = np.array([e.peak_dbfs for e in events])
    energies = np.array([
        e.excess_energy if e.excess_energy is not None else e.energy
        for e in events
    ])
    zp = robust_z(peaks)
    # energy is heavy-tailed; z on log-energy
    ze = robust_z(np.log10(energies + 1e-12))
    for e, a, b in zip(events, zp, ze):
        e.rel_peak = float(a)
        e.rel_energy = float(b)


def set_metrics(events: list[LaughEvent], duration_s: float) -> SetMetrics:
    m = SetMetrics(duration_s=duration_s)
    laughs = [e for e in events if e.kind in (EventKind.LAUGH.value,
                                              EventKind.MIXED.value)]
    m.n_events = len(laughs)
    m.total_laugh_s = sum(e.duration_s for e in laughs)
    minutes = duration_s / 60.0 if duration_s > 0 else 0.0
    if minutes > 0:
        m.laughs_per_minute = m.n_events / minutes
        m.laugh_s_per_minute = m.total_laugh_s / minutes
    # Comedy Evaluator Pro framing: PAR = % of stage time that is laughter;
    # their headliner benchmark of 18 s/min corresponds to PAR 30.
    m.par_score = 100.0 * m.total_laugh_s / duration_s if duration_s > 0 else 0.0
    if laughs:
        m.median_peak_dbfs = float(np.median([e.peak_dbfs for e in laughs]))
        m.median_event_duration_s = float(np.median([e.duration_s for e in laughs]))
    m.applause_breaks = sum(1 for e in events
                            if e.kind in (EventKind.APPLAUSE.value,
                                          EventKind.MIXED.value))
    m.longest_silence_s = _longest_gap(events, duration_s)
    return m


def _longest_gap(events: list[LaughEvent], duration_s: float) -> float:
    if not events:
        return duration_s
    edges = [0.0]
    for e in sorted(events, key=lambda e: e.start_s):
        edges.append(e.start_s)
        edges.append(e.end_s)
    edges.append(duration_s)
    gaps = [edges[i + 1] - edges[i] for i in range(0, len(edges) - 1, 2)]
    return float(max(gaps)) if gaps else 0.0


def joke_score(ji: JokeInstance) -> dict[str, Optional[float]]:
    """Per-instance summary used by reports and A/B comparison."""
    if not ji.events:
        return {"total_laugh_s": 0.0, "peak_rel": None, "energy_rel": None,
                "latency_s": None, "position": ji.position_in_set,
                "scored": 0.0}
    peak_rel = max((e.rel_peak for e in ji.events
                    if e.rel_peak is not None), default=None)
    energy_rel = max((e.rel_energy for e in ji.events
                      if e.rel_energy is not None), default=None)
    return {
        "total_laugh_s": ji.total_laugh_s,
        "peak_rel": peak_rel,
        "energy_rel": energy_rel,
        "latency_s": ji.latency_s,
        "position": ji.position_in_set,
        "scored": 1.0,
    }
