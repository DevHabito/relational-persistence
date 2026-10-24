"""Read-only source-licensing and immutable-file provenance audit.

Fetches only Zenodo metadata (not traffic measurements). It cannot
supersede the upstream Caltrans/DCRNN rights review.
"""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

ZENODO_METADATA_URL = "https://zenodo.org/api/records/5146275"
EXPECTED_FILENAME = "METR-LA.csv"
EXPECTED_MD5 = "d3adaa79856bf610f25558fc242c7190"


def audit(record: dict) -> dict:
    metadata = record.get("metadata", {})
    old_license = metadata.get("license", {})
    rights = metadata.get("rights", [])
    ids = []
    if isinstance(old_license, dict):
        ids.append(old_license.get("id"))
    elif isinstance(old_license, str):
        ids.append(old_license)
    if isinstance(rights, dict):
        rights = [rights]
    if isinstance(rights, list):
        for right in rights:
            if not isinstance(right, dict):
                continue
            rid = right.get("id")
            if rid:
                ids.append(rid)
            for item in right.get("licenses", []):
                if isinstance(item, dict):
                    ids.append(item.get("id") or item.get("title"))
    licenses = sorted({value for value in ids if isinstance(value, str) and value.strip()})
    files = []
    for entry in record.get("files", []):
        if entry.get("key") != EXPECTED_FILENAME and entry.get("filename") != EXPECTED_FILENAME:
            continue
        files.append({
            "name": EXPECTED_FILENAME,
            "checksum": entry.get("checksum"),
            "size_bytes": entry.get("size"),
        })
    checksum = files[0]["checksum"] if len(files) == 1 else None
    license_identified = bool(licenses)
    matching_file = bool(checksum and (
        checksum == "md5:" + EXPECTED_MD5 or checksum == EXPECTED_MD5
    ))
    return {
        "source": ZENODO_METADATA_URL,
        "doi": metadata.get("doi") or record.get("doi"),
        "record_id": record.get("id"),
        "license_identifiers": licenses,
        "access_right": metadata.get("access_right") or metadata.get("access", {}).get("status"),
        "files": files,
        "pinned_checksum_matches": matching_file,
        "record_license_identified": license_identified,
        "upstream_pems_rights_independently_verified": False,
        "ready_for_empirical_score_without_more_checks": False,
        "status": "metadata_only_not_a_measurement",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    req = Request(
        ZENODO_METADATA_URL,
        headers={"Accept": "application/json", "User-Agent": "RP-E002-research-provenance/0.1"},
    )
    with urlopen(req, timeout=45) as response:
        record = json.load(response)
    report = audit(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
