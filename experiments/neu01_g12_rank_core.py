"""NEU-01/G12 offline phase/power rank-fusion experiment.

The source-independent implementation is frozen against its protocol; it never
loads G12 EEG or optimizes weights, frequencies, subjects or electrode choices.
"""
from __future__ import annotations

from math import comb

import numpy as np
from scipy.stats import rankdata

from experiments import neu01_g11_alpha_core as g11

SUBJECTS = tuple(range(22, 34))
N = len(SUBJECTS)
SAMPLE_SESSIONS = (1, 3)
FUSION_POWER_WEIGHT = 0.5
FUSION_GRAPH_WEIGHT = 0.5
SURROGATE_SEED_OFFSET = 1202
LABEL_PERMUTATION_SEED = 1202
LABEL_PERMUTATIONS = 20_000

class G12Ineligible(ValueError):
    """Falsifiable, non-adaptive study admission or measurement failure."""


def compute_features(coeff: np.ndarray, *, participant: int, session: int) -> dict:
    """Apply unchanged G11 numeric feature definitions to G12 held-out subjects."""
    if participant not in SUBJECTS or session not in SAMPLE_SESSIONS:
        raise G12Ineligible("UNREGISTERED_G12_SUBJECT_OR_SESSION")
    graph, powers = g11._power_and_graph(coeff)
    shuffled = g11.epoch_shuffled(
        coeff, seed=SURROGATE_SEED_OFFSET + 10 * participant + session
    )
    null_graph, null_powers = g11._power_and_graph(shuffled)
    if not np.allclose(powers, null_powers, rtol=1e-12, atol=0):
        raise G12Ineligible("G12_SURROGATE_CHANGED_ALPHA_POWER")
    return {
        "graph": graph,
        "power": np.log(powers),
        "shuffled_graph": null_graph,
    }


def require_matrix(matrix: np.ndarray) -> None:
    if (not isinstance(matrix, np.ndarray) or matrix.shape != (N, N)
            or not bool(np.all(np.isfinite(matrix)))):
        raise G12Ineligible("G12_INVALID_TWELVE_BY_TWELVE_SIMILARITY")


def within_row_rank(matrix: np.ndarray) -> np.ndarray:
    """No training: scale all rows to within-row ordered fractional ranks."""
    require_matrix(matrix)
    ranks = rankdata(-matrix, axis=1, method="average")
    result = (N - ranks) / (N - 1)
    if not bool(np.all(np.isfinite(result))) or bool(np.any(result < 0)):
        raise G12Ineligible("G12_INVALID_RANK_NORMALIZATION")
    return result


def unique_predictions(matrix: np.ndarray) -> np.ndarray:
    """Return -1 for tied top scores; no first-index tie-breaking."""
    require_matrix(matrix)
    maxima = np.max(matrix, axis=1)
    tied = np.count_nonzero(matrix == maxima[:, None], axis=1) != 1
    result = np.argmax(matrix, axis=1).astype(np.int64)
    result[tied] = -1
    return result


def correct_flags(matrix: np.ndarray) -> list[bool]:
    result = unique_predictions(matrix)
    return [bool(result[i] == i) for i in range(N)]


def paired_discordance(better: list[bool], baseline: list[bool]) -> dict:
    if len(better) != N or len(baseline) != N:
        raise G12Ineligible("G12_ALL_TWELVE_PAIRED_ROWS_REQUIRED")
    if any(type(v) is not bool for v in better + baseline):
        raise G12Ineligible("G12_PAIRED_OUTCOMES_MUST_BE_BOOLS")
    improved = sum(g and not p for g, p in zip(better, baseline, strict=True))
    harmed = sum(p and not g for g, p in zip(better, baseline, strict=True))
    n = improved + harmed
    probability = (
        1.0 if n == 0 else
        sum(comb(n, k) for k in range(improved, n + 1)) / 2**n
    )
    return {
        "improved_count": improved,
        "harmed_count": harmed,
        "net_gain": improved - harmed,
        "discordant": n,
        "one_sided_exact_discordance_p": probability,
        "independent_rows_assumption_not_established": True,
    }


