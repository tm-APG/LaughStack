"""Deliverables: session report (Markdown + JSON) and A/B comparison report.

The Markdown report is the thing a producer or comic actually reads.
Rules: lead with the set-level numbers, then the laugh map (text timeline),
then the per-bit table including silent punchlines. Never hide a bit that
died — that's what the client is paying to find out.
"""

from __future__ import annotations

from pathlib import Path

from .models import Session, EventKind
from .metrics import joke_score
from .compare import MatchedJoke, ab_compare


def laugh_map(session: Session, width: int = 80) -> str:
    """ASCII timeline of the set: one row, laughter density by column."""
    if not session.metrics or session.metrics.duration_s <= 0:
        return "(no duration)"
    dur = session.metrics.duration_s
    cols = [0.0] * width
    for e in session.events:
        if e.kind == EventKind.APPLAUSE.value:
            continue
        c0 = int(e.start_s / dur * width)
        c1 = min(width - 1, int(e.end_s / dur * width))
        for c in range(c0, c1 + 1):
            cols[c] += max(e.confidence, 0.3)
    ramp = " .:-=+*#%@"
    peak = max(cols) or 1.0
    line = "".join(ramp[min(len(ramp) - 1, int(v / peak * (len(ramp) - 1)))]
                   for v in cols)
    mins = int(dur // 60)
    return f"|{line}|\n 0m{' ' * (width - 6)}{mins}m"


def session_markdown(session: Session) -> str:
    m = session.metrics
    lines = [
        f"# Set report — {session.performer or session.session_id}",
        "",
        f"- **Session**: `{session.session_id}`",
        f"- **Venue**: {session.venue or '—'}   **Date**: {session.date or '—'}",
    ]
    if session.audio:
        lines.append(f"- **Source**: {session.audio.source_type} "
                     f"({session.audio.duration_s / 60:.1f} min)")
        if session.audio.qc_notes:
            lines.append(f"- **QC notes**: {'; '.join(session.audio.qc_notes)}")
    lines.append("")
    if m:
        lines += [
            "## Set-level numbers",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Laughs per minute | {m.laughs_per_minute:.2f} |",
            f"| Laugh seconds per minute | {m.laugh_s_per_minute:.1f} |",
            f"| PAR score (% of stage time laughing) | {m.par_score:.1f} |",
            f"| Laugh events | {m.n_events} |",
            f"| Applause breaks | {m.applause_breaks} |",
            f"| Median laugh duration | {m.median_event_duration_s:.2f} s |",
            f"| Longest silence | {m.longest_silence_s:.1f} s |",
            "",
            "_Reference: 18 laugh-seconds/min (PAR 30) is the Comedy",
            "Evaluator Pro headliner benchmark._",
            "",
            "## Laugh map",
            "",
            "```",
            laugh_map(session),
            "```",
            "",
        ]
    if session.jokes:
        lines += [
            "## Per-bit results",
            "",
            "| # | Punchline | Laugh s | Energy (z) | Latency s | Position |",
            "|---|---|---|---|---|---|",
        ]
        for i, ji in enumerate(session.jokes, 1):
            s = joke_score(ji)
            punch = (ji.punchline_text or "(unaligned event)")[:60]
            energy = f"{s['energy_rel']:+.2f}" if s["energy_rel"] is not None else "—"
            lat = f"{s['latency_s']:.2f}" if s["latency_s"] is not None else "—"
            pos = f"{s['position']:.0%}" if s["position"] is not None else "—"
            laugh_s = f"{s['total_laugh_s']:.1f}" if ji.events else "**silent**"
            lines.append(f"| {i} | {punch} | {laugh_s} | {energy} | {lat} | {pos} |")
        lines.append("")
        silent = sum(1 for ji in session.jokes if not ji.events)
        if silent:
            lines.append(f"_{silent} bit(s) drew no detected response — "
                         f"listed above, not hidden._")
    return "\n".join(lines) + "\n"


def comparison_markdown(matches: list[MatchedJoke],
                        a_session: str, b_session: str) -> str:
    lines = [
        f"# A/B comparison — `{a_session}` vs `{b_session}`",
        "",
        "Scores are within-room robust z (median/MAD) — each delivery is",
        "judged against its own room's median laugh, then compared. A hot",
        "Friday crowd does not automatically beat a Tuesday mic here.",
        "",
    ]
    results = [r for m in matches
               if (r := ab_compare(m, a_session, b_session)) is not None]
    if not results:
        lines.append("_No jokes matched across both sessions._")
        return "\n".join(lines) + "\n"
    lines += [
        "| Joke | Δ laugh s | Δ energy z | Δ latency s | Pos. confound | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda r: -(r.delta_energy_rel or 0)):
        de = f"{r.delta_energy_rel:+.2f}" if r.delta_energy_rel is not None else "—"
        dl = f"{r.delta_latency_s:+.2f}" if r.delta_latency_s is not None else "—"
        pc = f"{r.position_confound:.0%}" if r.position_confound is not None else "—"
        lines.append(f"| {r.joke_text[:50]} | {r.delta_total_laugh_s:+.1f} "
                     f"| {de} | {dl} | {pc} | {r.verdict} |")
    return "\n".join(lines) + "\n"


def write_session_report(session: Session, out_dir: str | Path) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = out / f"{session.session_id}.report.md"
    js = out / f"{session.session_id}.session.json"
    md.write_text(session_markdown(session))
    session.save(js)
    return md, js
