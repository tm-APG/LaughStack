"""Synthesized audio fixtures.

No real recordings in the repo — tests build the acoustic scenarios they
need: cal tones, laugh-like modulated noise bursts, applause-like flat
noise, exponential room decays.
"""

from __future__ import annotations

import numpy as np
import pytest

SR = 16000


def _rng():
    return np.random.default_rng(1234)


def laugh_burst(duration_s: float, sr: int = SR, mod_hz: float = 5.0,
                level: float = 0.3, rng=None) -> np.ndarray:
    """Crowd-laughter surrogate: band-limited noise, amplitude-modulated at
    syllabic rate, with a fast attack and exponential release."""
    rng = rng or _rng()
    n = int(duration_s * sr)
    noise = rng.standard_normal(n)
    # crude band-limit to speech band via FFT mask
    spec = np.fft.rfft(noise)
    f = np.fft.rfftfreq(n, 1 / sr)
    mask = (f > 300) & (f < 3000)
    band = np.fft.irfft(spec * mask, n)
    band /= np.max(np.abs(band)) + 1e-12
    t = np.arange(n) / sr
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * mod_hz * t)
    attack = np.minimum(1.0, t / 0.1)
    release = np.exp(-np.maximum(0.0, t - (duration_s - 0.5)) / 0.3)
    return level * band * mod * attack * release


def applause_burst(duration_s: float, sr: int = SR, level: float = 0.3,
                   rng=None) -> np.ndarray:
    """Applause surrogate: broadband noise, no syllabic modulation."""
    rng = rng or _rng()
    n = int(duration_s * sr)
    x = rng.standard_normal(n)
    x /= np.max(np.abs(x)) + 1e-12
    t = np.arange(n) / sr
    attack = np.minimum(1.0, t / 0.05)
    release = np.exp(-np.maximum(0.0, t - (duration_s - 0.4)) / 0.25)
    return level * x * attack * release


def quiet_room(duration_s: float, sr: int = SR, level: float = 0.005,
               rng=None) -> np.ndarray:
    rng = rng or _rng()
    return level * rng.standard_normal(int(duration_s * sr))


def cal_tone(duration_s: float = 3.0, sr: int = SR, freq: float = 1000.0,
             level: float = 0.25) -> np.ndarray:
    t = np.arange(int(duration_s * sr)) / sr
    return level * np.sin(2 * np.pi * freq * t)


@pytest.fixture
def rng():
    return _rng()


@pytest.fixture
def sr():
    return SR
