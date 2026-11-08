"""RP-U005-D02 synthetic-fixture checks only — no original ANEEL rows used."""
from datetime import datetime, timedelta, timezone
import subprocess
import sys

import pytest

from experiments import rp_u005_aneel_schema_preflight as p


CNPJ = "12345678000190"  # Deliberately invented fixture, not a distributor ID.
OTHER_CNPJ = "98765432000112"  # Deliberately invented fixture.
UTC = timezone.utc
T0 = datetime(2026, 3, 3, 10, 0, tzinfo=UTC)


def emergency(ident="000123", company=CNPJ, year="2026"):
    return {
        "NumCnpjDistribuidora": company,
        "NumAnoCompetencia": year,
        "CodOcorrenciaEmergencial": ident,
    }


def interruption(ident="000123", company=CNPJ, year="2026", number="001"):
    return {
        "NumCNPJDistribuidora": company,
        "AnoCompetencia": year,
        "CodOcorrencia": ident,
        "CodInterrupcao": number,
    }


def test_2026_publisher_text_field_catalog_is_not_a_byte_validation():
    result = p.schema_presence(
        set(p.OCCURRENCE_2026), set(p.INTERRUPTION_2026),
    )
    assert result["syntactic_presence"] is True
    assert result["source_pdf_bytes_verified"] is False
    assert result["original_2026_rows_scanned"] is False
    assert result["semantic_crosswalk_verified"] is False
    assert result["physical_U004_repair_interventions_verified"] is False


def test_pre2026_columns_do_not_silently_pass_2026_schema():
    result = p.schema_presence(
        set(p.OLD_OCCURRENCE_FIELDS), set(p.OLD_INTERRUPTION_FIELDS)
    )
    assert result["syntactic_presence"] is False
    assert "CodOcorrenciaEmergencial" in result["missing_occurrence_fields"]
    assert "CodOcorrencia" in result["missing_interruption_fields"]
    assert "NumTempoExecucao" in result["missing_occurrence_fields"]


def test_candidate_identifier_preserves_leading_zeroes_and_scope():
    assert p.candidate_key(CNPJ, "2026", "000123").occurrence_id == "000123"
    assert p.candidate_key(CNPJ, "2026", "123") != p.candidate_key(
        CNPJ, "2026", "000123"
    )
    assert p.candidate_key(CNPJ, "2026", "000123") != p.candidate_key(
        OTHER_CNPJ, "2026", "000123"
    )
    assert p.candidate_key(CNPJ, "2026", "000123") != p.candidate_key(
        CNPJ, "2025", "000123"
    )


@pytest.mark.parametrize(
    "bad",
    [
        (12345678000190, "2026", "000123"),
        ("123", "2026", "000123"),
        (CNPJ, 2026, "000123"),
        (CNPJ, "2026", 123),
        (CNPJ, "2026", ""),
        (CNPJ, "2026", " 000123"),
        (CNPJ, "2026", "00000000000"),
    ],
)
def test_invalid_candidate_keys_are_rejected(bad):
    with pytest.raises(p.SourceGateError):
        p.candidate_key(*bad)


def test_exact_one_to_one_fixture_reports_counts_but_not_semantic_proof():
    result = p.pair_candidate_rows([emergency()], [interruption()])
    assert result.unambiguous_occurrences == 1
    assert result.matched_interruption_records == 1
    assert result.multiple_interruption_matches == 0
    assert result.audited_original_rows == 0


def test_company_and_year_mismatches_not_falsely_joined():
    result = p.pair_candidate_rows(
        [emergency()],
        [interruption(company=OTHER_CNPJ), interruption(year="2025")],
    )
    assert result.unambiguous_occurrences == 0
    assert result.unmatched_occurrences == 1
    assert result.unmatched_interruptions == 2
    assert result.matched_interruption_records == 0


def test_multiple_associated_interruptions_cannot_be_hidden():
    result = p.pair_candidate_rows(
        [emergency()],
        [interruption(number="001"), interruption(number="002")],
    )
    assert result.multiple_interruption_matches == 1
    assert result.unambiguous_occurrences == 0
    assert result.matched_interruption_records == 2
    assert result.audited_original_rows == 0


