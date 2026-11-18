"""RP-U008 source authentication, without downloading or analyzing original data."""
from __future__ import annotations

from io import BytesIO

import pytest

from experiments import rp_u008_external_recovery_core as core
from experiments import rp_u008_external_source as source


class FakeHTTPResponse(BytesIO):
    def __init__(self, content: bytes, url: str):
        super().__init__(content)
        self.url = url

    def geturl(self) -> str:
        return self.url


def test_publisher_exact_url_commit_and_original_git_object_are_frozen():
    assert source.ORIGINAL_URL == (
        "https://raw.githubusercontent.com/Ezharjan/LocalNetDynamicsDataset/"
        "d57ca705bfd2b0340b6476a2d01553d2c967636e/"
        "dataset/raw/localnet_desktop-eth_20260920_123407.csv"
    )
    assert source.PROTOCOL_ONLY_COMMIT == (
        "0cfd8327a58f4e507967b074e612c581a8f24a39"
    )
    assert core.SOURCE_SIZE == 15_143_900


def test_source_rejects_wrong_byte_count_before_any_field_parse():
    with pytest.raises(core.InvalidSource, match="RAW_FILE_BYTES_CHANGED"):
        source.verify_publisher_source(b"synthetic source not original")
    with pytest.raises(core.InvalidSource, match="RAW_FILE_BYTES_CHANGED"):
        source.fetch_publisher_raw(opener=type("O", (), {"open": lambda self,request,timeout:
            FakeHTTPResponse(b"tiny", request.full_url)})())


def test_source_disallows_redirect_to_similar_or_alternate_file():
    with pytest.raises(core.InvalidSource, match="REDIRECT"):
        source.fetch_publisher_raw(opener=type("O", (), {"open": lambda self,request,timeout:
            FakeHTTPResponse(b"tiny", "https://invalid.example/not-original.csv")})())


def test_raw_original_file_never_preexisting_on_first_run():
    assert source.FIRST_RESULT.as_posix() == (
        "docs/results/RP-U008-P01-first-run/audit.json"
    )
