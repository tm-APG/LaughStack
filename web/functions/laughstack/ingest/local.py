"""Local-file ingest and QC gates.

The QC pass is what stands between "crew hit record" and "we billed a
client for numbers derived from a clipped, dropped-out file". Gates:

* clipping        — fraction of samples within epsilon of full scale
* dropouts        — runs of digital silence mid-file (recorder glitch,
                    bumped cable) reported as regions
* cal tone        — locate the 1 kHz reference; without it, cross-mic and
                    cross-night level comparisons are labeled as such
* noise floor     — 10th-percentile frame RMS; a floor above -45 dBFS means
                    the audience mics were gained into the PA or HVAC

`run_qc` never raises on bad audio — it records findings and sets
``qc_passed``. The analyst decides what is fatal; the pipeline's job is to
never silently analyze a broken file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from ..dsp import detect_cal_tone, frame_rms_db
from ..models import AudioMeta, SourceType


def load_audio(path: str | Path, target_sr: Optional[int] = None,
               mono: bool = False) -> tuple[np.ndarray, int]:
    """Load an audio file as float64 in [-1, 1].

    Returns (audio, sr). Multichannel files come back as (n, ch) unless
    ``mono``. Resampling (if ``target_sr``) uses polyphase filtering.
    """
    x, sr = sf.read(str(path), always_2d=True, dtype="float64")
    if mono and x.shape[1] > 1:
        x = x.mean(axis=1, keepdims=True)
    if target_sr and target_sr != sr:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(target_sr, sr)
        x = resample_poly(x, target_sr // g, sr // g, axis=0)
        sr = target_sr
    if x.shape[1] == 1:
        x = x[:, 0]
    return x, sr


def run_qc(x: np.ndarray, sr: int, path: str = "",
           source_type: str = SourceType.KIT.value,
           expect_cal_tone: bool = True,
           clip_epsilon: float = 1e-4,
           max_clipping_ratio: float = 1e-4,
           dropout_min_s: float = 0.2,
           max_noise_floor_dbfs: float = -45.0) -> AudioMeta:
    """Run the QC gates over one (mono) channel and return its AudioMeta."""
    x = np.asarray(x, dtype=np.float64)
    meta = AudioMeta(path=str(path), source_type=source_type,
                     sample_rate=sr, channels=1,
                     duration_s=len(x) / sr)

    # clipping
    clipped = np.abs(x) >= (1.0 - clip_epsilon)
    meta.clipping_ratio = float(np.mean(clipped))
    if meta.clipping_ratio > max_clipping_ratio:
        meta.qc_passed = False
        meta.qc_notes.append(
            f"clipping: {meta.clipping_ratio:.2e} of samples at full scale "
            f"(limit {max_clipping_ratio:.0e})")

    # dropouts: runs of exact digital zero longer than dropout_min_s
    zero = x == 0.0
    meta.dropout_regions = _find_runs(zero, sr, dropout_min_s)
    # leading/trailing silence isn't a dropout
    meta.dropout_regions = [
        (a, b) for a, b in meta.dropout_regions
        if a > 0.5 and b < meta.duration_s - 0.5
    ]
    if meta.dropout_regions:
        meta.qc_passed = False
        meta.qc_notes.append(
            f"dropouts: {len(meta.dropout_regions)} region(s) of digital "
            f"silence mid-file, first at {meta.dropout_regions[0][0]:.1f}s")

    # noise floor
    _, rms_db = frame_rms_db(x, sr, frame_s=0.4, hop_s=0.2)
    meta.noise_floor_dbfs = float(np.percentile(rms_db, 10))
    if meta.noise_floor_dbfs > max_noise_floor_dbfs:
        meta.qc_notes.append(
            f"high noise floor: {meta.noise_floor_dbfs:.1f} dBFS "
            f"(want < {max_noise_floor_dbfs:.0f})")

    # cal tone
    if expect_cal_tone:
        tone = detect_cal_tone(x, sr)
        if tone is None:
            meta.qc_notes.append(
                "cal tone not found — cross-mic/cross-night level "
                "comparisons will be uncalibrated")
        else:
            meta.cal_tone_offset_s = tone.offset_s
            meta.cal_tone_level_dbfs = tone.level_dbfs
    return meta


def _find_runs(mask: np.ndarray, sr: int, min_s: float) -> list[tuple[float, float]]:
    min_len = int(min_s * sr)
    regions = []
    diff = np.diff(mask.astype(np.int8))
    starts = list(np.nonzero(diff == 1)[0] + 1)
    ends = list(np.nonzero(diff == -1)[0] + 1)
    if mask[0]:
        starts.insert(0, 0)
    if mask[-1]:
        ends.append(len(mask))
    for a, b in zip(starts, ends):
        if b - a >= min_len:
            regions.append((a / sr, b / sr))
    return regions
