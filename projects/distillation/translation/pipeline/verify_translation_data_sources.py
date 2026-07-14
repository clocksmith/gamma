#!/usr/bin/env python3
"""Verify exact public source candidates without admitting them to the campaign."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import tarfile
from typing import Any
from urllib.request import Request, urlopen


MASSIVE_REVISION = "ff6bd8e4b27c3543e4f8fe2108f32bb95a6f8740"
MASSIVE_URL = "https://amazon-massive-nlu-dataset.s3.amazonaws.com/amazon-massive-dataset-1.0.tar.gz"
MASSIVE_ARCHIVE_SHA256 = "7df623fd2d300a4d235d6ee5bd396c9a28258d3a0ccb29abdb054506eba153f8"
MASSIVE_FILES = {
    "1.0/data/en-US.jsonl": "c70f75c6a543a26e249ec383df67733ad9b1066f6c0406c2e04a3f03356e407e",
    "1.0/data/es-ES.jsonl": "310462a79fa181ff83c643a8d356c7b8155fd37a25e80a77ba3ca9b29305c4a5",
    "1.0/LICENSE": "c2e6ea015269147de02117ebdd91f30ef09831251f5345fa8365273b1db1d435",
}

TICO_REVISION = "55d70dc0b1d1d0b2151c5e22815d823fedac3f2f"
TICO_ROOT = f"https://huggingface.co/datasets/gmnlp/tico19/resolve/{TICO_REVISION}"
TICO_FILES = {
    "README.md": "3c1979db6944369f9444ac7e9b75b2ea0aa63b9d3ea0a5f6f88430492eadb097",
    "dev/dev.en-es-LA.tsv": "1ebedadbe8de42a126e80b8e18947f43ff9910df4699b9d8bcc0412675ae1d2f",
    "test/test.en-es-LA.tsv": "a0f5488d595627d01e680fd8559f7e69c794445487f4c3e5d71fe4c2751dd220",
}

FLORES_REVISION = "b3a5298db5721c8a682e7ef00a37fcc9ab522757"
FLORES_API = f"https://huggingface.co/api/datasets/openlanguagedata/flores_plus/revision/{FLORES_REVISION}"
FLORES_FILES = {
    "dev/eng_Latn.jsonl",
    "dev/spa_Latn.jsonl",
    "devtest/eng_Latn.jsonl",
    "devtest/spa_Latn.jsonl",
}


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "clocksmith-gamma-source-verifier/1"})
    with urlopen(request) as response:  # noqa: S310 - every URL is an immutable constant above
        return response.read()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_receipt_core(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_massive() -> dict[str, Any]:
    archive = _get(MASSIVE_URL)
    archive_sha256 = _sha256(archive)
    files: list[dict[str, Any]] = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        for path, expected_sha256 in MASSIVE_FILES.items():
            member = bundle.extractfile(path)
            if member is None:
                raise RuntimeError(f"MASSIVE archive is missing {path}")
            observed_sha256 = _sha256(member.read())
            files.append(
                {
                    "path": path,
                    "expectedSha256": expected_sha256,
                    "observedSha256": observed_sha256,
                    "matched": observed_sha256 == expected_sha256,
                }
            )
    matched = archive_sha256 == MASSIVE_ARCHIVE_SHA256 and all(entry["matched"] for entry in files)
    return {
        "sourceId": "massive-1.0-en-us-es-es-candidate",
        "sourceRevision": MASSIVE_REVISION,
        "sourceArtifact": MASSIVE_URL,
        "licenseId": "CC-BY-4.0",
        "expectedArtifactSha256": MASSIVE_ARCHIVE_SHA256,
        "observedArtifactSha256": archive_sha256,
        "boundFiles": files,
        "sourceIdentityMatched": matched,
        "campaignEligible": False,
        "eligibilityBlockers": [
            "human_license_approval_absent",
            "population_role_not_assigned",
            "cross_locale_alignment_and_localization_policy_not_audited",
            "attribution_manifest_absent",
        ],
    }


def verify_tico() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path, expected_sha256 in TICO_FILES.items():
        value = _get(f"{TICO_ROOT}/{path}")
        observed_sha256 = _sha256(value)
        entry: dict[str, Any] = {
            "path": path,
            "expectedSha256": expected_sha256,
            "observedSha256": observed_sha256,
            "matched": observed_sha256 == expected_sha256,
        }
        if path.endswith(".tsv"):
            entry["rowsIncludingHeader"] = len(value.splitlines())
        files.append(entry)
    return {
        "sourceId": "tico19-en-es-la-candidate",
        "sourceRevision": TICO_REVISION,
        "sourceRepository": "https://huggingface.co/datasets/gmnlp/tico19",
        "licenseId": "CC0-1.0",
        "boundFiles": files,
        "sourceIdentityMatched": all(entry["matched"] for entry in files),
        "campaignEligible": False,
        "eligibilityBlockers": [
            "human_license_approval_absent",
            "population_role_not_assigned",
            "row_level_source_url_and_license_audit_absent",
            "reverse_direction_reference_quality_review_absent",
        ],
    }


def verify_flores() -> dict[str, Any]:
    metadata = json.loads(_get(FLORES_API))
    siblings = {
        str(entry.get("rfilename", ""))
        for entry in metadata.get("siblings", [])
        if isinstance(entry, dict)
    }
    licenses = metadata.get("cardData", {}).get("license", [])
    revision_matched = metadata.get("sha") == FLORES_REVISION
    files_present = FLORES_FILES.issubset(siblings)
    license_matched = licenses == ["cc-by-sa-4.0"]
    gated = metadata.get("gated") == "auto"
    return {
        "sourceId": "flores-plus-en-es-candidate",
        "sourceRevision": FLORES_REVISION,
        "sourceRepository": "https://huggingface.co/datasets/openlanguagedata/flores_plus",
        "licenseId": "CC-BY-SA-4.0",
        "observedRevision": metadata.get("sha"),
        "observedGating": metadata.get("gated"),
        "requiredFiles": sorted(FLORES_FILES),
        "requiredFilesPresent": files_present,
        "sourceIdentityMatched": revision_matched and files_present and license_matched and gated,
        "bytesVerified": False,
        "campaignEligible": False,
        "eligibilityBlockers": [
            "gated_terms_not_accepted_by_population_custodian",
            "bound_file_hashes_absent",
            "human_license_approval_absent",
            "population_role_not_assigned",
            "contamination_screen_absent",
        ],
    }


def build_receipt(observed_on: str) -> dict[str, Any]:
    sources = [verify_massive(), verify_tico(), verify_flores()]
    identity_passed = all(source["sourceIdentityMatched"] for source in sources)
    eligibility_correctly_denied = all(source["campaignEligible"] is False for source in sources)
    core = {
        "schemaVersion": 1,
        "verificationId": "gamma.translation.enes.public-source-candidates.2026-07-14",
        "observedOn": observed_on,
        "status": "pass_source_identity_only" if identity_passed and eligibility_correctly_denied else "failed",
        "claimBoundary": "This receipt verifies the pinned public source identities and expected license labels only. It is not legal approval, population admission, contamination clearance, or promotion evidence.",
        "sources": sources,
        "campaignEligibilityGranted": False,
    }
    return {**core, "receiptHash": _hash_receipt_core(core)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed-on", default=date.today().isoformat())
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    receipt = build_receipt(args.observed_on)
    output = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if receipt["status"] == "pass_source_identity_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
