"""LaughStack Cloud Functions (Python, 2nd gen).

Deployed surface:

* ``analyze_upload`` — Storage trigger on ``uploads/{uid}/{sessionId}/…``.
  Downloads the file, transcodes to mono 16 kHz WAV (bundled ffmpeg via
  imageio-ffmpeg), runs the laughstack pipeline, writes the full session
  JSON to ``results/{uid}/{sessionId}/session.json`` and a summary to the
  Firestore doc ``sessions/{sessionId}``.

* ``compare_sessions`` — callable. Loads two completed sessions' JSON from
  Storage, runs joke matching + A/B, returns the comparison rows.

The DSP stays server-side on purpose (see docs/PATENTS.md — trade-secret
posture): the client only ever sees results.

Deploy note: run ``web/scripts/sync_package.sh`` before ``firebase deploy``
so ``functions/laughstack/`` is a current copy of ``src/laughstack``.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import traceback

from firebase_admin import initialize_app, firestore, storage as admin_storage
from firebase_functions import https_fn, storage_fn, options

initialize_app()

# Analysis is CPU-bound scipy; give it headroom and cap concurrency.
_RUNTIME = dict(memory=options.MemoryOption.GB_2, timeout_sec=540,
                max_instances=3, concurrency=1)

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".webm", ".mov"}


def _ffmpeg_path() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _to_wav(src: pathlib.Path, dst: pathlib.Path, sr: int = 16000) -> None:
    proc = subprocess.run(
        [_ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(src), "-ac", "1", "-ar", str(sr), "-sample_fmt", "s16",
         str(dst)],
        capture_output=True, text=True, timeout=480,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"transcode failed: {proc.stderr.strip()[:400]}")


@storage_fn.on_object_finalized(**_RUNTIME)
def analyze_upload(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]) -> None:
    name = event.data.name or ""
    parts = name.split("/")
    # only handle uploads/{uid}/{sessionId}/<file>
    if len(parts) != 4 or parts[0] != "uploads":
        return
    _, uid, session_id, filename = parts
    if pathlib.Path(filename).suffix.lower() not in AUDIO_EXTS:
        return

    db = firestore.client()
    doc = db.collection("sessions").document(session_id)
    snap = doc.get()
    meta_in = snap.to_dict() if snap.exists else {}
    if meta_in.get("status") == "complete":
        return  # idempotence: re-finalize events on the same object
    doc.set({"status": "processing", "owner": uid,
             "audioPath": name}, merge=True)

    try:
        result_path = _run_analysis(event.data.bucket, name, uid, session_id,
                                    meta_in)
        doc.set({"status": "complete", "resultPath": result_path,
                 **_summary_fields(event.data.bucket, result_path)},
                merge=True)
    except Exception as e:  # surface the failure on the doc, never swallow
        doc.set({"status": "error",
                 "error": f"{type(e).__name__}: {e}"[:800]}, merge=True)
        print(traceback.format_exc())
        raise


def _run_analysis(bucket_name: str, blob_name: str, uid: str,
                  session_id: str, meta_in: dict) -> str:
    from laughstack.config import load_config
    from laughstack.pipeline import analyze_file
    from laughstack.models import SourceType

    bucket = admin_storage.bucket(bucket_name)
    with tempfile.TemporaryDirectory() as td:
        tdir = pathlib.Path(td)
        src = tdir / pathlib.Path(blob_name).name
        bucket.blob(blob_name).download_to_filename(str(src))

        wav = src if src.suffix.lower() == ".wav" else tdir / "audio.wav"
        if wav is not src:
            _to_wav(src, wav)

        cfg = load_config()  # bundled config/default.yaml inside the package copy
        source = meta_in.get("sourceType", SourceType.UPLOAD.value)
        session = analyze_file(
            wav, cfg, session_id=session_id,
            performer=meta_in.get("performer", ""),
            venue=meta_in.get("venue", ""),
            date=meta_in.get("date", ""),
            source_type=source,
        )
        out = tdir / "session.json"
        session.save(out)
        result_path = f"results/{uid}/{session_id}/session.json"
        bucket.blob(result_path).upload_from_filename(
            str(out), content_type="application/json")
        return result_path


def _summary_fields(bucket_name: str, result_path: str) -> dict:
    """Small, Firestore-safe summary for the sessions list view."""
    bucket = admin_storage.bucket(bucket_name)
    data = json.loads(bucket.blob(result_path).download_as_text())
    m = data.get("metrics") or {}
    audio = data.get("audio") or {}
    return {
        "metrics": {
            "durationS": m.get("duration_s", 0),
            "nEvents": m.get("n_events", 0),
            "totalLaughS": m.get("total_laugh_s", 0),
            "lpm": m.get("laughs_per_minute", 0),
            "laughSPerMin": m.get("laugh_s_per_minute", 0),
            "parScore": m.get("par_score", 0),
            "longestSilenceS": m.get("longest_silence_s", 0),
            "applauseBreaks": m.get("applause_breaks", 0),
        },
        "qc": {
            "passed": audio.get("qc_passed", True),
            "notes": (audio.get("qc_notes") or [])[:10],
        },
        "sourceType": audio.get("source_type", "upload"),
    }


@https_fn.on_call(memory=options.MemoryOption.GB_1, timeout_sec=120)
def compare_sessions(req: https_fn.CallableRequest):
    """Callable: A/B two completed sessions owned by the caller."""
    from laughstack.models import Session
    from laughstack.compare import match_jokes, ab_compare

    if req.auth is None:
        raise https_fn.HttpsError("unauthenticated", "Sign in required.")
    uid = req.auth.uid
    a_id = str(req.data.get("a", ""))
    b_id = str(req.data.get("b", ""))
    if not a_id or not b_id or a_id == b_id:
        raise https_fn.HttpsError("invalid-argument",
                                  "Pass two distinct session ids as {a, b}.")

    db = firestore.client()
    sessions = []
    bucket = admin_storage.bucket()
    for sid in (a_id, b_id):
        snap = db.collection("sessions").document(sid).get()
        d = snap.to_dict() if snap.exists else None
        if not d or d.get("owner") != uid:
            raise https_fn.HttpsError("permission-denied",
                                      f"Session {sid} not found for this user.")
        if d.get("status") != "complete" or not d.get("resultPath"):
            raise https_fn.HttpsError("failed-precondition",
                                      f"Session {sid} is not complete.")
        raw = bucket.blob(d["resultPath"]).download_as_text()
        sessions.append(Session.from_dict(json.loads(raw)))

    matches = match_jokes(sessions)
    rows = []
    for m in matches:
        r = ab_compare(m, a_id, b_id)
        if r is None:
            continue
        rows.append({
            "joke": r.joke_text,
            "deltaTotalLaughS": r.delta_total_laugh_s,
            "deltaEnergyRel": r.delta_energy_rel,
            "deltaLatencyS": r.delta_latency_s,
            "positionConfound": r.position_confound,
            "verdict": r.verdict,
        })
    rows.sort(key=lambda r: -(r["deltaEnergyRel"] or 0))
    return {"a": a_id, "b": b_id, "matched": len(rows), "rows": rows}
