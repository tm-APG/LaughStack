"""End-to-end: synthesized 'set' WAV -> analyze -> report -> serialization
round trip, and QC gates on deliberately broken audio."""

import json

import numpy as np
import pytest
import soundfile as sf

from laughstack.config import load_config
from laughstack.ingest.local import run_qc
from laughstack.ingest.youtube import video_id_from_url
from laughstack.models import Session, SourceType, TranscriptSegment
from laughstack.pipeline import analyze_file
from laughstack.report import session_markdown, write_session_report
from laughstack.clips import clip_candidates
from conftest import SR, cal_tone, laugh_burst, quiet_room


@pytest.fixture
def set_wav(tmp_path, rng):
    """A miniature kit recording: cal tone, then a 2-minute 'set' with two
    laughs at known times."""
    pieces = [
        quiet_room(2.0, rng=rng),
        cal_tone(2.0),
        quiet_room(30.0, rng=rng),
        laugh_burst(3.0, rng=rng),
        quiet_room(40.0, rng=rng),
        laugh_burst(2.5, mod_hz=4.5, rng=rng),
        quiet_room(30.0, rng=rng),
    ]
    x = np.concatenate(pieces)
    path = tmp_path / "set.wav"
    sf.write(str(path), x, SR)
    return path


def test_analyze_file_end_to_end(set_wav, tmp_path):
    cfg = load_config()
    transcript = [
        TranscriptSegment(start_s=25.0, end_s=29.5,
                          text="and that's why my landlord hates me"),
        TranscriptSegment(start_s=60.0, end_s=71.5,
                          text="so the second date was at the DMV"),
    ]
    session = analyze_file(set_wav, cfg, performer="Test Comic",
                           venue="Test Room", transcript=transcript)

    # cal tone found and timeline shifted
    assert session.audio.cal_tone_offset_s == pytest.approx(2.0, abs=0.3)
    # both laughs detected (times relative to cal-tone onset)
    assert len(session.events) >= 2
    first = session.events[0]
    assert first.start_s == pytest.approx(32.0, abs=2.0)  # 2+2+30 - 2 offset

    assert session.metrics.n_events >= 2
    assert session.metrics.total_laugh_s > 3.0
    assert session.jokes, "transcript alignment produced no jokes"

    # report renders and round-trips
    md, js = write_session_report(session, tmp_path / "reports")
    text = md.read_text()
    assert "Laughs per minute" in text
    assert "landlord" in text
    loaded = Session.load(js)
    assert loaded.session_id == session.session_id
    assert len(loaded.events) == len(session.events)
    assert loaded.metrics.par_score == pytest.approx(session.metrics.par_score)


def test_qc_flags_clipping(rng):
    x = quiet_room(10.0, rng=rng)
    x[SR:2 * SR] = 1.0  # a full second of flat-topped samples
    meta = run_qc(x, SR, expect_cal_tone=False)
    assert not meta.qc_passed
    assert any("clipping" in n for n in meta.qc_notes)


def test_qc_flags_dropout(rng):
    x = quiet_room(20.0, rng=rng)
    x[5 * SR:6 * SR] = 0.0
    meta = run_qc(x, SR, expect_cal_tone=False)
    assert not meta.qc_passed
    assert meta.dropout_regions
    assert meta.dropout_regions[0][0] == pytest.approx(5.0, abs=0.1)


def test_qc_notes_missing_cal_tone(rng):
    x = quiet_room(10.0, rng=rng)
    meta = run_qc(x, SR, expect_cal_tone=True)
    assert any("cal tone" in n for n in meta.qc_notes)


def test_video_id_parsing():
    assert video_id_from_url("https://www.youtube.com/watch?v=M0qDTYmaT-Y") == "M0qDTYmaT-Y"
    assert video_id_from_url("https://youtu.be/M0qDTYmaT-Y?t=10") == "M0qDTYmaT-Y"
    assert video_id_from_url("https://www.youtube.com/shorts/abcdefghijk") == "abcdefghijk"
    assert video_id_from_url("M0qDTYmaT-Y") == "M0qDTYmaT-Y"
    assert video_id_from_url("https://example.com/nope") is None


def test_clip_candidates_rank_and_bounds(set_wav, tmp_path):
    cfg = load_config()
    transcript = [
        TranscriptSegment(start_s=25.0, end_s=29.5,
                          text="and that's why my landlord hates me"),
        TranscriptSegment(start_s=60.0, end_s=71.5,
                          text="so the second date was at the DMV"),
    ]
    session = analyze_file(set_wav, cfg, transcript=transcript)
    clips = clip_candidates(session, "set.mp4", max_clips=3)
    assert clips
    for c in clips:
        assert 8.0 <= c.duration_s <= 90.0
        assert c.start_s >= 0
        assert "ffmpeg" in c.ffmpeg_cmd


def test_markdown_lists_silent_bits():
    from laughstack.models import JokeInstance, SetMetrics
    s = Session(session_id="t", jokes=[
        JokeInstance(bit_id="a", setup_text="", punchline_text="the dead joke",
                     punchline_end_s=10.0, events=[]),
    ], metrics=SetMetrics(duration_s=60.0))
    md = session_markdown(s)
    assert "the dead joke" in md
    assert "silent" in md
