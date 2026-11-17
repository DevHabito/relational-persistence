"""G11 original-file runner: synthetic-only source gates and chronology checks."""
from __future__ import annotations

from hashlib import md5, sha256
from io import BytesIO

import pytest

from experiments import neu01_g11_source_runner as runner
from experiments import neu01_g11_alpha_core as core


class FakeResponse(BytesIO):
    def __init__(self, data: bytes, url: str):
        super().__init__(data)
        self.url = url

    def geturl(self) -> str:
        return self.url


def test_frozen_manifest_has_24_distinct_sources_and_prior_archive_intact():
    runner.check_frozen_evidence()
    assert len(runner.SOURCES) == 24
    assert [s.subject for s in runner.SOURCES[::2]] == list(runner.SUBJECTS)
    assert len({s.eeg_md5 for s in runner.SOURCES}) == 24
    assert len({s.header_md5 for s in runner.SOURCES}) == 24
    assert runner.PROTOCOL_COMMIT == "3c86a3b89ffacfc27c5136a5d1a696a56404733d"


def test_session_paths_are_frozen_and_derivative_not_allowed():
    first, last = runner.SOURCES[0], runner.SOURCES[1]
    assert runner.relative_path(first, "eeg") == (
        "sub-10/ses-session1/eeg/sub-10_ses-session1_task-eyesclosed_eeg.eeg"
    )
    assert runner.relative_path(last, "vhdr") == (
        "sub-10/ses-session3/eeg/sub-10_ses-session3_task-eyesclosed_eeg.vhdr"
    )
    assert runner.pinned_url(first, "eeg").startswith(runner.SOURCE_ROOT)
    with pytest.raises(runner.SourceFailure, match="FILE_EXTENSION"):
        runner.relative_path(first, "set")
    with pytest.raises(runner.SourceFailure, match="UNREGISTERED"):
        runner.relative_path(
            runner.Source("sub-10", 2, first.eeg_md5, first.header_md5), "eeg"
        )


def test_synthetic_authenticated_small_binary_and_sha(monkeypatch):
    original = runner.SOURCES[0]
    fake = b"synthetic only, not human EEG"
    pinned = runner.Source(
        original.subject, original.session, md5(fake).hexdigest(), original.header_md5
    )
    monkeypatch.setattr(runner, "SOURCES", (pinned,))
    monkeypatch.setattr(runner, "ROOT_BYTES", len(fake))
    body, identity = runner.authenticate_bytes(
        pinned, "eeg", opener=lambda req, timeout: FakeResponse(fake, req.full_url)
    )
    assert body == fake
    assert identity["published_body_sha256"] == sha256(fake).hexdigest()
    assert identity["publisher_pointer_md5_verified"] is True


def test_wrong_size_redirect_and_md5_cannot_be_accepted(monkeypatch):
    pair = runner.SOURCES[0]
    data = b"not an EEG"
    monkeypatch.setattr(runner, "ROOT_BYTES", len(data))
    with pytest.raises(runner.SourceFailure, match="REDIRECT"):
        runner.authenticate_bytes(
            pair, "eeg",
            opener=lambda req, timeout: FakeResponse(data, "https://other.invalid")
        )
    with pytest.raises(runner.SourceFailure, match="MD5_MISMATCH"):
        runner.authenticate_bytes(
            pair, "eeg",
            opener=lambda req, timeout: FakeResponse(data, req.full_url)
        )
    with pytest.raises(runner.SourceFailure, match="EXCEEDS"):
        runner.authenticate_bytes(
            pair, "eeg",
            opener=lambda req, timeout: FakeResponse(data + b"Z", req.full_url)
        )
    with pytest.raises(runner.SourceFailure, match="SIZE_MISMATCH"):
        runner.authenticate_bytes(
            pair, "eeg",
            opener=lambda req, timeout: FakeResponse(data[:-1], req.full_url)
        )


def synthetic_header(pair) -> bytes:
    name = runner.relative_path(pair, "eeg").rsplit("/", 1)[-1]
    lines = [
        "Brain Vision Data Exchange Header File Version 1.0",
        "[Common Infos]",
        "DataFile=" + name,
        "MarkerFile=" + name[:-4] + ".vmrk",
        "DataFormat=BINARY",
        "DataOrientation=MULTIPLEXED",
        "NumberOfChannels=61",
        "SamplingInterval=2000",
        "[Binary Infos]",
        "BinaryFormat=IEEE_FLOAT_32",
        "[Channel Infos]",
    ]
    lines.extend(f"Ch{k}=C{k},,1," for k in range(1, 62))
    return ("\n".join(lines) + "\n").encode("latin-1")


def test_wrong_session_header_and_sampling_rate_rejected():
    pair = runner.SOURCES[0]
    body = synthetic_header(pair)
    with pytest.raises(runner.HeaderFailure, match="LABELS"):
        runner.original_header_labels(body, pair)
    with pytest.raises(runner.HeaderFailure, match="TIME_GRID"):
        runner.original_header_labels(
            body.replace(b"SamplingInterval=2000", b"SamplingInterval=4000"),
            pair,
        )
    with pytest.raises(runner.HeaderFailure, match="TIME_GRID"):
        runner.original_header_labels(body, runner.SOURCES[1])
    with pytest.raises(runner.HeaderFailure, match="FLOAT32"):
        runner.original_header_labels(
            body.replace(b"IEEE_FLOAT_32", b"INT_16"), pair
        )


def test_invalid_channel_labels_and_duplicate_indices_rejected():
    pair = runner.SOURCES[0]
    body = synthetic_header(pair)
    with pytest.raises(runner.HeaderFailure, match="CHANNEL_RESOLUTION"):
        runner.original_header_labels(body.replace(b"Ch1=C1,,1,", b"Ch1=C1,,2,"), pair)
    with pytest.raises(runner.HeaderFailure, match="CHANNEL_INDICES"):
        runner.original_header_labels(body.replace(b"Ch61=C61,,1,", b""), pair)
    with pytest.raises(runner.HeaderFailure, match="DUPLICATE"):
        runner.original_header_labels(body.replace(b"Ch61=C61,,1,", b"Ch60=C61,,1,"), pair)


def test_fail_closed_complete_analysis_requires_all_twelve_records():
    with pytest.raises(core.MeasurementIneligible, match="TWELVE"):
        core.complete_analysis([], [])
    assert runner.ROOT_BYTES == 36_600_000
    assert runner.HEADER_BYTES == 1_122