def test_duplicate_emergency_key_is_a_fatal_ambiguity():
    with pytest.raises(p.SourceGateError, match="Duplicate occurrence"):
        p.pair_candidate_rows([emergency(), emergency()], [interruption()])


def test_no_online_feature_from_event_time_without_receive_time():
    with pytest.raises(p.SourceGateError, match="receipt/availability"):
        p.causal_feature("CodAlimentador", "F001", T0-timedelta(hours=1), None, T0)


def test_genuine_prior_receipt_fixture_is_allowed_without_claiming_real_data():
    sample = p.causal_feature(
        "CodAlimentador", "F001", T0-timedelta(hours=2),
        T0-timedelta(hours=1), T0,
    )
    assert sample == "F001"


@pytest.mark.parametrize("blocked", sorted(p.POSSIBLY_POST_OUTCOME | p.PUBLICATION_ONLY))
def test_outcome_and_publication_fields_never_enter_prediagnosis_features(blocked):
    with pytest.raises(p.SourceGateError, match="Outcome/publication"):
        p.causal_feature(
            blocked, 0, T0-timedelta(hours=1),
            T0-timedelta(minutes=1), T0,
        )


@pytest.mark.parametrize("offset", [0, 1])
def test_same_time_or_future_arrival_is_not_prior_information(offset):
    with pytest.raises(p.SourceGateError, match="Future or same-time"):
        p.causal_feature(
            "CodAlimentador", "F001",
            T0-timedelta(hours=1), T0+timedelta(seconds=offset), T0,
        )


def test_damaged_or_timezone_naive_intervals_fail_closed():
    with pytest.raises(p.SourceGateError):
        p.timestamp_interval(T0, T0-timedelta(seconds=1))
    with pytest.raises(p.SourceGateError):
        p.timestamp_interval(T0.replace(tzinfo=None), T0)
    p.timestamp_interval(T0, T0)


def test_optimized_python_cannot_disable_source_gates():
    probe = (
        "from experiments.rp_u005_aneel_schema_preflight import "
        "candidate_key; candidate_key(123, '2026', '001')"
    )
    run = subprocess.run(
        [sys.executable, "-O", "-c", probe],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert run.returncode != 0
    assert "Distributor CNPJ" in run.stderr


def test_decision_preserves_unknown_and_negative_findings():
    result = p.declared_decision()
    assert result["original_outcome_records_read"] == 0
    assert result["join_on_original_rows"] == "NOT_TESTED"
    assert result["historical_online_receipt"] == "NOT_CERTIFIED"
    assert result["contemporaneous_topology"] == "NOT_CERTIFIED"
    assert result["real_policy_comparison_supported"] is False
    assert result["decision"] == "CANDIDATE_FOR_SEPARATE_SOURCE_ONLY_AUDIT"


def test_normally_open_tie_is_not_an_energized_second_path():
    """Synthetic demonstration of the *installed* versus *active* graph gap.

    Vertices 0 and 3 are terminals; the normally open 0--3 tie exists in
    the built network but not in its radially energized state. This is a
    finite topology illustration, not a physical feeder observation.
    """
    def f2(edge_list):
        links = {v: set() for v in range(4)}
        for a, b in edge_list:
            links[a].add(b)
            links[b].add(a)
        complete = []

        def visit(route):
            if route[-1] == 3:
                complete.append(route)
                return
            for candidate in links[route[-1]]:
                if candidate not in route:
                    visit(route + (candidate,))

        visit((0,))
        return any(
            set(path[1:-1]).isdisjoint(other[1:-1])
            for idx, path in enumerate(complete)
            for other in complete[idx + 1:]
        )

    active_tree = ((0, 1), (1, 2), (2, 3))
    installed_with_open_tie = active_tree + ((0, 3),)
    assert f2(active_tree) is False
    assert f2(installed_with_open_tie) is True
