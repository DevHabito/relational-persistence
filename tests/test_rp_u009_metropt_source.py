"""U009 archive-authentication synthetic tests, never touching UCI telemetry."""
from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from experiments import rp_u009_metropt_core as core
from experiments import rp_u009_metropt_source as source


def test_only_one_exact_source_member_and_frozen_url():
    assert source.FIRST_OUTPUT.as_posix()==(
        "docs/results/RP-U009-P01-first-run/audit.json"
    )
    assert source.PRE_SOURCE_COMMIT=="744f00af2bc94a87fbe119bea2dd0e7fee791b82"
    assert source.SOURCE_DOWNLOAD_TIMEOUT_SECONDS==120


def test_source_zip_authentic_member_accepted_with_synthetic_payload(tmp_path):
    path=tmp_path/"ordinary.zip"
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("Data Description_Metro.pdf",b"synthetic")
        z.writestr("MetroPT3(AirCompressor).csv",
                   b"timestamp,Reservoirs,Motor_current,LPS\n")
    with zipfile.ZipFile(path) as z:
        member=source.verified_member(z)
        assert member.filename==core.ORIGINAL_CSV_BASENAME
        assert source.csv_identity(z,member)[
            "original_csv_uncompressed_bytes"]>10


def test_source_zip_prevents_zip_slip_and_duplicate_basename(tmp_path):
    path=tmp_path/"malicious.zip"
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("../MetroPT3(AirCompressor).csv",b"evil")
    with zipfile.ZipFile(path) as z:
        with pytest.raises(core.InvalidEvidence,match="UNSAFE_MEMBER_PATH"):
            source.verified_member(z)
    duplicate=tmp_path/"duplicate.zip"
    with zipfile.ZipFile(duplicate,"w") as z:
        z.writestr("one/MetroPT3(AirCompressor).csv",b"x")
        z.writestr("two/MetroPT3(AirCompressor).csv",b"x")
    with zipfile.ZipFile(duplicate) as z:
        with pytest.raises(core.InvalidEvidence,match="EXACTLY_ONE"):
            source.verified_member(z)


def test_original_study_runner_cannot_replace_unverified_sensor_archive(tmp_path):
    path=tmp_path/"not-a-real-zip.zip"
    path.write_bytes(b"not actual original UCI archive")
    with pytest.raises(zipfile.BadZipFile):
        source.study_one_time(path)
