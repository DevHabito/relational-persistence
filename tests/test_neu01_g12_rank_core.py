"""G12 pre-source synthetic, adversarial and negative-result controls.

No original participant, EEG source file or publisher URL is used by these tests.
"""
from __future__ import annotations

import numpy as np
import pytest

from experiments import neu01_g12_rank_core as g
from experiments import neu01_g11_alpha_core as previous


def test_contract_and_fixed_weights():
    assert g.SUBJECTS == tuple(range(22, 34))
    assert g.SAMPLE_SESSIONS == (1, 3)
    assert g.N == 12
    assert g.LABEL_PERMUTATIONS == 20_000
    assert (g.FUSION_POWER_WEIGHT, g.FUSION_GRAPH_WEIGHT) == (0.5, 0.5)


def test_rank_scaling_follows_relative_order_without_raw_similarity_scale():
    matrix = np.tile(np.arange(12, dtype=float), (12, 1))
    q = g.within_row_rank(matrix)
    assert np.all(q[:, -1] == 1.0)
    assert np.all(q[:, 0] == 0.0)
    assert np.array_equal(q, g.within_row_rank(10 * matrix + 7.0))
    with pytest.raises(g.G12Ineligible, match="TWELVE_BY_TWELVE"):
        g.within_row_rank(np.ones((11, 12)))
    with pytest.raises(g.G12Ineligible, match="TWELVE_BY_TWELVE"):
        bad = matrix.copy()
        bad[2, 7] = np.nan
        g.within_row_rank(bad)


def test_average_rank_ties_and_no_success_from_tied_maximum():
    matrix = np.eye(12)
    matrix[0, 1] = 1.0
    ranks = g.within_row_rank(matrix)
    assert ranks[0, 0] == ranks[0, 1]
    result = g.unique_predictions(matrix)
    assert result[0] == -1
    assert result[1] == 1
    assert g.correct_flags(matrix)[0] is False
    assert sum(g.correct_flags(matrix)) == 11


def test_exact_discordance_does_not_treat_equality_as_a_gain():
    correct = [True] * 7 + [False] * 5
    same = g.paired_discordance(correct, correct)
    assert same["net_gain"] == 0
    assert same["one_sided_exact_discordance_p"] == 1
    extra = g.paired_discordance([True]*12, [False]*5+[True]*7)
    assert extra["improved_count"] == 5 and extra["harmed_count"] == 0
    assert extra["one_sided_exact_discordance_p"] == 1/32
    with pytest.raises(g.G12Ineligible, match="BOOLS"):
        g.paired_discordance([1]*12, [False]*12)


def test_permutation_reference_is_reproducible_and_uses_20k_new_seed():
    perfect = np.eye(12, dtype=float)
    wrong = np.roll(perfect, 1, axis=1)
    a = g.label_permutation_reference(perfect, wrong)
    b = g.label_permutation_reference(perfect, wrong)
    assert a == b
    assert a["observed_net_match_gain"] == 12
    assert a["seed"] == 1202 and a["permutations"] == 20000
    assert a["not_a_power_conditional_null"] is True


def test_strict_negative_result_with_equal_identification_to_power():
    graph = np.eye(12)
    power = np.eye(12)
    shuffled = np.eye(12) * .1
    result = g.compute_from_matrices(graph, power, shuffled)
    assert result["model_correct_counts"]["fixed_equal_fusion"] == 12
    assert result["model_correct_counts"]["power_only"] == 12
    assert result["paired_exact_test"]["net_gain"] == 0
    assert result["status"] == "G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT"


def test_negative_result_when_phase_edges_conflict_with_spectral_matches():
    graph = np.roll(np.eye(12, dtype=float), 1, axis=1)
    power = np.eye(12, dtype=float)
    shuffled = np.roll(graph, 1, axis=1)
    result = g.compute_from_matrices(graph, power, shuffled)
    assert result["model_correct_counts"]["fixed_equal_fusion"] <= 12
    assert result["paired_exact_test"]["net_gain"] <= 0
    assert result["status"] == "G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT"


def test_source_features_reuse_predeclared_g11_estimator():
    rng = np.random.default_rng(12)
    coeff = (
        rng.standard_normal((150, 9, 61)) +
        1j * rng.standard_normal((150, 9, 61))
    )
    observed = g.compute_features(coeff, participant=22, session=1)
    parent_graph, parent_power = previous._power_and_graph(coeff)
    assert np.array_equal(observed["graph"], parent_graph)
    assert np.array_equal(observed["power"], np.log(parent_power))
    assert observed["shuffled_graph"].shape == (1830,)
    with pytest.raises(g.G12Ineligible, match="UNREGISTERED"):
        g.compute_features(coeff, participant=10, session=1)
    with pytest.raises(g.G12Ineligible, match="UNREGISTERED"):
        g.compute_features(coeff, participant=22, session=2)


def test_constant_features_rejected_prior_to_subject_fusion():
    g11_single = {"graph": np.ones(1830), "power": np.ones(61), "shuffled_graph":np.ones(1830)}
    with pytest.raises(ValueError, match="ZERO_VARIANCE"):
        g.evaluate_retest([g11_single]*12, [g11_single]*12)
    with pytest.raises(g.G12Ineligible, match="PAIRED_PARTICIPANTS"):
        g.evaluate_retest([], [])
