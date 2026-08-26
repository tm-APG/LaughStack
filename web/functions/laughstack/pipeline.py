"""End-to-end analysis: audio file -> scored Session.

This is the glue the CLI calls; each stage is importable on its own for
notebooks and tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np

from . import align as align_mod
from .detect import get_detector, detect_events
from .ingest.local import load_audio, run_qc
from .metrics import attribute_stacked, normalize_events, set_metrics
from .models import Session, SourceType, TranscriptSegment


def analyze_file(path: str | Path, cfg: dict[str, Any],
                 session_id: Optional[str] = None,
                 performer: str = "", venue: str = "", date: str = "",
                 source_type: str = SourceType.KIT.value,
                 transcript: Optional[list[TranscriptSegment]] = None,
                 rt60_s: Optional[float] = None) -> Session:
    """Run ingest -> QC -> detect -> (align) -> metrics on one recording."""
    path = Path(path)
    ing = cfg.get("ingest", {})
    det = cfg.get("detect", {})
    ali = cfg.get("align", {})

    sr_target = int(ing.get("target_sample_rate", 16000))
    x, sr = load_audio(path, target_sr=sr_target, mono=True)

    expect_tone = ing.get("expect_cal_tone", True) and \
        source_type == SourceType.KIT.value
    meta = run_qc(x, sr, path=str(path), source_type=source_type,
                  expect_cal_tone=expect_tone,
                  **_qc_kwargs(ing.get("qc", {})))
    if rt60_s is not None:
        meta.rt60_s = rt60_s

    # shift the timeline so t=0 is the cal-tone onset (shared across mics)
    t0 = meta.cal_tone_offset_s or 0.0

    detector = get_detector(det.get("backend", "heuristic"),
                            win_s=float(det.get("win_s", 1.0)),
                            hop_s=float(det.get("hop_s", 0.25)))
    events = detect_events(
        x, sr, detector=detector,
        on_threshold=float(det.get("on_threshold", 0.5)),
        off_threshold=float(det.get("off_threshold", 0.3)),
        min_event_s=float(det.get("min_event_s", 0.4)),
        merge_gap_s=float(det.get("merge_gap_s", 0.4)),
        rt60_s=meta.rt60_s,
    )
    for e in events:
        e.start_s -= t0
        e.end_s -= t0

    # stacked-tag attribution needs the envelope
    align_mod.mark_stacked(events, float(ali.get("stack_window_s", 1.5)))
    dec = max(1, sr // 50)
    env = np.array([np.max(np.abs(x[i:i + dec]))
                    for i in range(0, len(x), dec)])
    # envelope timeline shares the t0 shift via index offset
    off = int(t0 * 50)
    env_shifted = env[off:] if off < len(env) else env
    attribute_stacked(events, env_shifted, 50.0)
    normalize_events(events)

    duration = meta.duration_s - t0
    jokes = []
    if transcript:
        jokes = align_mod.align(
            events, transcript, set_duration_s=duration,
            max_latency_s=float(ali.get("max_latency_s", 3.0)))

    session = Session(
        session_id=session_id or path.stem,
        performer=performer, venue=venue, date=date,
        audio=meta, events=events, transcript=transcript or [],
        jokes=jokes, metrics=set_metrics(events, duration),
    )
    return session


def _qc_kwargs(qc_cfg: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k in ("max_clipping_ratio", "dropout_min_s", "max_noise_floor_dbfs"):
        if k in qc_cfg:
            out[k] = float(qc_cfg[k])
    return out
