"""G11 synthetic pre-source validation: no original EEG access."""
from __future__ import annotations

import numpy as np
import pytest

from experiments import neu01_g11_alpha_core as g


def _cube() -> np.ndarray:
    rng = np.random.default_rng(19)
    amplitude = rng.uniform(0.2, 2.0, (g.EPOCHS, g.ALPHA_BINS, g.CHANNELS))
    phase = rng.uniform(-np.pi, np.pi, (g.EPOCHS, g.ALPHA_BINS, g.CHANNELS))
    return amplitude * np.exp(1j * phase)


def test_frozen_alpha_bin_count_and_graph_dimension():
    assert g.ALPHA_MASK.sum() == 9
    assert g.FREQS[g.ALPHA_MASK].tolist() == [
        8., 8.5, 9., 9.5, 10., 10.5, 11., 11.5, 12.
    ]
    assert g.EPOCHS == 150
    assert g.SAMPLES_PER_EPOCH == 1000
    assert g.EDGE_COUNT == 1830


def test_graph_positive_sensor_gain_invariance_and_spectral_noninvariance():
    c = _cube()
    original_graph, power = g._power_and_graph(c)
    gain = np.linspace(.25, 8., g.CHANNELS)
    modified_graph, modified_power = g._power_and_graph(c * gain[None, None, :])
    assert np.allclose(original_graph, modified_graph, atol=1e-12, rtol=0)
    assert not np.allclose(np.log(power), np.log(modified_power))
    assert np.all(original_graph >= 0) and np.all(original_graph <= 1 + 1e-10)


def test_shuffled_epochs_preserve_each_sensor_power_and_are_deterministic():
    c = _cube()
    shuffled = g.epoch_shuffled(c, seed=1101)
    shuffled_again = g.epoch_shuffled(c, seed=1101)
    assert np.array_equal(shuffled, shuffled_again)
    assert np.allclose(
        np.sum(np.abs(c) ** 2, axis=(0, 1)),
        np.sum(np.abs(shuffled) ** 2, axis=(0, 1)),
        rtol=1e-12, atol=0.0,
    )
    assert not np.array_equal(c, shuffled)


def test_shuffling_breaks_known_epoch_coherent_phase_pairs():
    rng = np.random.default_rng(20)
    phase = rng.uniform(-np.pi, np.pi, g.EPOCHS)
    c = np.zeros((g.EPOCHS, g.ALPHA_BINS, g.CHANNELS), dtype=complex)
    for channel in range(g.CHANNELS):
        c[:, :, channel] = np.exp(1j * (phase[:, None] + channel * .027))
    aligned_graph, _ = g._power_and_graph(c)
    scrambled_graph, _ = g._power_and_graph(g.epoch_shuffled(c, seed=1101))
    assert aligned_graph.mean() > scrambled_graph.mean() + .1


def test_fourier_cube_rejects_zero_alpha_power_and_invalid_shape():
    c = _cube()
    c[:, :, 0] = 0
    with pytest.raises(g.MeasurementIneligible, match="ZERO_OR_NONFINITE"):
        g._power_and_graph(c)
    with pytest.raises(g.MeasurementIneligible, match="CUBE_SHAPE"):
        g._power_and_graph(c[:3])
    with pytest.raises(g.MeasurementIneligible, match="FOURIER_DATA"):
        broken = _cube()
        broken[0, 0, 0] = np.nan
        g._power_and_graph(broken)


def test_real_fft_returns_declared_nine_bins_with_finite_synthetic_waveforms():
    t = np.arange(g.FRAMES, dtype=np.float64) / g.RATE
    oscillation = np.sin(2 * np.pi * 10.0 * t)
    # Positive alpha power in all 61 channels, before any human source access.
    wave = (oscillation[:, None] * np.linspace(.2, 1.5, g.CHANNELS)).astype("<f4")
    coeff = g.alpha_fourier_coefficients(wave)
    assert coeff.shape == (150, 9, 61)
    _, powers = g._power_and_graph(coeff)
    assert np.all(powers > 0)
    with pytest.raises(g.MeasurementIneligible, match="SOURCE_MUST"):
        g.alpha_fourier_coefficients(wave.astype("<f8"))
    with pytest.raises(g.MeasurementIneligible, match="FRAME_OR_CHANNEL"):
        g.alpha_fourier_coefficients(wave[:-1])
    with pytest.raises(g.MeasurementIneligible, match="NONFINITE"):
        broken = wave.copy()
        broken[0, 0] = np.nan
        g.alpha_fourier_coefficients(broken)


def test_fixed_retest_similarity_and_permutation_are_reproducible():
    rng = np.random.default_rng(71)
    inputs = rng.normal(size=(12, 1830))
    results = inputs + rng.normal(scale=.03, size=inputs.shape)
    similarity = g.pearson_cross_sessions(inputs, results)
    result = g.diagnostic(similarity)
    assert result["unique_correct"] == 12
    assert result["d"] > 0
    p = g.primary_permutation_p(similarity)
    assert p == g.primary_permutation_p(similarity)
    assert p["permutations"] == 20000
    assert p["p_one_sided"] < .05


def test_identification_rejects_ties_and_mismatched_rows():
    tie = np.ones((12, 12))
    assert g.diagnostic(tie)["unique_correct"] == 0
    assert g.diagnostic(tie)["d"] == 0
    with pytest.raises(g.MeasurementIneligible, match="ALL_TWELVE"):
        g.complete_analysis([], [])
    with pytest.raises(g.MeasurementIneligible, match="SIMILARITY"):
        g.diagnostic(np.ones((3, 3)))
    with pytest.raises(g.MeasurementIneligible, match="ZERO_VARIANCE"):
        g.pearson_cross_sessions(np.ones((12, 61)), np.ones((12, 61)))


def test_feature_extraction_rejects_unregistered_subject_or_session():
    c = _cube()
    with pytest.raises(g.MeasurementIneligible, match="UNREGISTERED"):
        g.compute_three_features(c, participant_number=2, session=1)
    with pytest.raises(g.MeasurementIneligible, match="UNREGISTERED"):
        g.compute_three_features(c, participant_number=10, session=2)
    observed = g.compute_three_features(c, participant_number=10, session=1)
    assert set(observed) == {"graph", "power", "shuffled_graph"}
    assert observed["graph"].shape == (1830,)
    assert observed["power"].shape == (61,)
    assert observed["shuffled_graph"].shape == (1830,)


def test_registration_does_not_treat_a_power_only_feature_as_relational():
    rng = np.random.default_rng(4)
    first = []
    last = []
    for i in range(12):
        sample = {
            "graph": rng.normal(size=1830),
            "power": rng.normal(size=61),
            "shuffled_graph": rng.normal(size=1830),
        }
        another = {
            "graph": rng.normal(size=1830),
            "power": sample["power"].copy(),
            "shuffled_graph": rng.normal(size=1830),
        }
        first.append(sample)
        last.append(another)
    result = g.complete_analysis(first, last)
    assert result["status"] == "G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT"
    assert result["feature_diagnostics"]["power"]["unique_correct"] == 12
    assert result["spectral_only_increment_both_criteria"] is False