def label_permutation_reference(fusion: np.ndarray, baseline: np.ndarray) -> dict:
    """Only the declared joint-label exchangeability null, not a conditional model."""
    prediction_f = unique_predictions(fusion)
    prediction_p = unique_predictions(baseline)
    rng = np.random.default_rng(LABEL_PERMUTATION_SEED)
    actual = int(np.sum(prediction_f == np.arange(N))) - int(
        np.sum(prediction_p == np.arange(N))
    )
    extreme = 0
    for _ in range(LABEL_PERMUTATIONS):
        assignment = rng.permutation(N)
        diff = int(np.sum(prediction_f == assignment)) - int(
            np.sum(prediction_p == assignment)
        )
        if diff >= actual:
            extreme += 1
    return {
        "seed": LABEL_PERMUTATION_SEED,
        "permutations": LABEL_PERMUTATIONS,
        "observed_net_match_gain": actual,
        "extreme_count": extreme,
        "one_sided_joint_label_reference_p": (1 + extreme) / (
            1 + LABEL_PERMUTATIONS
        ),
        "not_a_power_conditional_null": True,
    }


def compute_from_matrices(graph: np.ndarray, power: np.ndarray,
                          shuffled: np.ndarray) -> dict:
    """Exact G12 predeclared outcomes, including failures and no-tune controls."""
    graph_q = within_row_rank(graph)
    power_q = within_row_rank(power)
    shuffled_q = within_row_rank(shuffled)
    fusion = FUSION_POWER_WEIGHT * power_q + FUSION_GRAPH_WEIGHT * graph_q
    null_fusion = FUSION_POWER_WEIGHT * power_q + FUSION_GRAPH_WEIGHT * shuffled_q
    models = {
        "power_only": power_q, "graph_only": graph_q,
        "shuffled_graph_only": shuffled_q,
        "fixed_equal_fusion": fusion, "fixed_shuffle_fusion": null_fusion,
    }
    correct = {key: correct_flags(v) for key, v in models.items()}
    count = {key: sum(v) for key, v in correct.items()}
    paired = paired_discordance(
        correct["fixed_equal_fusion"], correct["power_only"]
    )
    p_reference = label_permutation_reference(fusion, power_q)
    if p_reference["observed_net_match_gain"] != paired["net_gain"]:
        raise G12Ineligible("G12_INDEPENDENT_NET_GAIN_ACCOUNTING_CONFLICT")
    support = (
        paired["net_gain"] >= 2
        and paired["one_sided_exact_discordance_p"] < 0.05
        and count["fixed_equal_fusion"] > count["fixed_shuffle_fusion"]
    )
    return {
        "study": "NEU-01-G12-P01",
        "status": (
            "G12_COMPLETE_FIXED_FUSION_INCREMENT_WITHIN_SCOPE" if support else
            "G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT"
        ),
        "participants": list(SUBJECTS),
        "sessions": list(SAMPLE_SESSIONS),
        "fixed_fusion_power_weight": FUSION_POWER_WEIGHT,
        "fixed_fusion_graph_weight": FUSION_GRAPH_WEIGHT,
        "model_correct_counts": count,
        "model_correct_flags": correct,
        "paired_exact_test": paired,
        "joint_label_permutation_diagnostic": p_reference,
        "similarity_matrices": {
            "graph": graph.tolist(), "power": power.tolist(),
            "shuffled_graph": shuffled.tolist(),
        },
        "unit_rank_matrices": {
            "graph": graph_q.tolist(), "power": power_q.tolist(),
            "shuffled_graph": shuffled_q.tolist(),
            "fixed_equal_fusion": fusion.tolist(),
            "fixed_shuffle_fusion": null_fusion.tolist(),
        },
        "source_waveforms_published": False,
        "physiological_causes_or_intervention_recovery_proven": False,
    }


def evaluate_retest(first: list[dict], last: list[dict]) -> dict:
    """Reject missing participants and reuse validated G11 Pearson comparison."""
    if len(first) != N or len(last) != N:
        raise G12Ineligible("G12_ALL_TWELVE_PAIRED_PARTICIPANTS_REQUIRED")
    matrix = {}
    for family in ("graph", "power", "shuffled_graph"):
        a = np.stack([f[family] for f in first])
        b = np.stack([f[family] for f in last])
        matrix[family] = g11.pearson_cross_sessions(a, b)
    return compute_from_matrices(
        matrix["graph"], matrix["power"], matrix["shuffled_graph"]
    )
