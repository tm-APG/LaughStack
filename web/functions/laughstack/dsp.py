"""Signal-processing primitives.

These are the pieces the detection and metrics layers are built from:

* ``detect_cal_tone``     — find the 1 kHz kit calibration tone, giving a
                            shared time origin and level reference per mic.
* ``gcc_phat``            — inter-mic time-delay estimation (mic geometry QC,
                            stage/audience separation).
* ``NLMSCanceller``       — adaptive stage-bleed canceller for the audience
                            mics, with a *freeze mask* so it never adapts
                            during laughter (adapting during a laugh would
                            teach the filter to cancel the very signal we
                            are trying to measure).
* ``modulation_rate``     — envelope-modulation spectrum; crowd laughter
                            carries strong 3–8 Hz syllabic modulation that
                            speech babble and HVAC noise do not.
* ``band_coherence``      — magnitude-squared coherence between audience
                            mics; a room-wide laugh is coherent across mics,
                            one chatty table is not.
* ``estimate_rt60``       — Schroeder backward integration on a balloon pop
                            or swept-sine IR captured at load-in.
* ``decay_time``          — -20 dB decay time of a laugh tail, optionally
                            RT60-corrected so we measure the joke, not the
                            venue.
* ``decompose_stacked``   — energy of a tag's laugh measured *above* the
                            extrapolated decay envelope of the parent laugh.
                            Without this every tag on a still-ringing room
                            inherits the parent's energy and scores as a
                            killer.

Pure numpy/scipy; no ML dependencies. All functions take mono float arrays
in [-1, 1] unless stated otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import signal


# --------------------------------------------------------------------------
# Envelope helpers
# --------------------------------------------------------------------------

def amplitude_envelope(x: np.ndarray, sr: int, cutoff_hz: float = 20.0) -> np.ndarray:
    """Low-passed magnitude envelope, same length as x."""
    env = np.abs(x).astype(np.float64)
    nyq = sr / 2.0
    b, a = signal.butter(2, min(cutoff_hz / nyq, 0.99), btype="low")
    return signal.filtfilt(b, a, env)


def frame_rms_db(x: np.ndarray, sr: int, frame_s: float = 0.05,
                 hop_s: float = 0.025) -> tuple[np.ndarray, np.ndarray]:
    """Frame-wise RMS in dBFS. Returns (times, rms_db)."""
    frame = max(1, int(frame_s * sr))
    hop = max(1, int(hop_s * sr))
    n = 1 + max(0, (len(x) - frame) // hop)
    times = np.arange(n) * hop_s + frame_s / 2.0
    rms = np.empty(n)
    for i in range(n):
        seg = x[i * hop:i * hop + frame]
        rms[i] = np.sqrt(np.mean(seg * seg) + 1e-20)
    return times, 20.0 * np.log10(rms + 1e-12)


# --------------------------------------------------------------------------
# Calibration tone
# --------------------------------------------------------------------------

@dataclass
class CalTone:
    offset_s: float          # onset of the tone in this recording
    duration_s: float
    level_dbfs: float
    freq_hz: float


def detect_cal_tone(x: np.ndarray, sr: int, freq_hz: float = 1000.0,
                    search_s: float = 120.0, min_duration_s: float = 1.0,
                    rel_threshold_db: float = 12.0) -> Optional[CalTone]:
    """Find the kit calibration tone near the start of a recording.

    The kit plays a steady sine (default 1 kHz) through the room at soundcheck.
    Every mic that hears it gets a shared time origin (sample-accurate enough
    for alignment after GCC-PHAT refinement) and a level reference so gains
    are comparable across mics and across nights.

    Strategy: STFT; per frame, compare energy in a narrow band around
    ``freq_hz`` to total frame energy. The tone is where the narrowband
    dominates (within ``rel_threshold_db`` of total) for at least
    ``min_duration_s``.
    """
    n_search = min(len(x), int(search_s * sr))
    seg = x[:n_search].astype(np.float64)
    frame = int(0.05 * sr)
    hop = frame // 2
    if len(seg) < frame:
        return None

    f, t, Z = signal.stft(seg, fs=sr, nperseg=frame, noverlap=frame - hop,
                          boundary=None, padded=False)
    power = np.abs(Z) ** 2                              # (freq, time)
    tone_sel = np.abs(f - freq_hz) <= 50.0              # ±50 Hz around target
    tone_db = 10.0 * np.log10(power[tone_sel].sum(axis=0) + 1e-20)
    total_db = 10.0 * np.log10(power.sum(axis=0) + 1e-20)

    # Tone frames: narrowband within rel_threshold of total (i.e. tone dominates)
    dominance = tone_db - total_db          # ~0 dB when frame is pure tone
    is_tone = dominance > -rel_threshold_db
    # also require the frame to be well above the quietest frames (not silence)
    is_tone &= total_db > np.median(total_db)

    min_frames = int(min_duration_s * sr / hop)
    run_start, run_len = _longest_run(is_tone)
    if run_len < min_frames:
        return None

    start_sample = run_start * hop
    dur_s = run_len * hop / sr
    tone_seg = seg[start_sample:start_sample + run_len * hop]
    level = 20.0 * np.log10(np.sqrt(np.mean(tone_seg ** 2)) + 1e-12)
    return CalTone(offset_s=start_sample / sr, duration_s=dur_s,
                   level_dbfs=level, freq_hz=freq_hz)


def _longest_run(mask: np.ndarray) -> tuple[int, int]:
    """(start, length) of the longest True run in a boolean array."""
    best_start = best_len = 0
    cur_start = cur_len = 0
    for i, v in enumerate(mask):
        if v:
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_start, best_len = cur_start, cur_len
        else:
            cur_len = 0
    return best_start, best_len


# --------------------------------------------------------------------------
# Inter-mic alignment
# --------------------------------------------------------------------------

def gcc_phat(a: np.ndarray, b: np.ndarray, sr: int,
             max_delay_s: float = 0.5) -> tuple[float, float]:
    """Generalized cross-correlation with phase transform.

    Returns (delay_s, peak) where delay_s > 0 means ``b`` lags ``a``.
    PHAT weighting whitens the spectrum so the estimate keys on timing, not
    on whichever loud sound dominates — robust in reverberant rooms.
    """
    n = len(a) + len(b)
    nfft = 1 << (n - 1).bit_length()
    A = np.fft.rfft(a, nfft)
    B = np.fft.rfft(b, nfft)
    R = A * np.conj(B)
    R /= (np.abs(R) + 1e-15)
    cc = np.fft.irfft(R, nfft)
    max_shift = min(int(max_delay_s * sr), nfft // 2 - 1)
    cc = np.concatenate((cc[-max_shift:], cc[:max_shift + 1]))
    shift = np.argmax(np.abs(cc)) - max_shift
    return -shift / sr, float(np.abs(cc).max())


def band_coherence(a: np.ndarray, b: np.ndarray, sr: int,
                   band_hz: tuple[float, float] = (300.0, 3000.0),
                   nperseg: Optional[int] = None) -> float:
    """Mean magnitude-squared coherence between two mics in a band.

    A room-wide response (laugh, applause) is coherent across audience mics;
    a conversation at one table, glassware, or a mic-local rumble is not.
    """
    if nperseg is None:
        nperseg = min(len(a), 2048)
    f, cxy = signal.coherence(a, b, fs=sr, nperseg=nperseg)
    sel = (f >= band_hz[0]) & (f <= band_hz[1])
    if not np.any(sel):
        return 0.0
    return float(np.mean(cxy[sel]))


# --------------------------------------------------------------------------
# Stage-bleed cancellation (NLMS with freeze mask)
# --------------------------------------------------------------------------

class NLMSCanceller:
    """Normalized LMS adaptive canceller.

    Reference input: the stage/PA feed (what the comic's mic hears).
    Primary input: an audience mic (comic bleed + audience response).
    Output: audience mic minus the adaptively-estimated bleed.

    The critical detail is the *freeze mask*: while a laugh (or any
    audience event) is happening, adaptation is frozen. If we let the
    filter adapt during a laugh, the laugh is "noise" from the filter's
    point of view and it will happily learn to remove correlated parts of
    it — silently deflating every measurement. The filter still *applies*
    during the freeze; it just stops learning.
    """

    def __init__(self, n_taps: int = 256, mu: float = 0.5, eps: float = 1e-6):
        self.n_taps = n_taps
        self.mu = mu
        self.eps = eps
        self.w = np.zeros(n_taps)

    def process(self, primary: np.ndarray, reference: np.ndarray,
                freeze_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Return primary with the reference-correlated component removed.

        ``freeze_mask`` is a boolean array (same length): True = freeze
        adaptation at that sample.
        """
        n = min(len(primary), len(reference))
        primary = primary[:n].astype(np.float64)
        reference = reference[:n].astype(np.float64)
        if freeze_mask is None:
            freeze_mask = np.zeros(n, dtype=bool)
        out = np.empty(n)
        buf = np.zeros(self.n_taps)
        w = self.w
        for i in range(n):
            buf[1:] = buf[:-1]
            buf[0] = reference[i]
            y = w @ buf
            e = primary[i] - y
            out[i] = e
            if not freeze_mask[i]:
                norm = buf @ buf + self.eps
                w = w + (self.mu / norm) * e * buf
        self.w = w
        return out


def block_nlms_cancel(primary: np.ndarray, reference: np.ndarray, sr: int,
                      freeze_mask: Optional[np.ndarray] = None,
                      n_taps: int = 256, mu: float = 0.5,
                      block_s: float = 1.0) -> np.ndarray:
    """Convenience wrapper: frequency-agnostic block processing of the
    sample-wise NLMS (kept simple; for long files run offline, not live)."""
    c = NLMSCanceller(n_taps=n_taps, mu=mu)
    return c.process(primary, reference, freeze_mask)


# --------------------------------------------------------------------------
# Laughter cues
# --------------------------------------------------------------------------

def modulation_rate(x: np.ndarray, sr: int,
                    mod_band_hz: tuple[float, float] = (3.0, 8.0),
                    carrier_band_hz: tuple[float, float] = (300.0, 3000.0),
                    ) -> tuple[float, float]:
    """Envelope-modulation analysis of a segment.

    Crowd laughter is a chorus of "ha-ha-ha" bursts: strong amplitude
    modulation of the 0.3–3 kHz band at roughly syllabic rate (3–8 Hz).
    Speech has modulation there too but from a single source it is far less
    stationary; applause modulates much faster (individual claps ~ >10 Hz
    density) and HVAC/rumble barely modulates at all.

    Returns (mod_ratio, peak_mod_hz):
      mod_ratio  — fraction of envelope-spectrum power in ``mod_band_hz``
                   relative to 0.5–20 Hz total.
      peak_mod_hz — location of the strongest modulation component.
    """
    if len(x) < sr // 4:
        return 0.0, 0.0
    nyq = sr / 2.0
    lo = max(carrier_band_hz[0] / nyq, 1e-4)
    hi = min(carrier_band_hz[1] / nyq, 0.99)
    b, a = signal.butter(4, [lo, hi], btype="band")
    band = signal.filtfilt(b, a, x.astype(np.float64))
    env = amplitude_envelope(band, sr, cutoff_hz=30.0)
    # decimate envelope to ~100 Hz for the modulation FFT
    dec = max(1, sr // 100)
    env_d = env[::dec]
    esr = sr / dec
    env_d = env_d - np.mean(env_d)
    if np.allclose(env_d, 0):
        return 0.0, 0.0
    f, pxx = signal.welch(env_d, fs=esr, nperseg=min(len(env_d), 256))
    total_sel = (f >= 0.5) & (f <= 20.0)
    band_sel = (f >= mod_band_hz[0]) & (f <= mod_band_hz[1])
    total = np.sum(pxx[total_sel]) + 1e-20
    ratio = float(np.sum(pxx[band_sel]) / total)
    peak_hz = float(f[total_sel][np.argmax(pxx[total_sel])]) if np.any(total_sel) else 0.0
    return ratio, peak_hz


def spectral_flatness(x: np.ndarray, sr: int, nperseg: int = 1024) -> float:
    """Wiener entropy over 200 Hz–6 kHz. Applause ≈ broadband noise (high),
    laughter is voiced-ish (mid), a held vocal note is tonal (low)."""
    f, pxx = signal.welch(x, fs=sr, nperseg=min(len(x), nperseg))
    sel = (f >= 200) & (f <= 6000)
    p = pxx[sel] + 1e-20
    return float(np.exp(np.mean(np.log(p))) / np.mean(p))


# --------------------------------------------------------------------------
# Room acoustics
# --------------------------------------------------------------------------

def estimate_rt60(ir: np.ndarray, sr: int,
                  fit_range_db: tuple[float, float] = (-5.0, -25.0)) -> float:
    """RT60 from an impulse response (balloon pop / clap / swept-sine IR)
    via Schroeder backward integration, extrapolating a T20 fit to 60 dB.

    Sixty seconds with a balloon at load-in turns every decay-time metric
    from "measuring the venue" into "measuring the joke".
    """
    ir = ir.astype(np.float64)
    # trim to the peak (direct sound)
    start = int(np.argmax(np.abs(ir)))
    ir = ir[start:]
    energy = ir ** 2
    sch = np.cumsum(energy[::-1])[::-1]
    sch_db = 10.0 * np.log10(sch / (sch[0] + 1e-20) + 1e-20)
    hi, lo = fit_range_db
    idx_hi = np.argmax(sch_db <= hi)
    idx_lo = np.argmax(sch_db <= lo)
    if idx_lo <= idx_hi:
        return 0.0
    t = np.arange(len(sch_db)) / sr
    coeffs = np.polyfit(t[idx_hi:idx_lo], sch_db[idx_hi:idx_lo], 1)
    slope = coeffs[0]  # dB/s, negative
    if slope >= 0:
        return 0.0
    return float(-60.0 / slope)


def decay_time(env: np.ndarray, sr_env: float, peak_idx: int,
               drop_db: float = 20.0, rt60_s: Optional[float] = None) -> Optional[float]:
    """Time for the envelope to fall ``drop_db`` below its peak, measured
    from the peak. If ``rt60_s`` is given, subtract the room's contribution
    (energy decay of the room alone over the same dB drop) so numbers are
    comparable across venues. Returns None if the envelope never falls far
    enough before the array ends (e.g. a stacked tag re-excites the room).
    """
    peak = env[peak_idx]
    if peak <= 0:
        return None
    target = peak * 10 ** (-drop_db / 20.0)
    below = np.nonzero(env[peak_idx:] <= target)[0]
    if len(below) == 0:
        return None
    t = below[0] / sr_env
    if rt60_s is not None and rt60_s > 0:
        room_t = rt60_s * (drop_db / 60.0)
        t = max(0.0, t - room_t)
    return float(t)


# --------------------------------------------------------------------------
# Stacked-tag decomposition
# --------------------------------------------------------------------------

@dataclass
class StackedDecomposition:
    tag_total_energy: float      # naive energy of the tag window
    parent_extrapolated: float   # what the parent's ringing alone accounts for
    excess_energy: float         # tag_total - parent_extrapolated (floored at 0)
    excess_ratio: float          # excess / total (0 = pure inheritance, 1 = all new)


def decompose_stacked(env: np.ndarray, sr_env: float,
                      parent_peak_idx: int, tag_start_idx: int,
                      tag_end_idx: int) -> StackedDecomposition:
    """Separate a tag's genuine response from the parent laugh it landed on.

    Fit an exponential decay to the parent's envelope between its peak and
    the tag onset, extrapolate that envelope through the tag window, and
    credit the tag only with energy *above* the extrapolation. A tag that
    merely rides the parent's ringing scores ~0 excess; a tag that re-lifts
    the room scores its real contribution.
    """
    env = np.asarray(env, dtype=np.float64)
    seg = env[parent_peak_idx:tag_start_idx]
    tag = env[tag_start_idx:tag_end_idx]
    dt = 1.0 / sr_env
    tag_total = float(np.sum(tag ** 2) * dt)

    if len(seg) < 3 or seg[0] <= 0:
        # nothing to fit — treat all tag energy as genuine
        return StackedDecomposition(tag_total, 0.0, tag_total,
                                    1.0 if tag_total > 0 else 0.0)

    # log-linear fit of the parent decay: env(t) ≈ A * exp(-t/tau)
    t = np.arange(len(seg)) * dt
    logs = np.log(np.maximum(seg, 1e-12))
    slope, intercept = np.polyfit(t, logs, 1)
    if slope >= 0:
        # parent isn't decaying (still rising / plateau) — can't attribute;
        # conservative choice: extrapolate a flat envelope at the boundary level
        extrap = np.full(len(tag), seg[-1])
    else:
        t_tag = (np.arange(len(tag)) + len(seg)) * dt
        extrap = np.exp(intercept + slope * t_tag)

    parent_energy = float(np.sum(np.minimum(extrap, tag) ** 2) * dt)
    excess = max(0.0, tag_total - parent_energy)
    ratio = excess / tag_total if tag_total > 0 else 0.0
    return StackedDecomposition(tag_total, parent_energy, excess, ratio)
