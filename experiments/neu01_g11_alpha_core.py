"""NEU-01 G11: frozen alpha relationship and power retest statistics.

No file or network access occurs in this module. The core contains no fitted
subject parameters, waveform labels, phase optimization, or electrode searches.
"""
from __future__ import annotations

import numpy as np

CHANNELS = 61
FRAMES = 150_000
RATE = 500
SAMPLES_PER_EPOCH = 1_000
EPOCHS = 150
BAND_LOW = 8.0
BAND_HIGH = 12.0
FREQS = np.fft.rfftfreq(SAMPLES_PER_EPOCH, d=1 / RATE)
ALPHA_MASK = (FREQS >= BAND_LOW) & (FREQS <= BAND_HIGH)
ALPHA_BINS = 9
EDGE_COUNT = CHANNELS * (CHANNELS - 1) // 2
SUBJECTS = 12
PERMUTATIONS = 20_000
PERMUTATION_SEED = 1101


class MeasurementIneligible(ValueError):
    """A numerical input violates the frozen G11 measurement contract."""


def alpha_fourier_coefficients(native_samples: np.ndarray) -> np.ndarray:
    """All 150 disjoint, demeaned, Hann-windowed two-second epochs."""
    if not isinstance(native_samples, np.ndarray) or native_samples.shape != (
        FRAMES, CHANNELS
    ):
        raise MeasurementIneligible("G11_WRONG_NATIVE_FRAME_OR_CHANNEL_SHAPE")
    if native_samples.dtype.kind != "f" or native_samples.dtype.itemsize != 4:
        raise MeasurementIneligible("G11_SOURCE_MUST_BE_NATIVE_FLOAT32")
    if not bool(np.all(np.isfinite(native_samples))):
        raise MeasurementIneligible("G11_NONFINITE_ORIGINAL_EEG_SAMPLES")
    if int(np.count_nonzero(ALPHA_MASK)) != ALPHA_BINS:
        raise MeasurementIneligible("G11_ALPHA_FREQUENCY_BIN_CONTRACT_BROKEN")

    raw = native_samples.reshape(EPOCHS, SAMPLES_PER_EPOCH, CHANNELS).astype(
        np.float64, copy=False
    )
    centered = raw - raw.mean(axis=1, keepdims=True)
    weighted = centered * np.hanning(SAMPLES_PER_EPOCH)[None, :, None]
    coeff = np.fft.rfft(weighted, axis=1)[:, ALPHA_MASK, :]
    if coeff.shape != (EPOCHS, ALPHA_BINS, CHANNELS):
        raise MeasurementIneligible("G11_WRONG_FFT_CUBE_SHAPE")
    if not bool(np.all(np.isfinite(coeff))):
        raise MeasurementIneligible("G11_NONFINITE_ALPHA_FOURIER_VALUES")
    return coeff


def _validate_cube(coeff: np.ndarray) -> None:
    if not isinstance(coeff, np.ndarray) or coeff.shape != (
        EPOCHS, ALPHA_BINS, CHANNELS
    ):
        raise MeasurementIneligible("G11_INVALID_FOURIER_CUBE_SHAPE")
    if coeff.dtype.kind != "c" or not bool(np.all(np.isfinite(coeff))):
        raise MeasurementIneligible("G11_INVALID_COMPLEX_FOURIER_DATA")


