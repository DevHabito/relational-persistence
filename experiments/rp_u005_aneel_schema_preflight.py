"""RP-U005-D02: conservative, fixture-only source and temporal linkage gates.

No original ANEEL data files have been read by this module.
The two published 2026 dictionary PDFs were seen as extracted text, but
the direct source bytes have not been authenticated and a viewer conflict
was observed. This module cannot certify that any real records match.

Tests operate only on explicitly constructed synthetic examples. Passing a
fixture is not evidence that its identifiers or time assumptions hold in
an actual distributor's records.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence


OCCURRENCE_2026 = frozenset({
    "NumCnpjDistribuidora", "CodOcorrenciaEmergencial",
    "CodAlimentador", "CodSubestacao", "DthIniOcorrencia",
    "DthFimOcorrencia", "NumTempoPreparacao",
    "NumTempoDeslocamento", "NumTempoExecucao",
})
INTERRUPTION_2026 = frozenset({
    "NumCNPJDistribuidora", "CodOcorrencia", "CodInterrupcao",
    "CodAlimentador", "CodSubestacao",
    "DatInicioInterrupcao", "DatFimInterrupcao",
    "QtdConsumidoresAfetados",
})
# The documented pre-2026 schema is not an alias of the 2026 schema.
OLD_OCCURRENCE_FIELDS = frozenset({
    "NumOcorrencia", "MdaPreparo", "MdaDeslocamento",
    "MdaExecucao", "DscNumInterrupcao",
})
OLD_INTERRUPTION_FIELDS = frozenset({
    "NumOrdemInterrupcao", "DscAlimentadorSubestacao",
})
# Deliberately conservative: whether affected-customer counts are available
# earlier varies by real system and must be checked separately.
POSSIBLY_POST_OUTCOME = frozenset({
    "DthFimOcorrencia", "NumTempoExecucao", "DatFimInterrupcao",
    "QtdConsumidoresAfetados",
})
PUBLICATION_ONLY = frozenset({"DatGeracaoConjuntoDados"})


class SourceGateError(ValueError):
    """Fail-closed data identity or causal-time ambiguity."""


@dataclass(frozen=True)
class CandidateLink:
    company: str
    year: str
    occurrence_id: str


@dataclass(frozen=True)
class JoinCensus:
    occurrence_records: int
    interruption_records: int
    unambiguous_occurrences: int
    unmatched_occurrences: int
    unmatched_interruptions: int
    multiple_interruption_matches: int
    matched_interruption_records: int
    audited_original_rows: int = 0


def schema_presence(
    occurrence_columns: set[str], interruption_columns: set[str]
) -> dict:
    """A syntactic check; never a real-byte verification or field semantical proof."""
    _typed = all(isinstance(s, str) for s in occurrence_columns | interruption_columns)
    if not _typed:
        raise SourceGateError("Non-string column name")
    missing_occ = sorted(OCCURRENCE_2026 - occurrence_columns)
    missing_interrupt = sorted(INTERRUPTION_2026 - interruption_columns)
    return {
        "missing_occurrence_fields": missing_occ,
        "missing_interruption_fields": missing_interrupt,
        "syntactic_presence": not missing_occ and not missing_interrupt,
        "source_pdf_bytes_verified": False,
        "original_2026_rows_scanned": False,
        "semantic_crosswalk_verified": False,
        "physical_U004_repair_interventions_verified": False,
    }


def candidate_key(company: object, year: object, ident: object) -> CandidateLink:
    """No integer coercion or stripping: leading zeroes must survive."""
    if not (isinstance(company, str) and company.isascii() and
            len(company) == 14 and company.isdecimal()):
        raise SourceGateError("Distributor CNPJ must be 14 unchanged decimal characters")
    if not (isinstance(year, str) and len(year) == 4 and
            year.isascii() and year.isdecimal()):
        raise SourceGateError("Year must be a four-character decimal string")
    if not (isinstance(ident, str) and 0 < len(ident) <= 30 and
            ident == ident.strip()):
        raise SourceGateError("Occurrence ID absent or ambiguously normalized")
    return CandidateLink(company, year, ident)


def pair_candidate_rows(
    occurrence_rows: Sequence[Mapping[str, str]],
    interruption_rows: Sequence[Mapping[str, str]],
) -> JoinCensus:
    """Disclose missing and one-to-many matches; never silently pick a winner.

    This is an *illustration on synthetic fixtures* only. Company, year and
    occurrence identifier are candidate conditions; distributor-defined
    semantics and uniqueness must still be established from real data.
    """
    occurrences = {}
    for row in occurrence_rows:
        key = candidate_key(
            row["NumCnpjDistribuidora"], row["NumAnoCompetencia"],
            row["CodOcorrenciaEmergencial"],
        )
        if key in occurrences:
            raise SourceGateError("Duplicate occurrence key: cannot claim unique join")
        occurrences[key] = row
    outages_by_key = defaultdict(list)
    for row in interruption_rows:
        key = candidate_key(
            row["NumCNPJDistribuidora"], row["AnoCompetencia"],
            row["CodOcorrencia"],
        )
        outages_by_key[key].append(row)
    matches = [len(outages_by_key.get(key, [])) for key in occurrences]
    matched = sum(n for n in matches)
    unmatched = sum(
        len(v) for key, v in outages_by_key.items() if key not in occurrences
    )
    return JoinCensus(
        occurrence_records=len(occurrence_rows),
        interruption_records=len(interruption_rows),
        unambiguous_occurrences=sum(n == 1 for n in matches),
        unmatched_occurrences=sum(n == 0 for n in matches),
        unmatched_interruptions=unmatched,
        multiple_interruption_matches=sum(n > 1 for n in matches),
        matched_interruption_records=matched,
    )


def causal_feature(
    name: str, value: object, event_timestamp: datetime,
    received_timestamp: datetime | None, origin: datetime
) -> object:
    """Strictly historical feature availability; event time is not receipt time.

    The publisher's generation timestamp and post-outcome values are never
    accepted as predecision features in this conservative feasibility gate.
    """
    if name in POSSIBLY_POST_OUTCOME | PUBLICATION_ONLY:
        raise SourceGateError("Outcome/publication field is not a certified predecision feature")
    if event_timestamp.tzinfo is None or origin.tzinfo is None:
        raise SourceGateError("Timezone-aware timestamps required")
    if received_timestamp is None or received_timestamp.tzinfo is None:
        raise SourceGateError("Decision-time receipt/availability not certified")
    if event_timestamp >= origin or received_timestamp >= origin:
        raise SourceGateError("Future or same-time information rejected")
    return value


def timestamp_interval(start: datetime, end: datetime) -> None:
    """Negative guard on temporal order, not a statement about real source values."""
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise SourceGateError("Invalid or ambiguous event interval")


def declared_decision() -> dict:
    """Metadata-only conclusion; no provider bytes or policy effects observed."""
    return {
        "protocol": "RP-U005-D02",
        "audit_class": "RETROSPECTIVE_SOURCE_METADATA_PREFLIGHT",
        "publisher": "ANEEL",
        "schema_text_candidate": "2026 dictionaries, original PDF bytes not independently verified",
        "original_outcome_records_read": 0,
        "join_on_original_rows": "NOT_TESTED",
        "historical_online_receipt": "NOT_CERTIFIED",
        "contemporaneous_topology": "NOT_CERTIFIED",
        "real_edge_repair_actions": "NOT_CERTIFIED",
        "real_decision_costs": "NOT_CERTIFIED",
        "real_U004_F2_endpoint": "NOT_CERTIFIED",
        "decision": "CANDIDATE_FOR_SEPARATE_SOURCE_ONLY_AUDIT",
        "real_policy_comparison_supported": False,
    }
