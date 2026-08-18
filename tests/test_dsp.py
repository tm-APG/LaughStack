import numpy as np
import pytest

from laughstack.dsp import (
    detect_cal_tone, gcc_phat, modulation_rate, spectral_flatness,
    estimate_rt60, decay_time, decompose_stacked, NLMSCanceller,
    band_coherence,
)
from conftest import SR, cal_tone, laugh_burst, applause_burst, quiet_room


def test_cal_tone_found_at_offset(rng):
    x = np.concatenate([
        quiet_room(5.0, rng=rng),
        cal_tone(3.0),
        quiet_room(5.0, rng=rng),
    ])
    tone = detect_cal_tone(x, SR)
    assert tone is not None
    assert tone.offset_s == pytest.approx(5.0, abs=0.2)
    assert tone.duration_s == pytest.approx(3.0, abs=0.5)
    assert tone.level_dbfs == pytest.approx(20 * np.log10(0.25 / np.sqrt(2)), abs=1.5)


def test_cal_tone_absent(rng):
    x = quiet_room(20.0, rng=rng)
    assert detect_cal_tone(x, SR) is None


def test_gcc_phat_recovers_known_delay(rng):
    n = SR * 2
    a = rng.standard_normal(n)
    delay = 120  # samples
    b = np.concatenate([np.zeros(delay), a[:-delay]])
    d, peak = gcc_phat(a, b, SR, max_delay_s=0.05)
    assert d == pytest.approx(delay / SR, abs=1.0 / SR)


def test_modulation_rate_separates_laugh_from_applause(rng):
    laugh = laugh_burst(3.0, mod_hz=5.0, rng=rng)
    clap = applause_burst(3.0, rng=rng)
    m_laugh, peak_hz = modulation_rate(laugh, SR)
    m_clap, _ = modulation_rate(clap, SR)
    assert m_laugh > m_clap
    assert 3.0 <= peak_hz <= 8.0
    assert m_laugh > 0.35


def test_spectral_flatness_orders_sources(rng):
    tone = cal_tone(2.0)
    clap = applause_burst(2.0, rng=rng)
    assert spectral_flatness(clap, SR) > spectral_flatness(tone, SR)


def test_rt60_of_synthetic_decay():
    # exponential decay engineered for RT60 = 0.6 s
    rt60 = 0.6
    t = np.arange(int(1.5 * SR)) / SR
    rng = np.random.default_rng(7)
    ir = rng.standard_normal(len(t)) * np.exp(-6.91 * t / rt60)
    est = estimate_rt60(ir, SR)
    assert est == pytest.approx(rt60, rel=0.15)


def test_decay_time_rt60_correction():
    # envelope decaying at exactly the room rate: corrected decay ≈ 0
    sr_env = 50.0
    rt60 = 1.0
    t = np.arange(int(3 * sr_env)) / sr_env
    env = np.exp(-np.log(10 ** (60 / 20)) * t / rt60)  # -60 dB over rt60
    raw = decay_time(env, sr_env, 0, drop_db=20.0)
    corrected = decay_time(env, sr_env, 0, drop_db=20.0, rt60_s=rt60)
    assert raw == pytest.approx(rt60 * 20 / 60, rel=0.1)
    assert corrected == pytest.approx(0.0, abs=0.05)


def test_decompose_stacked_pure_inheritance():
    # tag window is exactly the parent's continuing decay: excess ≈ 0
    sr_env = 50.0
    t = np.arange(int(4 * sr_env)) / sr_env
    env = np.exp(-t / 0.5)
    d = decompose_stacked(env, sr_env, parent_peak_idx=0,
                          tag_start_idx=int(1.0 * sr_env),
                          tag_end_idx=int(2.0 * sr_env))
    assert d.excess_ratio < 0.1


def test_decompose_stacked_genuine_tag():
    # tag re-lifts the envelope well above the parent's decay
    sr_env = 50.0
    t = np.arange(int(4 * sr_env)) / sr_env
    env = np.exp(-t / 0.5)
    tag_start = int(1.0 * sr_env)
    tag_end = int(2.0 * sr_env)
    env2 = env.copy()
    env2[tag_start:tag_end] += 0.8  # big new laugh
    d = decompose_stacked(env2, sr_env, 0, tag_start, tag_end)
    assert d.excess_ratio > 0.8
    assert d.excess_energy > 0


def test_nlms_cancels_bleed_but_freeze_protects_laugh(rng):
    """Reference (stage feed) bleeding into an audience mic gets cancelled;
    with the freeze mask on during the 'laugh', the laugh survives."""
    n = SR * 4
    stage = rng.standard_normal(n) * 0.3
    # bleed: simple attenuation + small delay
    delay = 40
    bleed = 0.5 * np.concatenate([np.zeros(delay), stage[:-delay]])
    laugh = np.zeros(n)
    seg = laugh_burst(1.0, rng=rng)
    laugh[2 * SR:2 * SR + len(seg)] = seg
    primary = bleed + laugh

    freeze = np.zeros(n, dtype=bool)
    freeze[2 * SR:3 * SR] = True

    c = NLMSCanceller(n_taps=64, mu=0.5)
    out = c.process(primary, stage, freeze_mask=freeze)

    # bleed region (after convergence, before laugh) strongly attenuated
    pre = slice(int(1.5 * SR), 2 * SR)
    assert np.std(out[pre]) < 0.3 * np.std(primary[pre])
    # laugh region retains most of the laugh's energy
    lg = slice(2 * SR, 2 * SR + len(seg))
    corr = np.corrcoef(out[lg], laugh[lg])[0, 1]
    assert corr > 0.7


def test_band_coherence_room_wide_vs_local(rng):
    n = SR * 2
    shared = laugh_burst(2.0, rng=rng)
    mic_a = shared + 0.02 * rng.standard_normal(n)[:len(shared)]
    mic_b = shared + 0.02 * rng.standard_normal(n)[:len(shared)]
    local_a = rng.standard_normal(len(shared)) * 0.2
    local_b = rng.standard_normal(len(shared)) * 0.2
    coh_shared = band_coherence(mic_a, mic_b, SR)
    coh_local = band_coherence(local_a, local_b, SR)
    assert coh_shared > 0.8
    assert coh_local < 0.3