def _power_and_graph(coeff: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _validate_cube(coeff)
    flat = np.ascontiguousarray(coeff).reshape(EPOCHS * ALPHA_BINS, CHANNELS)
    powers = np.sum(np.abs(flat) ** 2, axis=0, dtype=np.float64)
    if not bool(np.all(np.isfinite(powers))) or bool(np.any(powers <= 0)):
        raise MeasurementIneligible("G11_ZERO_OR_NONFINITE_ALPHA_POWER")
    cross = flat.T @ flat.conj()
    denominator = np.sqrt(powers[:, None]) * np.sqrt(powers[None, :])
    coherency = cross / denominator
    graph = np.abs(np.imag(coherency))[
        np.triu_indices(CHANNELS, k=1)
    ]
    if graph.size != EDGE_COUNT or not bool(np.all(np.isfinite(graph))):
        raise MeasurementIneligible("G11_GRAPH_FEATURE_INVALID")
    if bool(np.any(graph < -1e-10)) or bool(np.any(graph > 1 + 1e-10)):
        raise MeasurementIneligible("G11_COHERENCY_OUT_OF_THEORETICAL_BOUNDS")
    return graph.astype(np.float64), powers


def epoch_shuffled(coeff: np.ndarray, *, seed: int) -> np.ndarray:
    """Within each sensor independently permute complete epoch FFT vectors."""
    _validate_cube(coeff)
    rng = np.random.default_rng(seed)
    out = np.empty_like(coeff)
    for channel in range(CHANNELS):
        order = rng.permutation(EPOCHS)
        out[:, :, channel] = coeff[order, :, channel]
    # The shuffle conserves power mathematically. Float summation is order-sensitive;
    # allow only roundoff-scale relative differences, never material power changes.
    original = np.sum(np.abs(coeff) ** 2, axis=(0, 1))
    shuffled = np.sum(np.abs(out) ** 2, axis=(0, 1))
    if not np.allclose(original, shuffled, rtol=1e-12, atol=0.0):
        raise MeasurementIneligible("G11_EPOCH_SHUFFLE_CHANGED_CHANNEL_POWER")
    return out


def compute_three_features(coeff: np.ndarray, *,
                           participant_number: int, session: int) -> dict[str, np.ndarray]:
    """Graph, spectral baseline, and a single declared epoch-shuffle control."""
    if not (10 <= participant_number <= 21 and session in (1, 3)):
        raise MeasurementIneligible("G11_UNREGISTERED_SUBJECT_SESSION")
    graph, powers = _power_and_graph(coeff)
    shuffled = epoch_shuffled(coeff, seed=1101 + 10 * participant_number + session)
    null_graph, null_powers = _power_and_graph(shuffled)
    if not np.allclose(powers, null_powers, rtol=1e-12, atol=0.0):
        raise MeasurementIneligible("G11_POWER_CHANGED_BY_NEGATIVE_CONTROL")
    power_features = np.log(powers)
    if not bool(np.all(np.isfinite(power_features))):
        raise MeasurementIneligible("G11_LOG_POWER_NOT_FINITE")
    return {
        "graph": graph,
        "power": power_features,
        "shuffled_graph": null_graph,
    }


def pearson_cross_sessions(first: np.ndarray, last: np.ndarray) -> np.ndarray:
    """Frozen Pearson similarity; constant signatures are ineligible."""
    if (not isinstance(first, np.ndarray) or not isinstance(last, np.ndarray)
            or first.ndim != 2 or first.shape != last.shape
            or first.shape[0] != SUBJECTS
            or first.shape[1] not in (EDGE_COUNT, CHANNELS)):
        raise MeasurementIneligible("G11_INCOMPATIBLE_RETEST_FINGERPRINTS")
    if not bool(np.all(np.isfinite(first))) or not bool(np.all(np.isfinite(last))):
        raise MeasurementIneligible("G11_NONFINITE_FINGERPRINT")
    a = np.asarray(first, dtype=np.float64)
    b = np.asarray(last, dtype=np.float64)
    a = a - a.mean(axis=1, keepdims=True)
    b = b - b.mean(axis=1, keepdims=True)
    a_norm = np.linalg.norm(a, axis=1)
    b_norm = np.linalg.norm(b, axis=1)
    if (bool(np.any(a_norm <= 0)) or bool(np.any(b_norm <= 0))
            or not bool(np.all(np.isfinite(a_norm)))
            or not bool(np.all(np.isfinite(b_norm)))):
        raise MeasurementIneligible("G11_ZERO_VARIANCE_RETEST_FINGERPRINT")
    corr = (a / a_norm[:, None]) @ (b / b_norm[:, None]).T
    if corr.shape != (SUBJECTS, SUBJECTS) or not bool(np.all(np.isfinite(corr))):
        raise MeasurementIneligible("G11_INVALID_SIMILARITY_MATRIX")
    return np.clip(corr, -1.0, 1.0)


def diagnostic(similarity: np.ndarray) -> dict:
    if (not isinstance(similarity, np.ndarray)
            or similarity.shape != (SUBJECTS, SUBJECTS)
            or not bool(np.all(np.isfinite(similarity)))):
        raise MeasurementIneligible("G11_INVALID_SUBJECT_SIMILARITY")
    selected = np.diag(similarity)
    between = (float(np.sum(similarity)) - float(np.sum(selected))) / (
        SUBJECTS * (SUBJECTS - 1)
    )
    within = float(np.mean(selected))
    max_by_row = np.max(similarity, axis=1)
    # A tie, even at one floating-point value, cannot count as identification.
    unique = np.sum(similarity == max_by_row[:, None], axis=1) == 1
    correct = (selected == max_by_row) & unique
    return {
        "mean_within": within,
        "mean_between": between,
        "d": within - between,
        "unique_correct": int(np.count_nonzero(correct)),
        "denominator": SUBJECTS,
        "per_subject_unique_correct": [bool(x) for x in correct],
    }


def primary_permutation_p(similarity: np.ndarray, *, count: int = PERMUTATIONS,
                          seed: int = PERMUTATION_SEED) -> dict:
    if count != PERMUTATIONS or seed != PERMUTATION_SEED:
        raise MeasurementIneligible("G11_UNREGISTERED_PERMUTATION_CONTRACT")
    observed = diagnostic(similarity)["d"]
    rng = np.random.default_rng(seed)
    i = np.arange(SUBJECTS)
    total = float(np.sum(similarity))
    extreme = 0
    for _ in range(PERMUTATIONS):
        perm = rng.permutation(SUBJECTS)
        diag = float(np.sum(similarity[i, perm]))
        different = (total - diag) / (SUBJECTS * (SUBJECTS - 1))
        d_perm = diag / SUBJECTS - different
        if d_perm >= observed:
            extreme += 1
    return {
        "permutations": PERMUTATIONS,
        "seed": PERMUTATION_SEED,
        "extreme_count": extreme,
        "p_one_sided": (1 + extreme) / (PERMUTATIONS + 1),
        "observed_d": observed,
    }


def complete_analysis(first: list[dict[str, np.ndarray]],
                      last: list[dict[str, np.ndarray]]) -> dict:
    if len(first) != SUBJECTS or len(last) != SUBJECTS:
        raise MeasurementIneligible("G11_ALL_TWELVE_SUBJECTS_REQUIRED")
    families = ("graph", "power", "shuffled_graph")
    matrices = {}
    diagnostics = {}
    for family in families:
        a = np.stack([r[family] for r in first])
        b = np.stack([r[family] for r in last])
        mat = pearson_cross_sessions(a, b)
        matrices[family] = mat
        diagnostics[family] = diagnostic(mat)
    p_test = primary_permutation_p(matrices["graph"])
    increment = (
        diagnostics["graph"]["unique_correct"] > diagnostics["power"]["unique_correct"]
        and diagnostics["graph"]["d"] > diagnostics["power"]["d"]
    )
    shifted_control = diagnostics["graph"]["d"] > diagnostics["shuffled_graph"]["d"]
    support = p_test["p_one_sided"] < 0.05 and increment and shifted_control
    return {
        "study": "NEU-01-G11-P01",
        "status": ("G11_COMPLETE_RELATIONAL_PATTERN_SUPPORT_WITHIN_SCOPE" if support
                   else "G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT"),
        "subjects": SUBJECTS,
        "sessions": [1, 3],
        "eye_condition": "eyesclosed",
        "all_requested_source_records_eligible": True,
        "primary_permutation": p_test,
        "feature_diagnostics": diagnostics,
        "spectral_only_increment_both_criteria": increment,
        "aligned_beats_independent_epoch_shuffle": shifted_control,
        "similarity_matrices": {
            k: v.tolist() for k, v in matrices.items()
        },
        "subject_identity_or_biological_causal_mechanism_tested": False,
        "no_raw_signal_values_published": True,
    }
