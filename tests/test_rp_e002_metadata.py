"""Synthetic metadata fixtures exercise the read-only source gate."""

from experiments.rp_e002_metadata import audit


def test_structured_legacy_license_and_expected_file():
    record = {
        "id": 5146275,
        "metadata": {
            "doi": "10.5281/zenodo.5146275",
            "license": {"id": "cc-by-4.0"},
            "access_right": "open",
        },
        "files": [{
            "key": "METR-LA.csv",
            "checksum": "md5:d3adaa79856bf610f25558fc242c7190",
            "size": 72700000,
        }],
    }
    result = audit(record)
    assert result["pinned_checksum_matches"] is True
    assert result["record_license_identified"] is True
    assert result["upstream_pems_rights_independently_verified"] is False
    assert result["ready_for_empirical_score_without_more_checks"] is False


def test_unrecognized_checksum_is_a_stop_not_a_guess():
    record = {
        "id": 5146275,
        "metadata": {},
        "files": [{"key": "METR-LA.csv", "checksum": "md5:wrong"}],
    }
    result = audit(record)
    assert result["pinned_checksum_matches"] is False
    assert result["record_license_identified"] is False
    assert result["ready_for_empirical_score_without_more_checks"] is False


def test_new_rights_schema_only_identifies_license():
    record = {
        "metadata": {"rights": [{"id": "cc-by-4.0"}]},
        "files": [],
    }
    result = audit(record)
    assert "cc-by-4.0" in result["license_identifiers"]
    assert not result["pinned_checksum_matches"]
    assert not result["ready_for_empirical_score_without_more_checks"]
