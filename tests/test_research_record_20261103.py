"""Dated research-record integrity checks.

These tests validate documentation provenance and repository navigation.
They do not rerun experiments, validate external papers, or prove physics.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATED = (
    ROOT / "docs/research/RESEARCH-RECORD-2026-11-03.md",
    ROOT / "docs/literature/REVIEW-2026-11-03.md",
)
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_dated_research_docs_have_no_broken_relative_links():
    for source in DATED:
        assert source.is_file(), f"Missing dated research source: {source}"
        contents = source.read_text(encoding="utf-8")
        assert contents.strip()
        for reference in LINK.findall(contents):
            if reference.startswith(("https://", "http://", "#", "mailto:")):
                continue
            path = (source.parent / reference.split("#", 1)[0]).resolve()
            assert path.is_relative_to(ROOT.resolve()), f"Escaping repository: {reference}"
            assert path.is_file(), f"Broken relative link in {source}: {reference}"


def test_research_record_preserves_original_negative_f1_tie_and_limits():
    diary = DATED[0].read_text(encoding="utf-8")
    assert "| GREEDY1 | 15,888 | 7,852 |" in diary
    assert "| LOOKAHEAD2 | 15,888 | 7,968 |" in diary
    assert "not a blind" in diary.lower()
    assert "No experimentally calibrated persistence observable" in diary
    assert "No physical derivation of spacetime" in diary


def test_literature_review_identifies_prior_scholarship_and_corrections():
    reading = DATED[1].read_text(encoding="utf-8")
    for expected in (
        "Karl Menger (1927)",
        "C. S. Holling (1 November 1973)",
        "Reza Olfati-Saber, J. Alex Fax and Richard M. Murray (January 2007)",
        "Igor Averbakh and Jordi Pereira (21 September 2018 online)",
        "erratum on 4 May 2016",
        "author correction on 28 March 2019",
        "not an exhaustive priority search",
    ):
        assert expected in reading
