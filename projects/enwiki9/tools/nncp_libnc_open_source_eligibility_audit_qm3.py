#!/usr/bin/env python3
"""Produce durable tar-member and Makefile proof for LibNC eligibility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_open_source_eligibility_audit_qm3_v1"
DONOR_TAR = Path("/home/x/enwiki9-nonproof/external/nncp-2024-06-05.tar.gz")
SOURCE_TAR = (
    ROOT
    / "programs/nncp_libnc_midsegment32_cpu_xz_package_qm1_v1/nncp_cpu_source.tar.xz"
)
Q2_DECISION = (
    ROOT / "results/nncp_libnc_open_source_eligibility_audit_qm2_v1/decision.json"
)
COMMITTEE_EXCEPTION = ROOT / "docs/nncp_libnc_committee_source_exception.txt"
EXPECTED = {
    "donor_tar": "7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119",
    "source_tar": "9b015bdbe9d2d625efd080021864717d39277502158472e825bacb05e2a70082",
    "q2_decision": "14c1575db03fdef73d8975ee65b72040871e153510c9318eb503c18c6f8d4887",
}
README_MEMBER = "nncp-2024-06-05/readme.txt"
MAKEFILE_MEMBER = "Makefile"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def member_bytes(path: Path, mode: str, member: str) -> bytes:
    with tarfile.open(path, mode) as archive:
        handle = archive.extractfile(member)
        if handle is None:
            raise ValueError(f"missing archive member: {member}")
        return handle.read()


def main() -> int:
    bound = {
        "donor_tar": DONOR_TAR,
        "source_tar": SOURCE_TAR,
        "q2_decision": Q2_DECISION,
    }
    for name, path in bound.items():
        if not path.is_file() or sha256(path) != EXPECTED[name]:
            raise ValueError(f"{name} identity mismatch")

    q2 = json.loads(Q2_DECISION.read_text())
    if q2.get("status") != "ELIGIBILITY_DEBT":
        raise ValueError("q2 did not establish the expected eligibility debt")

    readme = member_bytes(DONOR_TAR, "r:gz", README_MEMBER)
    makefile = member_bytes(SOURCE_TAR, "r:xz", MAKEFILE_MEMBER)
    makefile_text = makefile.decode()
    q2_readme = q2["license_census"]["donor_readme"]
    if q2_readme["bytes"] != len(readme) or q2_readme["sha256"] != hash_bytes(readme):
        raise ValueError("q2 README member identity mismatch")

    links_bundled_libnc = "libnc$(DLLEXT)" in makefile_text
    libnc_source_build_rule_present = any(
        line.strip().startswith("libnc$(DLLEXT):")
        for line in makefile_text.splitlines()
    )
    complete_libnc_source_present = bool(
        q2["package_census"]["complete_libnc_source_present"]
    )
    committee_exception_present = COMMITTEE_EXCEPTION.is_file()
    source_eligibility_proven = (
        complete_libnc_source_present or committee_exception_present
    )
    failed: list[str] = []
    if not links_bundled_libnc:
        failed.append("makefile_does_not_link_expected_libnc_dependency")
    if not libnc_source_build_rule_present:
        failed.append("libnc_source_build_rule_absent")
    if not complete_libnc_source_present:
        failed.append("complete_osi_libnc_source_absent")
    if not committee_exception_present:
        failed.append("receipt_bound_committee_exception_absent")
    if not source_eligibility_proven:
        failed.append("prize_source_eligibility_not_proven")

    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(f"refusing to replace existing output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    decision = {
        "schema": "enwiki9_nncp_libnc_open_source_eligibility_audit_qm3_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "PASS" if source_eligibility_proven else "ELIGIBILITY_DEBT",
        "verdict": (
            "authorize_prize_facing_source_package"
            if source_eligibility_proven
            else "retain_nncp_only_as_teacher_until_open_cpu_replacement"
        ),
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Durable local archive-member and Makefile dependency proof. "
            "It does not bind contest judges or decide legal rights."
        ),
        "durable_members": {
            "donor_readme": {
                "archive_path": str(DONOR_TAR),
                "member": README_MEMBER,
                "bytes": len(readme),
                "sha256": hash_bytes(readme),
            },
            "candidate_makefile": {
                "archive_path": str(SOURCE_TAR),
                "member": MAKEFILE_MEMBER,
                "bytes": len(makefile),
                "sha256": hash_bytes(makefile),
            },
        },
        "build_dependency_proof": {
            "links_bundled_libnc_binary": links_bundled_libnc,
            "libnc_source_build_rule_present": libnc_source_build_rule_present,
            "complete_libnc_source_present": complete_libnc_source_present,
            "bundled_libnc_binary": q2["package_census"]["libnc_binary_member"],
            "committee_exception_path": str(COMMITTEE_EXCEPTION),
            "committee_exception_present": committee_exception_present,
            "source_eligibility_proven": source_eligibility_proven,
        },
        "research_effect": {
            "nncp_midpoint_remains_valid_teacher_evidence": True,
            "libnc_archives_receive_prize_facing_score_credit": False,
            "open_compact_cpu_replacement_required": True,
            "verified_full_1g_score_bytes": None,
        },
        "official_authorities": [
            "https://prize.hutter1.net/hrules.htm",
            "https://bellard.org/libnc/",
        ],
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
