import pytest

from laughstack.models import (LaughEvent, TranscriptSegment, Session,
                               JokeInstance, EventKind)
from laughstack.align import align, mark_stacked, bit_id_for
from laughstack.metrics import normalize_events
from laughstack.compare import (joke_similarity, match_jokes, ab_compare)


def seg(start, end, text):
    return TranscriptSegment(start_s=start, end_s=end, text=text)


def ev(start, end, peak=-20.0, energy=1.0):
    return LaughEvent(start_s=start, end_s=end, peak_dbfs=peak, energy=energy)


def test_align_attaches_laugh_to_preceding_segment():
    transcript = [
        seg(0, 4, "so I went to the doctor last week"),
        seg(4, 8, "and he said sir this is a Wendy's"),
        seg(12, 16, "anyway my dog is in therapy now"),
    ]
    events = [ev(8.3, 11.0)]
    jokes = align(events, transcript, set_duration_s=60.0)
    scored = [j for j in jokes if j.events]
    assert len(scored) == 1
    assert scored[0].punchline_text == "and he said sir this is a Wendy's"
    assert scored[0].latency_s == pytest.approx(0.3)
    assert "doctor" in scored[0].setup_text
    # the trailing dog segment drew nothing -> kept as a silent instance
    silent = [j for j in jokes if not j.events]
    assert len(silent) == 1
    assert "dog" in silent[0].punchline_text


def test_align_unaligned_event_kept():
    events = [ev(30.0, 32.0)]
    jokes = align(events, [seg(0, 3, "hello everybody")], set_duration_s=60.0)
    unaligned = [j for j in jokes if j.events]
    assert len(unaligned) == 1
    assert unaligned[0].bit_id.startswith("unaligned")
    assert unaligned[0].punchline_text == ""
    # the greeting drew nothing and is kept as a silent instance
    assert any(not j.events and j.punchline_text == "hello everybody"
               for j in jokes)


def test_mark_stacked_links_close_events():
    events = [ev(10, 13), ev(13.5, 15), ev(30, 31)]
    mark_stacked(events, stack_window_s=1.5)
    assert events[1].parent_index == 0
    assert events[2].parent_index is None


def test_bit_id_stable_under_whitespace_and_case():
    assert bit_id_for("My Dog  is in THERAPY") == bit_id_for("my dog is in therapy")


def test_joke_similarity_matches_reworded_joke():
    a = "so my landlord finally fixed the heater in my apartment"
    b = "my landlord fixed the heater in the apartment finally"
    assert joke_similarity(a, b) > 0.6
    assert joke_similarity(a, "completely different premise about airplanes") < 0.2


def make_session(session_id, punch_text, energy_rel):
    ji = JokeInstance(bit_id=bit_id_for(punch_text), setup_text="my landlord story",
                      punchline_text=punch_text, punchline_end_s=100.0,
                      events=[ev(100.5, 103.0)], latency_s=0.5,
                      position_in_set=0.5)
    ji.events[0].rel_energy = energy_rel
    ji.events[0].rel_peak = energy_rel
    return Session(session_id=session_id, jokes=[ji])


def test_match_and_ab_compare():
    a = make_session("fri_late", "landlord fixed the heater with a hammer", 0.2)
    b = make_session("tue_mic", "landlord finally fixed that heater with a hammer", 1.4)
    matches = match_jokes([a, b], min_similarity=0.5)
    assert len(matches) == 1
    r = ab_compare(matches[0], "fri_late", "tue_mic")
    assert r is not None
    assert r.delta_energy_rel == pytest.approx(1.2)
    assert "tue_mic" in r.verdict


def test_ab_flags_position_confound():
    a = make_session("s1", "the heater joke about my landlord", 0.0)
    b = make_session("s2", "the heater joke about my landlord", 1.0)
    a.jokes[0].position_in_set = 0.1
    b.jokes[0].position_in_set = 0.9
    matches = match_jokes([a, b], min_similarity=0.5)
    r = ab_compare(matches[0], "s1", "s2")
    assert r.position_confound == pytest.approx(0.8)
    assert "CAUTION" in r.verdict


def test_silent_punchline_emitted():
    """A punchline followed by a pause and no laugh stays in the tables."""
    transcript = [
        seg(0, 8, "so my grandmother wanted to try an escape room"),
        seg(8, 12, "she solved it immediately, she escaped Poland in the forties"),
        # 6-second pause: the comic waited, nothing came
        seg(18, 24, "anyway I tried a meal kit subscription"),
        seg(24, 27, "it's just groceries with homework"),
    ]
    events = [ev(27.3, 30.0)]
    jokes = align(events, transcript, set_duration_s=60.0)
    assert len(jokes) == 2
    silent = jokes[0]
    assert silent.punchline_text.startswith("she solved it")
    assert silent.events == []
    scored = jokes[1]
    assert scored.punchline_text == "it's just groceries with homework"
    # the dead bit's text must not leak into the next joke's setup
    assert "Poland" not in scored.setup_text
    assert "meal kit" in scored.setup_text
