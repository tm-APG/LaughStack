import numpy as np
import pytest

from laughstack.models import LaughEvent, JokeInstance, EventKind
from laughstack.metrics import (
    robust_z, attribute_stacked, normalize_events, set_metrics, joke_score,
    _longest_gap,
)
from laughstack.align import mark_stacked


def ev(start, end, kind=EventKind.LAUGH.value, peak=-20.0, energy=1.0):
    return LaughEvent(start_s=start, end_s=end, kind=kind,
                      peak_dbfs=peak, energy=energy)


def test_robust_z_ignores_outlier():
    vals = np.array([1.0, 1.1, 0.9, 1.05, 0.95, 100.0])
    z = robust_z(vals)
    # the outlier is huge in z, the cluster stays near 0
    assert abs(z[0]) < 1.5
    assert z[-1] > 10


def test_robust_z_zero_mad():
    assert np.all(robust_z(np.array([2.0, 2.0, 2.0])) == 0)


def test_normalize_events_fills_rel_fields():
    events = [ev(0, 1, peak=-30, energy=0.5), ev(10, 12, peak=-10, energy=5.0),
              ev(20, 21, peak=-25, energy=1.0)]
    normalize_events(events)
    assert all(e.rel_peak is not None and e.rel_energy is not None
               for e in events)
    assert events[1].rel_peak > events[0].rel_peak


def test_stacked_attribution_reduces_inherited_energy():
    """A 'tag' event sitting entirely inside the parent's decay should get
    excess_energy well below its raw energy."""
    sr_env = 50.0
    t = np.arange(int(10 * sr_env)) / sr_env
    env = np.zeros_like(t)
    # parent laugh at t=1..2 peaking then decaying with tau=0.6
    p0 = int(1.0 * sr_env)
    env[p0:] = np.exp(-(t[p0:] - 1.0) / 0.6)
    events = [ev(1.0, 2.5, energy=2.0), ev(3.0, 4.0, energy=0.5)]
    mark_stacked(events, stack_window_s=1.5)
    assert events[1].parent_index == 0
    attribute_stacked(events, env, sr_env)
    assert events[0].excess_energy == pytest.approx(2.0)
    assert events[1].excess_energy < 0.5 * events[1].energy


def test_non_stacked_event_keeps_energy():
    events = [ev(1.0, 2.0, energy=2.0), ev(30.0, 31.0, energy=0.5)]
    mark_stacked(events)
    env = np.zeros(50 * 60)
    attribute_stacked(events, env, 50.0)
    assert events[1].excess_energy == pytest.approx(0.5)


def test_set_metrics_basics():
    events = [ev(10, 13), ev(60, 62),
              ev(100, 104, kind=EventKind.APPLAUSE.value)]
    m = set_metrics(events, duration_s=300.0)
    assert m.n_events == 2                      # applause not a laugh
    assert m.total_laugh_s == pytest.approx(5.0)
    assert m.laughs_per_minute == pytest.approx(2 / 5.0)
    assert m.laugh_s_per_minute == pytest.approx(1.0)
    assert m.par_score == pytest.approx(100 * 5 / 300)
    assert m.applause_breaks == 1


def test_longest_silence():
    # gaps: 0-10 (10s), 13-100 (87s), 102-200 (98s) -> longest is the tail
    events = [ev(10, 13), ev(100, 102)]
    m = set_metrics(events, duration_s=200.0)
    assert m.longest_silence_s == pytest.approx(98.0)
    # and between-laugh gap wins when the tail is short
    m2 = set_metrics(events, duration_s=110.0)
    assert m2.longest_silence_s == pytest.approx(87.0)


def test_empty_set_metrics():
    m = set_metrics([], duration_s=120.0)
    assert m.n_events == 0
    assert m.longest_silence_s == pytest.approx(120.0)


def test_joke_score_silent_punchline():
    ji = JokeInstance(bit_id="x", setup_text="setup", punchline_text="punch",
                      punchline_end_s=10.0, events=[], position_in_set=0.5)
    s = joke_score(ji)
    assert s["scored"] == 0.0
    assert s["total_laugh_s"] == 0.0
    assert s["position"] == 0.5
