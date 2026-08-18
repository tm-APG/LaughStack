"""Optional transcription via faster-whisper.

Word-level timestamps are what let us pin a laugh to the words that caused
it. This module is a thin wrapper that degrades loudly, not silently: if
faster-whisper isn't installed, ``transcribe`` raises with install
instructions rather than returning an empty transcript that downstream
code would misread as "the comic said nothing".
"""

from __future__ import annotations

from pathlib import Path

from .models import TranscriptSegment


def transcribe(wav_path: str | Path, model_size: str = "small",
               language: str = "en",
               vad_filter: bool = True) -> list[TranscriptSegment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise ImportError(
            "faster-whisper is not installed. `pip install faster-whisper` "
            "(or `pip install laughstack[asr]`). Transcription is optional: "
            "detection and set-level metrics run without it, but per-joke "
            "alignment (align.py) needs word timestamps."
        ) from e

    model = WhisperModel(model_size, compute_type="int8")
    segments, _info = model.transcribe(
        str(wav_path), language=language, word_timestamps=True,
        vad_filter=vad_filter,
    )
    out: list[TranscriptSegment] = []
    for seg in segments:
        words = [
            {"word": w.word, "start": float(w.start), "end": float(w.end)}
            for w in (seg.words or [])
        ]
        out.append(TranscriptSegment(
            start_s=float(seg.start), end_s=float(seg.end),
            text=seg.text.strip(), words=words,
        ))
    return out
