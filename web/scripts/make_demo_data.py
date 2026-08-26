"""Regenerate web/public/demo/* through the real pipeline.

Two synthetic nights of the same six-joke set (one silent bit, one quick
tag, an applause-break closer) so the web app's demo mode exercises every
dashboard feature. Run from the repo root:

    python web/scripts/make_demo_data.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "src"))

from conftest import SR, cal_tone, laugh_burst, applause_burst, quiet_room  # noqa: E402
from laughstack.config import load_config  # noqa: E402
from laughstack.pipeline import analyze_file  # noqa: E402
from laughstack.models import TranscriptSegment  # noqa: E402
from laughstack.compare import match_jokes, ab_compare  # noqa: E402

OUT = ROOT / "web" / "public" / "demo"

JOKES = [
    ("so I finally met my landlord in person after three years",
     "turns out he's been living in my walls the whole time"),
    ("my therapist told me to write letters to people who hurt me and burn them",
     "so I did that, but now I don't know what to do with all these letters"),
    ("I took my grandmother to one of those escape rooms",
     "she solved it immediately, she escaped Poland in the forties"),  # silent
    ("I tried one of those meal kit subscriptions",
     "it's just groceries with homework"),
    ("and honestly the worst part",
     "the homework is graded by your own disappointment"),  # quick tag
    ("anyway that's my time, you've been wonderful",
     "tip your bartenders, I'm serious, I dated one, they remember everything"),
]

SPECS = [
    ("demo-tuesday-mic", "Jane Doe", "The Basement (Tuesday mic)", "2026-08-04",
     [0.22, 0.25, 0.0, 0.30, 0.26, 0.30], 11),
    ("demo-friday-late", "Jane Doe", "The Basement (Friday late)", "2026-08-14",
     [0.45, 0.30, 0.0, 0.34, 0.42, 0.5], 22),
]


def build(levels, seed):
    rng = np.random.default_rng(seed)
    pieces = [quiet_room(2.0, rng=rng), cal_tone(2.0)]
    t = 4.0
    transcript = []
    for i, (setup, punch) in enumerate(JOKES):
        setup_dur = 14.0 + (i % 3) * 4
        pieces.append(quiet_room(setup_dur, rng=rng))
        t += setup_dur
        # contiguous Whisper-style segments; punchline ends 0.4s pre-laugh
        punch_end = t - 2.0 - 0.4  # shifted timeline (cal onset ~2.0s)
        punch_start = punch_end - 3.1
        transcript.append(TranscriptSegment(start_s=punch_start - 6.0,
                                            end_s=punch_start, text=setup))
        transcript.append(TranscriptSegment(start_s=punch_start,
                                            end_s=punch_end, text=punch))
        lvl = levels[i]
        if lvl > 0:
            if i == 4:
                burst = laugh_burst(2.0, mod_hz=5.5, level=lvl, rng=rng)
            elif i == 5:
                burst = np.concatenate([laugh_burst(2.5, level=lvl, rng=rng),
                                        applause_burst(4.0, level=0.35, rng=rng)])
            else:
                burst = laugh_burst(2.0 + 2.5 * lvl, mod_hz=4.5 + i * 0.3,
                                    level=lvl, rng=rng)
            pieces.append(burst)
            t += len(burst) / SR
        else:
            pieces.append(quiet_room(2.0, rng=rng))
            t += 2.0
        gap = 1.0 if i == 3 else 8.0
        pieces.append(quiet_room(gap, rng=rng))
        t += gap
    pieces.append(quiet_room(15.0, rng=rng))
    return np.concatenate(pieces), transcript


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    sessions = []
    with tempfile.TemporaryDirectory() as td:
        for sid, perf, venue, date, levels, seed in SPECS:
            x, transcript = build(levels, seed)
            p = os.path.join(td, sid + ".wav")
            sf.write(p, x, SR)
            s = analyze_file(p, cfg, session_id=sid, performer=perf,
                             venue=venue, date=date, transcript=transcript)
            s.audio.path = sid + ".wav"
            s.save(OUT / f"{sid}.json")
            sessions.append(s)
            print(sid, "events:", len(s.events), "jokes:", len(s.jokes),
                  "silent:", sum(1 for j in s.jokes if not j.events))

    idx = {"sessions": [{
        "id": s.session_id, "performer": s.performer, "venue": s.venue,
        "date": s.date, "status": "complete", "sourceType": "kit",
        "metrics": {"lpm": s.metrics.laughs_per_minute,
                     "parScore": s.metrics.par_score,
                     "nEvents": s.metrics.n_events},
    } for s in sessions]}
    (OUT / "index.json").write_text(json.dumps(idx, indent=2))

    matches = match_jokes(sessions)
    rows = []
    for mt in matches:
        r = ab_compare(mt, sessions[0].session_id, sessions[1].session_id)
        if r:
            rows.append({"joke": r.joke_text,
                         "deltaTotalLaughS": r.delta_total_laugh_s,
                         "deltaEnergyRel": r.delta_energy_rel,
                         "deltaLatencyS": r.delta_latency_s,
                         "positionConfound": r.position_confound,
                         "verdict": r.verdict})
    rows.sort(key=lambda r: -(r["deltaEnergyRel"]
                              if r["deltaEnergyRel"] is not None else -99))
    (OUT / "comparison.json").write_text(json.dumps(
        {"a": sessions[0].session_id, "b": sessions[1].session_id,
         "matched": len(rows), "rows": rows}, indent=2))
    print("matched:", len(rows))
    for r in rows:
        print("  ", r["joke"][:45], "->", r["verdict"][:65])


if __name__ == "__main__":
    main()
