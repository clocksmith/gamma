#!/usr/bin/env python3
"""Audit whether the compact NNCP/LibNC package proves source eligibility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_open_source_eligibility_audit_qm2_v1"
DONOR_TAR = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05.tar.gz")
Q1_PROGRAM = ROOT / "programs/nncp_libnc_midsegment32_cpu_xz_package_qm1_v1"
Q1_SOURCE_TAR = Q1_PROGRAM / "nncp_cpu_source.tar.xz"
Q1_DECISION = (
    ROOT
    / "results/nncp_libnc_midsegment32_cpu_xz_package_qm1_v1/decision.json"
)
COMMITTEE_EXCEPTION = ROOT / "docs/nncp_libnc_committee_source_exception.txt"
EXPECTED = {
    "donor_tar": "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119",
    "q1_source_tar": "9b015bdbe9d2d625efd080021864717d39277502158472e825bacb05e2a70082",
    "q1_decision": "74f5016d6b858826cc35624213c605da6c6e801f78bbcee7dc83fa64485d9f90",
}
NNCP_LICENSE_SENTENCE = "The source code is released under the MIT licence."
LIBNC_BINARY_SENTENCE = (
    "The LibNC library is provided in binary form and can be freely redistributed."
)
OFFICIAL_RULES_URL = "https://prize.hutter1.net/hrules.htm"
LIBNC_URL = "https://bellard.org/libnc/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def archive_members(path: Path, mode: str) -> list[dict[str, object]]:
    with tarfile.open(path, mode) as archive:
        return [
            {"name": member.name, "bytes": member.size, "type": member.type.decode()}
            for member in archive.getmembers()
            if member.isfile()
        ]


def main() -> int:
    bound = {
        "donor_tar": DONOR_TAR,
        "q1_source_tar": Q1_SOURCE_TAR,
        "q1_decision": Q1_DECISION,
    }
    for name, path in bound.items():
        if not path.is_file() or sha256(path) != EXPECTED[name]:
            raise ValueError(f"{name} identity mismatch")

    q1_decision = json.loads(Q1_DECISION.read_text())
    if q1_decision.get("status") != "PASS":
        raise ValueError("q1 package certificate is not a pass")

    q1_members = archive_members(Q1_SOURCE_TAR, "r:xz")
    q1_names = {str(member["name"]) for member in q1_members}
    library_member = next(
        (member for member in q1_members if member["name"] == "libnc.so"), None
    )
    libnc_source_suffixes = (".c", ".cc", ".cpp", ".S", ".s")
    libnc_source_members = sorted(
        name
        for name in q1_names
        if "libnc" in name.lower() and name.endswith(libnc_source_suffixes)
    )

    with tempfile.TemporaryDirectory(prefix="nncp-libnc-license-audit-") as temp:
        with tarfile.open(DONOR_TAR, "r:gz") as archive:
            archive.extract("nncp-2024-06-05/readme.txt", temp)
        readme = Path(temp) / "nncp-2024-06-05/readme.txt"
        readme_text = readme.read_text()
        readme_identity = artifact(readme)

    nncp_mit_claim_present = NNCP_LICENSE_SENTENCE in readme_text
    libnc_binary_redistribution_claim_present = LIBNC_BINARY_SENTENCE in readme_text
    complete_libnc_source_present = bool(libnc_source_members)
    committee_exception_present = COMMITTEE_EXCEPTION.is_file()
    source_eligibility_proven = (
        complete_libnc_source_present or committee_exception_present
    )

    failed: list[str] = []
    if library_member is None:
        failed.append("required_libnc_binary_missing")
    if not nncp_mit_claim_present:
        failed.append("nncp_mit_license_claim_missing")
    if not libnc_binary_redistribution_claim_present:
        failed.append("libnc_binary_redistribution_claim_missing")
    if not complete_libnc_source_present:
        failed.append("complete_osi_libnc_source_not_present")
    if not committee_exception_present:
        failed.append("receipt_bound_committee_exception_not_present")
    if not source_eligibility_proven:
        failed.append("prize_source_eligibility_not_proven")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    decision = {
        "schema": "enwiki9_nncp_libnc_open_source_eligibility_audit_qm2_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if source_eligibility_proven else "ELIGIBILITY_DEBT",
        "verdict": (
            "authorize_prize_facing_source_package"
            if source_eligibility_proven
            else "teacher_only_until_open_libnc_replacement_or_written_exception"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Receipt-bound package and license census. It does not decide legal "
            "rights or bind contest judges; absent complete LibNC source or a "
            "written exception, it refuses prize-facing eligibility credit."
        ),
        "official_contract": {
            "rules_url": OFFICIAL_RULES_URL,
            "libnc_url": LIBNC_URL,
            "required_proof": (
                "Buildable OSI-licensed source for compressor, decompressor, "
                "and required runtime components, or an exact written contest exception."
            ),
        },
        "package_census": {
            "q1_package_bytes": q1_decision["package"]["bytes"],
            "source_tar_members": q1_members,
            "libnc_binary_member": library_member,
            "libnc_source_members": libnc_source_members,
            "complete_libnc_source_present": complete_libnc_source_present,
            "q1_program_top_level_files": sorted(
                path.name for path in Q1_PROGRAM.iterdir() if path.is_file()
            ),
        },
        "license_census": {
            "donor_readme": readme_identity,
            "nncp_mit_claim_present": nncp_mit_claim_present,
            "libnc_binary_redistribution_claim_present": (
                libnc_binary_redistribution_claim_present
            ),
            "committee_exception_path": str(COMMITTEE_EXCEPTION),
            "committee_exception_present": committee_exception_present,
            "source_eligibility_proven": source_eligibility_proven,
        },
        "required_resolution": [
            "Replace LibNC with complete buildable OSI-licensed CPU source while preserving exact codec behavior.",
            "Alternatively preserve a receipt-bound written contest exception for this exact bundled LibNC binary.",
        ],
        "research_effect": {
            "existing_compression_receipts_remain_valid_as_teacher_evidence": True,
            "existing_package_size_measurement_remains_valid": True,
            "prize_facing_score_or_forecast_authorized": False,
            "verified_full_1g_score_bytes": None,
        },
        "inputs": {
            **{name: artifact(path) for name, path in bound.items()},
            "driver": artifact(Path(__file__).resolve()),
        },
        "failed_conditions": failed,
    }
    (output_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
