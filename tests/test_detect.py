import numpy as np

from laughstack.detect import detect_events, HeuristicDetector
from laughstack.models import EventKind
from conftest import SR, laugh_burst, applause_burst, quiet_room


def build_set(rng):
    """3 minutes of quiet room with two laughs and one applause break at
    known times. Returns (audio, truth) where truth is [(start, kind)]."""
    pieces = []
    truth = []
    t = 0.0

    def add(x):
        nonlocal t
        pieces.append(x)
        t += len(x) / SR

    add(quiet_room(20.0, rng=rng))
    truth.append((t, EventKind.LAUGH.value))
    add(laugh_burst(3.0, rng=rng))
    add(quiet_room(25.0, rng=rng))
    truth.append((t, EventKind.LAUGH.value))
    add(laugh_burst(2.0, mod_hz=4.5, rng=rng))
    add(quiet_room(30.0, rng=rng))
    truth.append((t, EventKind.APPLAUSE.value))
    add(applause_burst(4.0, rng=rng))
    add(quiet_room(20.0, rng=rng))
    return np.concatenate(pieces), truth


def test_detects_planted_events(rng):
    x, truth = build_set(rng)
    events = detect_events(x, SR)
    assert len(events) >= len(truth)
    for t0, kind in truth:
        hits = [e for e in events if e.start_s - 2.0 <= t0 <= e.end_s + 0.5]
        assert hits, f"missed planted event at {t0:.1f}s ({kind})"


def test_laugh_vs_applause_classification(rng):
    x, truth = build_set(rng)
    events = detect_events(x, SR)
    for t0, kind in truth:
        ev = min(events, key=lambda e: abs(e.start_s - t0))
        if kind == EventKind.LAUGH.value:
            assert ev.kind in (EventKind.LAUGH.value, EventKind.MIXED.value)
        else:
            assert ev.kind in (EventKind.APPLAUSE.value, EventKind.MIXED.value)


def test_quiet_room_yields_no_events(rng):
    x = quiet_room(120.0, rng=rng)
    events = detect_events(x, SR)
    assert events == []


def test_event_features_populated(rng):
    x, _ = build_set(rng)
    events = detect_events(x, SR)
    for e in events:
        assert e.end_s > e.start_s
        assert -80 < e.peak_dbfs <= 0
        assert e.energy > 0
        assert 0 <= e.confidence <= 1


def test_hysteresis_merges_breathing_laugh(rng):
    """A laugh with a brief dip should come out as one event, not two."""
    a = laugh_burst(2.0, rng=rng)
    dip = quiet_room(0.3, rng=rng)
    b = laugh_burst(2.0, mod_hz=5.5, rng=rng)
    x = np.concatenate([quiet_room(15.0, rng=rng), a, dip, b,
                        quiet_room(15.0, rng=rng)])
    events = detect_events(x, SR)
    laughs = [e for e in events if e.kind != EventKind.APPLAUSE.value]
    assert len(laughs) == 1
