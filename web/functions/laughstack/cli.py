"""Command-line interface.

    laughstack analyze  <audio> [--performer --venue --date --source ...]
    laughstack youtube  <url> [--start --end] --out data/youtube
    laughstack compare  <session.json> <session.json> [...]
    laughstack clips    <session.json> --media <video-or-audio>
    laughstack qc       <audio>

Every command writes machine-readable JSON next to the human deliverable,
so re-runs and audits never depend on console scrollback.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .models import Session, SourceType


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="laughstack",
                                description="Audience-response analytics for live comedy")
    p.add_argument("--config", help="per-engagement YAML overriding config/default.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="analyze one recording into a scored session")
    a.add_argument("audio")
    a.add_argument("--session-id")
    a.add_argument("--performer", default="")
    a.add_argument("--venue", default="")
    a.add_argument("--date", default="")
    a.add_argument("--source", default="kit", choices=[s.value for s in SourceType])
    a.add_argument("--rt60", type=float, help="measured room RT60 in seconds")
    a.add_argument("--transcribe", action="store_true",
                   help="run faster-whisper for per-joke alignment (needs [asr] extra)")
    a.add_argument("--out", default="reports")

    y = sub.add_parser("youtube", help="pull a published set's audio and analyze it")
    y.add_argument("url")
    y.add_argument("--start", type=float, help="clip start (s) inside the video")
    y.add_argument("--end", type=float, help="clip end (s) inside the video")
    y.add_argument("--performer", default="")
    y.add_argument("--venue", default="")
    y.add_argument("--out", default=None, help="download dir (default from config)")
    y.add_argument("--reports", default="reports")
    y.add_argument("--transcribe", action="store_true")
    y.add_argument("--probe-only", action="store_true",
                   help="print metadata JSON without downloading")

    c = sub.add_parser("compare", help="match jokes across analyzed sessions and A/B them")
    c.add_argument("sessions", nargs="+", help="session.json files from analyze")
    c.add_argument("--out", default="reports")

    k = sub.add_parser("clips", help="rank social-clip candidates from a scored session")
    k.add_argument("session", help="session.json from analyze")
    k.add_argument("--media", required=True, help="source video/audio to cut from")
    k.add_argument("--out", default="reports")

    q = sub.add_parser("qc", help="QC gates only (crew tool: run before leaving the venue)")
    q.add_argument("audio")
    q.add_argument("--no-cal-tone", action="store_true")

    args = p.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "analyze":
        return _cmd_analyze(args, cfg)
    if args.cmd == "youtube":
        return _cmd_youtube(args, cfg)
    if args.cmd == "compare":
        return _cmd_compare(args, cfg)
    if args.cmd == "clips":
        return _cmd_clips(args, cfg)
    if args.cmd == "qc":
        return _cmd_qc(args, cfg)
    return 2


def _maybe_transcript(audio_path: str, enabled: bool, cfg: dict):
    if not enabled:
        return None
    from .transcribe import transcribe
    tcfg = cfg.get("transcribe", {})
    return transcribe(audio_path, model_size=tcfg.get("model_size", "small"),
                      language=tcfg.get("language", "en"))


def _cmd_analyze(args, cfg) -> int:
    from .pipeline import analyze_file
    from .report import write_session_report
    transcript = _maybe_transcript(args.audio, args.transcribe, cfg)
    session = analyze_file(
        args.audio, cfg, session_id=args.session_id,
        performer=args.performer, venue=args.venue, date=args.date,
        source_type=args.source, transcript=transcript, rt60_s=args.rt60,
    )
    md, js = write_session_report(session, args.out)
    print(f"report: {md}\nsession: {js}")
    if session.audio and not session.audio.qc_passed:
        print("WARNING: QC gates failed — see report QC notes", file=sys.stderr)
        return 1
    return 0


def _cmd_youtube(args, cfg) -> int:
    from .ingest.youtube import fetch_youtube_audio, probe_youtube
    from .pipeline import analyze_file
    from .report import write_session_report

    if args.probe_only:
        print(json.dumps(probe_youtube(args.url), indent=2))
        return 0

    ycfg = cfg.get("youtube", {})
    out_dir = args.out or ycfg.get("out_dir", "data/youtube")
    wav, meta = fetch_youtube_audio(
        args.url, out_dir, sample_rate=int(ycfg.get("sample_rate", 16000)),
        start_s=args.start, end_s=args.end,
    )
    transcript = _maybe_transcript(str(wav), args.transcribe, cfg)
    session = analyze_file(
        wav, cfg, session_id=meta.video_id,
        performer=args.performer or (meta.channel or ""),
        venue=args.venue, date=meta.upload_date or "",
        source_type=SourceType.YOUTUBE.value, transcript=transcript,
    )
    # carry provenance from the download into the session
    session.audio.url = meta.url
    session.audio.video_id = meta.video_id
    session.audio.title = meta.title
    session.audio.channel = meta.channel
    session.audio.upload_date = meta.upload_date
    session.audio.qc_notes.extend(meta.qc_notes)
    md, js = write_session_report(session, args.reports)
    print(f"audio: {wav}\nreport: {md}\nsession: {js}")
    return 0


def _cmd_compare(args, cfg) -> int:
    from .compare import match_jokes
    from .report import comparison_markdown
    sessions = [Session.load(pth) for pth in args.sessions]
    matches = match_jokes(sessions,
                          min_similarity=float(cfg.get("compare", {})
                                               .get("min_similarity", 0.5)))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if len(sessions) >= 2:
        md = comparison_markdown(matches, sessions[0].session_id,
                                 sessions[1].session_id)
        path = out / f"compare_{sessions[0].session_id}_vs_{sessions[1].session_id}.md"
        path.write_text(md)
        print(f"comparison: {path}")
    manifest = [
        {"joke": m.canonical_text[:100], "instances": m.table()}
        for m in matches
    ]
    jpath = out / "matched_jokes.json"
    jpath.write_text(json.dumps(manifest, indent=2))
    print(f"matches: {jpath} ({len(matches)} joke(s) matched)")
    return 0


def _cmd_clips(args, cfg) -> int:
    from .clips import clip_candidates, write_manifest
    session = Session.load(args.session)
    ccfg = cfg.get("clips", {})
    clips = clip_candidates(
        session, args.media,
        max_clips=int(ccfg.get("max_clips", 5)),
        min_duration_s=float(ccfg.get("min_duration_s", 8.0)),
        max_duration_s=float(ccfg.get("max_duration_s", 90.0)),
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    mpath = out / f"{session.session_id}.clips.json"
    write_manifest(clips, mpath)
    print(f"clip manifest: {mpath}")
    for c in clips:
        print(f"  #{c.rank} [{c.start_s:.1f}–{c.end_s:.1f}s] "
              f"laugh {c.total_laugh_s:.1f}s  z={c.score:+.2f}  {c.punchline!r}")
    return 0


def _cmd_qc(args, cfg) -> int:
    from .ingest.local import load_audio, run_qc
    ing = cfg.get("ingest", {})
    x, sr = load_audio(args.audio, mono=True)
    meta = run_qc(x, sr, path=args.audio,
                  expect_cal_tone=not args.no_cal_tone,
                  **{k: float(v) for k, v in ing.get("qc", {}).items()})
    print(json.dumps({
        "qc_passed": meta.qc_passed,
        "duration_s": round(meta.duration_s, 1),
        "clipping_ratio": meta.clipping_ratio,
        "dropouts": meta.dropout_regions,
        "noise_floor_dbfs": round(meta.noise_floor_dbfs or 0.0, 1),
        "cal_tone_offset_s": meta.cal_tone_offset_s,
        "cal_tone_level_dbfs": meta.cal_tone_level_dbfs,
        "notes": meta.qc_notes,
    }, indent=2))
    return 0 if meta.qc_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
