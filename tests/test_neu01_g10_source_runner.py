"""G10 prospective runner synthetic/adversarial controls: no publisher I/O."""
from __future__ import annotations

from hashlib import md5, sha256
from io import BytesIO

import pytest

from experiments import neu01_g10_source_runner as runner
from experiments import neu01_g10_pre_source as frozen


class FakeResponse(BytesIO):
    def __init__(self, content: bytes, url: str):
        super().__init__(content)
        self.url = url

    def geturl(self) -> str:
        return self.url


def test_sidecar_shas_and_sizes_frozen_in_original_eight_order():
    assert len(runner.SIDE_CARS) == 8
    assert len(frozen.PAIRS) == 8
    assert runner.SIDE_CARS[4] == (
        "0a616db5642e313354e310e4fe8c1be029e6a355", 593
    )
    assert runner.SIDE_CARS[5] == (
        "5a9d79eeb2df07b9f6b7801e25671547b294e772", 597
    )


def test_frozen_source_url_does_not_allow_source_fallback():
    pair = frozen.PAIRS[0]
    expected = frozen.publisher_url(pair, "root")
    with pytest.raises(runner.SourceUnavailable, match="REDIRECT"):
        runner.fetch_authenticated(
            pair, "root", opener=lambda req, timeout: FakeResponse(
                b"not a source", "https://other.invalid/source"
            )
        )
    assert expected.startswith("https://s3.amazonaws.com/openneuro.org/ds004148/")


def test_empty_truncated_body_not_authenticated(monkeypatch):
    pair = frozen.PAIRS[0]
    monkeypatch.setattr(frozen, "ROOT_BYTES", 12)
    with pytest.raises(runner.SourceUnavailable, match="SIZE_MISMATCH"):
        runner.fetch_authenticated(
            pair, "root", opener=lambda req, timeout: FakeResponse(
                b"a" * 11, req.full_url
            )
        )


def test_oversized_binary_not_authenticated(monkeypatch):
    pair = frozen.PAIRS[0]
    monkeypatch.setattr(frozen, "ROOT_BYTES", 10)
    with pytest.raises(runner.SourceUnavailable, match="EXCEEDS"):
        runner.fetch_authenticated(
            pair, "root", opener=lambda req, timeout: FakeResponse(
                b"a" * 11, req.full_url
            )
        )


def test_original_publisher_md5_is_required(monkeypatch):
    pair = frozen.PAIRS[0]
    content = b"synthetic only"
    monkeypatch.setattr(frozen, "ROOT_BYTES", len(content))
    with pytest.raises(runner.SourceUnavailable, match="MD5_MISMATCH"):
        runner.fetch_authenticated(
            pair, "root", opener=lambda req, timeout: FakeResponse(
                content, req.full_url
            )
        )


def test_exact_synthetic_publisher_MD5_and_independent_sha(monkeypatch):
    old_pair = frozen.PAIRS[0]
    content = b"fixed synthetic bytes"
    patched = frozen.Pair(old_pair.subject, old_pair.session, old_pair.task,
                          md5(content).hexdigest(), old_pair.header_md5,
                          old_pair.derivative_md5)
    monkeypatch.setattr(frozen, "PAIRS", (patched,))
    monkeypatch.setattr(frozen, "ROOT_BYTES", len(content))
    got, identity = runner.fetch_authenticated(
        patched, "root", opener=lambda req, timeout: FakeResponse(
            content, req.full_url
        )
    )
    assert got == content
    assert identity["source_body_sha256"] == sha256(content).hexdigest()
    assert identity["publisher_pointer_md5_verified"] is True


def test_wrong_publisher_TSV_git_blob_rejected():
    pair = frozen.PAIRS[0]
    with pytest.raises(runner.SourceUnavailable, match="SIZE_MISMATCH"):
        runner.fetch_authenticated(
            pair, "channels", opener=lambda req, timeout: FakeResponse(
                b"not the published 983-byte source", req.full_url
            )
        )


def test_sidecar_channel_class_disagreement_recorded_not_silently_reclassified():
    pair = frozen.PAIRS[4]
    content = b'{"SamplingFrequency": 500, "RecordingDuration": 300, "EEGChannelCount": 60, "MiscChannelCount": 1, "EEGReference": "FCz"}'
    info = runner.inspect_sidecar(content, pair)
    assert info["source_sidecar_classification_disagrees_with_tsv"] is True
    assert info["total_eeg_plus_misc"] == 61
    assert info["eeg_channel_count_declared"] == 60
    assert info["amplifier_origin_or_preprocessing_history_proven"] is False


def test_sidecar_does_not_claim_unread_or_malformed_metadata_eligible():
    pair = frozen.PAIRS[0]
    with pytest.raises(runner.EligibilityFailure, match="UNREADABLE"):
        runner.inspect_sidecar(b"{", pair)
    with pytest.raises(runner.EligibilityFailure, match="GRID"):
        runner.inspect_sidecar(
            b'{"SamplingFrequency": 256, "RecordingDuration": 300, "EEGChannelCount": 61, "MiscChannelCount": 0}',
            pair,
        )
    with pytest.raises(runner.EligibilityFailure, match="NOT_INTEGERS"):
        runner.inspect_sidecar(
            b'{"SamplingFrequency": 500, "RecordingDuration": 300, "EEGChannelCount": "61", "MiscChannelCount": 0}',
            pair,
        )
