"""Audience-response detection.

Two-tier design:

* ``HeuristicDetector`` — pure DSP, no model downloads, runs anywhere.
  Frame-level score from band energy + envelope modulation (3–8 Hz laughter
  syllable rate) + spectral flatness (separates applause), hysteresis
  thresholding into events. Good enough for kit recordings where the
  audience mics are clean; the honest baseline to compare ML backends
  against.

* ML backends (optional installs) — registered by name via
  ``get_detector``. ``yamnet``/``sensevoice``/``whisper-at`` slots exist as
  documented integration points; each maps model posteriors into the same
  ``FrameScores`` shape so everything downstream is backend-agnostic.
  (TIC-TALK, 2026, runs Whisper-AT at 0.8 s stride in high-recall config
  and merges contiguous positive windows — same event-merge logic as here.)

Backends emit frame scores; ``detect_events`` turns frame scores into
``LaughEvent``s. Keep that split: the merge/hysteresis logic is where most
tuning happens and it must not be duplicated per backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

import numpy as np
from scipy import signal as sp_signal

from ..dsp import modulation_rate, spectral_flatness, decay_time
from ..models import LaughEvent, EventKind


@dataclass
class FrameScores:
    """Backend-agnostic frame-level output."""
    times: np.ndarray          # frame centers, seconds
    laugh: np.ndarray          # 0..1 per frame
    applause: np.ndarray       # 0..1 per frame
    hop_s: float


class Detector(Protocol):
    def score(self, x: np.ndarray, sr: int) -> FrameScores: ...


# --------------------------------------------------------------------------
# Heuristic backend
# --------------------------------------------------------------------------

class HeuristicDetector:
    """DSP-only laughter/applause scorer.

    Per analysis window (default 1.0 s, hop 0.25 s):
      * band RMS (300–3000 Hz) relative to a rolling noise floor —
        "is the room louder than its own baseline?"
      * modulation ratio in 3–8 Hz — "does it pulse like laughter?"
      * spectral flatness — high flatness + weak syllabic modulation
        reads as applause, not laughter.

    Scores are products of sigmoid-squashed cues, so every cue can veto.
    Thresholds are deliberately conservative on the laugh side: for kit
    work we prefer missing a chuckle to crediting HVAC.
    """

    def __init__(self, win_s: float = 1.0, hop_s: float = 0.25,
                 floor_percentile: float = 20.0,
                 energy_gate_db: float = 6.0):
        self.win_s = win_s
        self.hop_s = hop_s
        self.floor_percentile = floor_percentile
        self.energy_gate_db = energy_gate_db

    def score(self, x: np.ndarray, sr: int) -> FrameScores:
        x = np.asarray(x, dtype=np.float64)
        win = int(self.win_s * sr)
        hop = int(self.hop_s * sr)
        if len(x) < win:
            x = np.pad(x, (0, win - len(x)))
        n = 1 + (len(x) - win) // hop

        # band-limit once for energy; per-window work uses views
        nyq = sr / 2.0
        b, a = sp_signal.butter(4, [300 / nyq, min(3000 / nyq, 0.99)], btype="band")
        band = sp_signal.filtfilt(b, a, x)

        times = np.empty(n)
        rms_db = np.empty(n)
        mod = np.empty(n)
        flat = np.empty(n)
        for i in range(n):
            s = i * hop
            seg = x[s:s + win]
            bseg = band[s:s + win]
            times[i] = (s + win / 2) / sr
            rms_db[i] = 20 * np.log10(np.sqrt(np.mean(bseg ** 2)) + 1e-12)
            mod[i], _ = modulation_rate(seg, sr)
            flat[i] = spectral_flatness(seg, sr)

        # rolling noise floor: percentile of band RMS over a 60 s neighborhood
        floor = _rolling_percentile(rms_db, int(60 / self.hop_s) | 1,
                                    self.floor_percentile)
        elevation = rms_db - floor

        energy_cue = _sigmoid((elevation - self.energy_gate_db) / 3.0)
        mod_cue = _sigmoid((mod - 0.35) / 0.10)
        # applause: energy up, flat spectrum, weak syllabic modulation
        flat_cue = _sigmoid((flat - 0.25) / 0.08)
        no_mod_cue = _sigmoid((0.30 - mod) / 0.10)

        laugh = energy_cue * mod_cue
        applause = energy_cue * flat_cue * no_mod_cue
        return FrameScores(times=times, laugh=laugh, applause=applause,
                           hop_s=self.hop_s)


def _sigmoid(z: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _rolling_percentile(x: np.ndarray, win: int, q: float) -> np.ndarray:
    if len(x) <= win:
        return np.full_like(x, np.percentile(x, q))
    out = np.empty_like(x)
    half = win // 2
    for i in range(len(x)):
        lo = max(0, i - half)
        hi = min(len(x), i + half + 1)
        out[i] = np.percentile(x[lo:hi], q)
    return out


# --------------------------------------------------------------------------
# Backend registry
# --------------------------------------------------------------------------

def get_detector(name: str = "heuristic", **kwargs) -> Detector:
    if name == "heuristic":
        return HeuristicDetector(**kwargs)
    if name in ("yamnet", "sensevoice", "whisper-at"):
        raise NotImplementedError(
            f"Backend '{name}' is a documented integration point but not "
            f"bundled: it needs optional ML dependencies. Install the [ml] "
            f"extra and implement score() mapping model posteriors to "
            f"FrameScores (see docs/TECHNICAL_SPEC.md §Detection)."
        )
    raise ValueError(f"Unknown detector backend: {name!r}")


# --------------------------------------------------------------------------
# Frame scores -> events
# --------------------------------------------------------------------------

def detect_events(x: np.ndarray, sr: int,
                  detector: Optional[Detector] = None,
                  on_threshold: float = 0.5,
                  off_threshold: float = 0.3,
                  min_event_s: float = 0.4,
                  merge_gap_s: float = 0.4,
                  rt60_s: Optional[float] = None) -> list[LaughEvent]:
    """Full detection pass: score frames, hysteresis-threshold, merge,
    classify, and attach per-event acoustic features.

    Hysteresis (enter at ``on_threshold``, stay until below
    ``off_threshold``) keeps one laugh from fragmenting as it breathes.
    Events closer than ``merge_gap_s`` merge — contiguous positive windows
    belong to one response.
    """
    if detector is None:
        detector = HeuristicDetector()
    fs = detector.score(x, sr)
    combined = np.maximum(fs.laugh, fs.applause)

    spans = _hysteresis_spans(combined, on_threshold, off_threshold)
    spans = _merge_spans(spans, int(round(merge_gap_s / fs.hop_s)))

    events: list[LaughEvent] = []
    env = np.abs(x).astype(np.float64)
    # 50 Hz envelope for decay measurement
    dec = max(1, sr // 50)
    env50 = np.array([np.max(env[i:i + dec]) for i in range(0, len(env), dec)])
    sr50 = sr / dec

    for s_idx, e_idx in spans:
        start_s = float(fs.times[s_idx] - fs.hop_s / 2)
        end_s = float(fs.times[min(e_idx, len(fs.times) - 1)] + fs.hop_s / 2)
        if end_s - start_s < min_event_s:
            continue
        a = int(start_s * sr)
        bnd = int(end_s * sr)
        seg = x[a:bnd]
        if len(seg) == 0:
            continue
        peak_dbfs = float(20 * np.log10(np.max(np.abs(seg)) + 1e-12))
        energy = float(np.sum(seg.astype(np.float64) ** 2) / sr)
        laugh_mean = float(np.mean(fs.laugh[s_idx:e_idx + 1]))
        app_mean = float(np.mean(fs.applause[s_idx:e_idx + 1]))
        if laugh_mean >= 2 * app_mean:
            kind = EventKind.LAUGH.value
        elif app_mean >= 2 * laugh_mean:
            kind = EventKind.APPLAUSE.value
        else:
            kind = EventKind.MIXED.value

        # decay of the tail, measured on the 50 Hz envelope
        pa = int(start_s * sr50)
        pb = min(int(end_s * sr50) + int(2 * sr50), len(env50))
        d = None
        if pb - pa > 3:
            local = env50[pa:pb]
            d = decay_time(local, sr50, int(np.argmax(local)), rt60_s=rt60_s)

        events.append(LaughEvent(
            start_s=start_s, end_s=end_s, kind=kind,
            confidence=max(laugh_mean, app_mean),
            peak_dbfs=peak_dbfs, energy=energy, decay_s=d,
        ))
    return events


def _hysteresis_spans(score: np.ndarray, on: float, off: float) -> list[tuple[int, int]]:
    spans = []
    active = False
    start = 0
    for i, v in enumerate(score):
        if not active and v >= on:
            active, start = True, i
        elif active and v < off:
            spans.append((start, i - 1))
            active = False
    if active:
        spans.append((start, len(score) - 1))
    return spans


def _merge_spans(spans: list[tuple[int, int]], gap: int) -> list[tuple[int, int]]:
    if not spans:
        return []
    merged = [spans[0]]
    for s, e in spans[1:]:
        ps, pe = merged[-1]
        if s - pe <= gap:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged
