"""YouTube ingest: pull audio + metadata from published sets.

Purpose: corpus building and detector validation against real rooms
(Kill Tony regulars, comics who upload multiple takes of the same hour,
late-night set vs. special versions of the same joke — see docs/CORPUS.md),
and a low-end analysis product for comics who only have a published video.

Two honest caveats baked into the metadata:

* A YouTube pull is one channel of the venue's board mix or a camera mic.
  There is no audience-mic separation, no cal tone, no RT60 — so events
  are detectable but absolute levels are not comparable across videos.
  ``source_type`` is set to ``youtube`` and downstream normalization is
  always within-video (median/MAD) for these.
* Some videos sweeten laughter in post. Cross-video comparisons on
  YouTube material are indicative, not evidential.

Copyright: downloads are for internal analysis/validation only. Do not
redistribute pulled audio; keep it inside the access-controlled bucket
with the same retention policy as client recordings.

Requires ``yt-dlp`` (pip) and ``ffmpeg`` on PATH.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from ..models import AudioMeta, SourceType

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeIngestError(RuntimeError):
    pass


def _require_tools() -> None:
    missing = [t for t in ("yt-dlp", "ffmpeg") if shutil.which(t) is None]
    if missing:
        raise YouTubeIngestError(
            f"missing required tool(s): {', '.join(missing)}. "
            f"Install yt-dlp via pip and ffmpeg via your package manager.")


def video_id_from_url(url: str) -> Optional[str]:
    """Extract the 11-char video id from common YouTube URL shapes."""
    if _ID_RE.match(url):
        return url
    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"/shorts/([A-Za-z0-9_-]{11})",
        r"/live/([A-Za-z0-9_-]{11})",
        r"/embed/([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def probe_youtube(url: str, timeout_s: int = 120) -> dict[str, Any]:
    """Fetch metadata (no download). Returns the yt-dlp info dict, trimmed."""
    _require_tools()
    proc = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-download", "--no-playlist", url],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise YouTubeIngestError(f"yt-dlp probe failed: {proc.stderr.strip()[:500]}")
    info = json.loads(proc.stdout)
    keep = ("id", "title", "channel", "uploader", "upload_date", "duration",
            "webpage_url", "view_count", "like_count", "chapters")
    return {k: info.get(k) for k in keep}


def fetch_youtube_audio(url: str, out_dir: str | Path,
                        sample_rate: int = 16000,
                        keep_original: bool = False,
                        start_s: Optional[float] = None,
                        end_s: Optional[float] = None,
                        timeout_s: int = 1800) -> tuple[Path, AudioMeta]:
    """Download a video's audio and normalize it to mono WAV.

    Returns (wav_path, AudioMeta). ``start_s``/``end_s`` clip a section
    (useful when only one comic's set inside a long show matters — e.g.
    one regular's slot in a 3-hour Kill Tony episode).

    Output naming: ``<video_id>.wav`` (plus ``<video_id>.info.json`` with
    the trimmed metadata) so re-ingesting the same video is idempotent.
    """
    _require_tools()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    info = probe_youtube(url)
    vid = info["id"]
    wav_path = out_dir / f"{vid}.wav"
    meta_path = out_dir / f"{vid}.info.json"

    if not wav_path.exists():
        # download best audio to a temp container, then transcode with ffmpeg
        tmp_tmpl = str(out_dir / f"{vid}.src.%(ext)s")
        cmd = ["yt-dlp", "-f", "bestaudio/best", "--no-playlist",
               "-o", tmp_tmpl, url]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_s)
        if proc.returncode != 0:
            raise YouTubeIngestError(
                f"yt-dlp download failed: {proc.stderr.strip()[:500]}")
        srcs = sorted(out_dir.glob(f"{vid}.src.*"))
        if not srcs:
            raise YouTubeIngestError("download reported success but no file found")
        src = srcs[0]

        ff = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        if start_s is not None:
            ff += ["-ss", str(start_s)]
        if end_s is not None:
            ff += ["-to", str(end_s)]
        ff += ["-i", str(src), "-ac", "1", "-ar", str(sample_rate),
               "-sample_fmt", "s16", str(wav_path)]
        proc = subprocess.run(ff, capture_output=True, text=True,
                              timeout=timeout_s)
        if proc.returncode != 0:
            raise YouTubeIngestError(f"ffmpeg failed: {proc.stderr.strip()[:500]}")
        if not keep_original:
            src.unlink(missing_ok=True)

    meta_path.write_text(json.dumps(info, indent=2))

    import soundfile as sf
    with sf.SoundFile(str(wav_path)) as f:
        duration = len(f) / f.samplerate

    meta = AudioMeta(
        path=str(wav_path),
        source_type=SourceType.YOUTUBE.value,
        sample_rate=sample_rate,
        channels=1,
        duration_s=duration,
        url=info.get("webpage_url") or url,
        video_id=vid,
        title=info.get("title"),
        channel=info.get("channel") or info.get("uploader"),
        upload_date=info.get("upload_date"),
        qc_notes=["youtube source: single-channel board/camera mix; "
                  "no cal tone, no RT60; within-video normalization only"],
    )
    return wav_path, meta
