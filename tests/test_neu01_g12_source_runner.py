"""G12 strict source runner pre-data controls; only artificial byte bodies."""
from __future__ import annotations

from hashlib import md5, sha256
from io import BytesIO

import pytest

from experiments import neu01_g12_source_runner as runner


class FakeResponse(BytesIO):
    def __init__(self, body: bytes, url: str):
        super().__init__(body)
        self.url = url

    def geturl(self) -> str:
        return self.url


def test_publisher_manifest_has_exactly_twenty_four_complete_hashes():
    runner.verify_prior_and_manifest()
    assert len(runner.SOURCES) == 24
    assert runner.SUBJECTS == tuple(f"sub-{i}" for i in range(22, 34))
    assert all(len(s.root_md5) == len(s.header_md5) == 32 for s in runner.SOURCES)
    assert len({s.root_md5 for s in runner.SOURCES}) == 24
    assert len({s.header_md5 for s in runner.SOURCES}) == 24


def test_exact_session_source_paths_no_derivative_or_substitution():
    pair = runner.SOURCES[0]
    assert runner.source_path(pair, "eeg") == (
        "sub-22/ses-session1/eeg/sub-22_ses-session1_task-eyesclosed_eeg.eeg"
    )
    assert runner.source_path(runner.SOURCES[1], "vhdr") == (
        "sub-22/ses-session3/eeg/sub-22_ses-session3_task-eyesclosed_eeg.vhdr"
    )
    with pytest.raises(runner.SourceFailure, match="UNREGISTERED"):
        runner.source_path(runner.Source("sub-22", 2, pair.root_md5, pair.header_md5), "eeg")
    with pytest.raises(runner.SourceFailure, match="FORMAT"):
        runner.source_path(pair, "set")


def test_source_digest_verification_on_declared_synthetic_only_payload(monkeypatch):
    original = runner.SOURCES[0]
    body = b"G12 synthetic digest body not actual EEG"
    fake = runner.Source(original.subject, original.session,
                         md5(body).hexdigest(), original.header_md5)
    monkeypatch.setattr(runner, "SOURCES", (fake,))
    monkeypatch.setattr(runner, "ROOT_BYTES", len(body))
    observed, identity = runner.authenticated_source(
        fake, "eeg", opener=lambda req, timeout: FakeResponse(body, req.full_url)
    )
    assert observed == body
    assert identity["actual_original_sha256"] == sha256(body).hexdigest()
    assert identity["publisher_MD5_body_verified"]


def test_url_redirect_truncation_and_wrong_md5_stopped(monkeypatch):
    source = runner.SOURCES[0]
    data = b"source synthetic"
    monkeypatch.setattr(runner, "ROOT_BYTES", len(data))
    with pytest.raises(runner.SourceFailure, match="REDIRECT"):
        runner.authenticated_source(
            source, "eeg", opener=lambda req, timeout: FakeResponse(data, "https://fake.invalid")
        )
    with pytest.raises(runner.SourceFailure, match="SIZE"):
        runner.authenticated_source(
            source, "eeg", opener=lambda req, timeout: FakeResponse(data[:-1], req.full_url)
        )
    with pytest.raises(runner.SourceFailure, match="EXCEEDS"):
        runner.authenticated_source(
            source, "eeg", opener=lambda req, timeout: FakeResponse(data + b"*", req.full_url)
        )
    with pytest.raises(runner.SourceFailure, match="MD5"):
        runner.authenticated_source(
            source, "eeg", opener=lambda req, timeout: FakeResponse(data, req.full_url)
        )


def fake_header(source) -> bytes:
    root = runner.source_path(source, "eeg").rsplit("/", 1)[-1]
    head = [
        "Brain Vision Data Exchange Header File Version 1.0",
        "[Common Infos]",
        f"DataFile={root}",
        f"MarkerFile={root[:-4]}.vmrk",
        "DataFormat=BINARY",
        "DataOrientation=MULTIPLEXED",
        "NumberOfChannels=61",
        "SamplingInterval=2000",
        "[Binary Infos]",
        "BinaryFormat=IEEE_FLOAT_32",
        "[Channel Infos]",
    ]
    head.extend(f"Ch{i}=C{i},,1," for i in range(1, 62))
    return ("\n".join(head) + "\n").encode("latin-1")


def test_header_rejects_wrong_montage_framerate_and_session():
    source = runner.SOURCES[0]
    body = fake_header(source)
    with pytest.raises(runner.MetadataFailure, match="ORDER"):
        runner.header_electrodes(body, source)
    with pytest.raises(runner.MetadataFailure, match="GRID"):
        runner.header_electrodes(
            body.replace(b"SamplingInterval=2000", b"SamplingInterval=4000"), source
        )
    with pytest.raises(runner.MetadataFailure, match="GRID"):
        runner.header_electrodes(body, runner.SOURCES[1])
    with pytest.raises(runner.MetadataFailure, match="FLOAT_32"):
        runner.header_electrodes(body.replace(b"IEEE_FLOAT_32", b"INT_16"), source)


def test_header_rejects_malformed_channels():
    pair = runner.SOURCES[0]
    body = fake_header(pair)
    with pytest.raises(runner.MetadataFailure, match="CHANNEL_INDEX_SET"):
        runner.header_electrodes(body.replace(b"Ch61=C61,,1,", b""), pair)
    with pytest.raises(runner.MetadataFailure, match="RESOLUTION"):
        runner.header_electrodes(body.replace(b"Ch61=C61,,1,", b"Ch61=C61,,2,"), pair)
    with pytest.raises(runner.MetadataFailure, match="DUPLICATE"):
        runner.header_electrodes(body.replace(b"Ch1=C1,,1,", b"Ch1=C1,,1,\nCh1=C1,,1,"), pair)
