"""Core data model.

Everything downstream of detection speaks these types. They serialize to
plain dicts (and therefore JSON) so session results can be archived next to
the audio and re-loaded without re-running DSP.

Units: all times are seconds from the start of the *session-aligned*
timeline (after cal-tone offset correction), all levels are dBFS unless a
field name says otherwise.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EventKind(str, Enum):
    LAUGH = "laugh"
    APPLAUSE = "applause"
    MIXED = "mixed"          # laugh rolling into applause (a "spike")
    GROAN = "groan"          # negative-affect response; still a response
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    KIT = "kit"              # our multi-mic rental kit recording
    YOUTUBE = "youtube"      # single-channel pull from a published video
    UPLOAD = "upload"        # customer-supplied file (phone recording etc.)


@dataclass
class AudioMeta:
    """Provenance and QC facts for one ingested recording."""
    path: str
    source_type: str = SourceType.KIT.value
    sample_rate: int = 48000
    channels: int = 1
    duration_s: float = 0.0
    # QC gate results (ingest.local.run_qc fills these)
    clipping_ratio: float = 0.0          # fraction of samples at full scale
    dropout_regions: list[tuple[float, float]] = field(default_factory=list)
    cal_tone_offset_s: Optional[float] = None
    cal_tone_level_dbfs: Optional[float] = None
    noise_floor_dbfs: Optional[float] = None
    rt60_s: Optional[float] = None       # measured at load-in if available
    qc_passed: bool = True
    qc_notes: list[str] = field(default_factory=list)
    # YouTube-specific provenance
    url: Optional[str] = None
    video_id: Optional[str] = None
    title: Optional[str] = None
    channel: Optional[str] = None
    upload_date: Optional[str] = None


@dataclass
class LaughEvent:
    """One detected audience response."""
    start_s: float
    end_s: float
    kind: str = EventKind.LAUGH.value
    confidence: float = 1.0
    peak_dbfs: float = -60.0
    energy: float = 0.0                  # integrated linear energy (envelope^2 * dt)
    decay_s: Optional[float] = None      # -20 dB decay time of the tail, RT60-corrected if possible
    # Stacked-tag decomposition: energy measured above the extrapolated
    # decay envelope of the parent laugh (see dsp.decompose_stacked).
    parent_index: Optional[int] = None   # index of the laugh this one landed on
    excess_energy: Optional[float] = None
    # Normalized scores, filled by metrics.normalize_events
    rel_peak: Optional[float] = None     # robust z vs session median/MAD
    rel_energy: Optional[float] = None

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass
class TranscriptSegment:
    start_s: float
    end_s: float
    text: str
    words: list[dict[str, Any]] = field(default_factory=list)  # {word, start, end}


@dataclass
class JokeInstance:
    """One delivery of one joke: a transcript span plus the response it drew.

    A *silent* punchline is still a JokeInstance — events may be empty.
    Silence is data.
    """
    bit_id: str                          # stable id for the bit this belongs to
    setup_text: str
    punchline_text: str
    punchline_end_s: float
    events: list[LaughEvent] = field(default_factory=list)
    latency_s: Optional[float] = None    # punchline end -> laugh onset
    position_in_set: Optional[float] = None  # 0..1, where in the set it landed

    @property
    def total_laugh_s(self) -> float:
        return sum(e.duration_s for e in self.events)

    @property
    def scored(self) -> bool:
        return bool(self.events)


@dataclass
class SetMetrics:
    """Whole-set summary numbers."""
    duration_s: float = 0.0
    n_events: int = 0
    total_laugh_s: float = 0.0
    laughs_per_minute: float = 0.0
    laugh_s_per_minute: float = 0.0      # Comedy Evaluator Pro-style basis
    par_score: float = 0.0               # % of stage time that is laughter (18s/min == 30)
    median_peak_dbfs: float = -60.0
    median_event_duration_s: float = 0.0
    longest_silence_s: float = 0.0
    applause_breaks: int = 0


@dataclass
class Session:
    """One analyzed performance."""
    session_id: str
    performer: str = ""
    venue: str = ""
    date: str = ""
    audio: Optional[AudioMeta] = None
    events: list[LaughEvent] = field(default_factory=list)
    transcript: list[TranscriptSegment] = field(default_factory=list)
    jokes: list[JokeInstance] = field(default_factory=list)
    metrics: Optional[SetMetrics] = None
    notes: dict[str, Any] = field(default_factory=dict)

    # ---- serialization -------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "Session":
        d = json.loads(Path(path).read_text())
        return cls.from_dict(d)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Session":
        audio = AudioMeta(**d["audio"]) if d.get("audio") else None
        events = [LaughEvent(**{k: v for k, v in e.items()}) for e in d.get("events", [])]
        transcript = [TranscriptSegment(**t) for t in d.get("transcript", [])]
        jokes = []
        for j in d.get("jokes", []):
            ev = [LaughEvent(**e) for e in j.pop("events", [])]
            jokes.append(JokeInstance(events=ev, **j))
        metrics = SetMetrics(**d["metrics"]) if d.get("metrics") else None
        return cls(
            session_id=d["session_id"],
            performer=d.get("performer", ""),
            venue=d.get("venue", ""),
            date=d.get("date", ""),
            audio=audio,
            events=events,
            transcript=transcript,
            jokes=jokes,
            metrics=metrics,
            notes=d.get("notes", {}),
        )
