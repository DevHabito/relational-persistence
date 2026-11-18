"""D01 synthetic token-only inspection, no original compressor data or pressure."""
from __future__ import annotations

from io import BytesIO
import zipfile

import pytest

from experiments import rp_u009_lps_token_diagnostic as d
from experiments import rp_u009_metropt_core as c


def test_original_invalid_p01_sha_cannot_be_overwritten():
    assert d.KNOWN_P01_ZIP_SIZE==218_381_995
    assert d.KNOWN_P01_ZIP_SHA==(
        "aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a"
    )
    assert d.D01_ADDENDUM_COMMIT=="26cf6dff3e15805124f58c61529ff54924be6b24"


def test_synthetic_window_has_distinct_binary_text_from_diagnostic():
    assert d.ALLOWED_TOKENS==frozenset({"0","1","0.0","1.0"})
    assert "2" not in d.ALLOWED_TOKENS


def test_token_diagnostic_does_not_import_or_compute_pressure_observations():
    assert d.D01_OUTPUT.as_posix().endswith(
        "RP-U009-P01-D01-post-source-token-diagnostic/audit.json"
    )
    assert d.run_diagnostic.__name__=="run_diagnostic"
    assert len(c.fixed_windows())==4


def test_source_fault_remains_in_original_archive():
    d.verify_original_failure()
