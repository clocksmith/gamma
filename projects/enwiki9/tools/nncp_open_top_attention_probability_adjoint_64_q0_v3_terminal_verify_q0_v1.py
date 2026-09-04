#!/usr/bin/env python3
"""Read-only terminal verifier for the complete negative dP v3 evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tarfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_top_attention_probability_adjoint_64_q0_v3_terminal_verify_q0_v1"
SOURCE_ID = "nncp_open_top_attention_probability_adjoint_64_q0_v3"
SOURCE_JOB_ID = "20260904T151950Z_c9dcdc1798"
RESULT = ROOT / "results" / CANDIDATE_ID
SOURCE_RESULT = ROOT / "results" / SOURCE_ID
DECISION = SOURCE_RESULT / "decision.json"
GUARD_A = SOURCE_RESULT / "evaluation-a.guard.json"
GUARD_B = SOURCE_RESULT / "evaluation-b.guard.json"
TREATMENT = SOURCE_RESULT / "open-exact-probability-adjoint.bf16"
PACKAGE = SOURCE_RESULT / "incremental_source.tar.xz"
LDD = SOURCE_RESULT / "ldd.stdout"
COMPARATOR = (
    ROOT
    / "results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/source-attention-probability-adjoint.bf16"
)
SOURCE_JOB = ROOT / "operations/adaptive/failed/000_20260904T151950Z_c9dcdc1798.json"
SOURCE_REFLECTION = ROOT / "operations/adaptive/reflections/20260904T151950Z_c9dcdc1798.json"
EXPECTED = {
    DECISION: "2a99acc939078f97518149094bb0626806c93b0347a912b0fc5ba3050f121f43",
    GUARD_A: "7ff9537aaae40c0fe0875752d829b50438a4ca4ba8cb6871917f256612efb777",
    GUARD_B: "62f73f2976fdda3d384f076adcd3a291751a3b94dbe6b6dbcb40a7e15c875a5a",
    TREATMENT: "367e837fcc15db00dbca258e50bfd2edf1274f869e74bb7c95aeb09560b887ba",
    PACKAGE: "096283b3b9b9218f2b6daf1ab648aec499347295d33933cb25e5f0d942082822",
    LDD: "2c14e4614df089b4fe419d2ae771531bb8a3f91bc22e8792e8f10c840777b80e",
    COMPARATOR: "94763dc5ad7c78020c2620a06b0824fd7f2280c6a2a4c3783618931da44dbe22",
    SOURCE_JOB: "e2daf1cb648626762c7ca18f729013d590432bfbccfc3022a5c2a889cf1a0d18",
    SOURCE_REFLECTION: "7ff76fcdcb2d7acd1bbdd15aabe4a8e8f83afa5206ea9f2c7eb77bdf1772b934",
}
STATES = 64
HEADS = 8
STREAMS = 32
KEYS = 320
OUTPUT_BYTES = 10_485_760
OUTPUT_ELEMENTS = 5_242_880
FORBIDDEN = ("libnc", "ggml", "cuda", "openmp", "gomp", "blas")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def verify_adaptive_environment() -> bool:
    revision_text = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    experiment_text = os.environ.get("GAMMA_ENWIKI9_EXPERIMENT_JSON")
    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    snapshot_text = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if not all((revision_text, experiment_text, snapshot_id, snapshot_text)):
        return False
    revision = json.loads(revision_text)
    experiment = json.loads(experiment_text)
    return (
        snapshot_id == CANDIDATE_ID
        and revision.get("candidateId") == CANDIDATE_ID
        and experiment.get("path")
        == f"operations/adaptive/experiments/{CANDIDATE_ID}.json"
        and Path(snapshot_text).is_dir()
    )


def guard_pass(value: dict[str, Any]) -> bool:
    measurements = value.get("measurements")
    guards = value.get("guards")
    cgroup = value.get("cgroup")
    return (
        value.get("schema") == "gamma.enwiki9.resource-guard-receipt.v3"
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and isinstance(measurements, dict)
        and bool(measurements)
        and all(item is True for item in measurements.values())
        and isinstance(guards, dict)
        and bool(guards)
        and all(item is False for item in guards.values())
        and isinstance(cgroup, dict)
        and cgroup.get("joined_before_exec") is True
    )


def mismatch_count(left: bytes, right: bytes) -> int:
    if len(left) != len(right) or len(left) % 2:
        raise RuntimeError("BF16 population geometry mismatch")
    return sum(
        left[index : index + 2] != right[index : index + 2]
        for index in range(0, len(left), 2)
    )


def stream_major(source_order: bytes) -> bytes:
    if len(source_order) != OUTPUT_BYTES:
        raise RuntimeError("treatment byte count mismatch")
    output = bytearray(len(source_order))
    row_bytes = KEYS * 2
    for state in range(STATES):
        for head in range(HEADS):
            for stream in range(STREAMS):
                source_row = (((state * HEADS + head) * STREAMS + stream) * KEYS)
                target_row = (((state * STREAMS + stream) * HEADS + head) * KEYS)
                source_offset = source_row * 2
                target_offset = target_row * 2
                output[target_offset : target_offset + row_bytes] = source_order[
                    source_offset : source_offset + row_bytes
                ]
    return bytes(output)


def package_pass() -> tuple[bool, list[str]]:
    required = {
        "tools/nncp_open_top_attention_probability_adjoint_64_q0_v2.py",
        "tools/nncp_open_top_attention_probability_adjoint_64_q0_v3.py",
        "programs/nncp_open_top_attention_probability_adjoint_64_q0_v3/attention_probability_adjoint.cpp",
        "operations/adaptive/experiments/nncp_open_top_attention_probability_adjoint_64_q0_v3.json",
    }
    with tarfile.open(PACKAGE, "r:xz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
    safe = all(
        name and not Path(name).is_absolute() and ".." not in Path(name).parts
        for name in names
    )
    return safe and required.issubset(names) and PACKAGE.stat().st_size <= 500_000, names


def main() -> int:
    if RESULT.exists():
        if not RESULT.is_dir() or any(RESULT.iterdir()):
            raise RuntimeError(f"refusing to overwrite nonempty {RESULT}")
    else:
        RESULT.mkdir(parents=True)

    decision = load_json(DECISION)
    job = load_json(SOURCE_JOB)
    source_reflection = load_json(SOURCE_REFLECTION)
    guards = [load_json(GUARD_A), load_json(GUARD_B)]
    evidence_hashes_pass = all(
        path.is_file() and sha256(path) == expected for path, expected in EXPECTED.items()
    )

    treatment = TREATMENT.read_bytes()
    comparator = COMPARATOR.read_bytes()
    permutation_a = stream_major(treatment)
    permutation_b = stream_major(treatment)
    treatment_mismatches = mismatch_count(treatment, comparator)
    permutation_mismatches = mismatch_count(permutation_a, comparator)
    permutation_sha256 = hashlib.sha256(permutation_a).hexdigest()

    execution = decision.get("execution", {})
    comparisons = execution.get("comparisons", {})
    evaluations = execution.get("evaluations", [])
    output_rows = [row.get("outputs", {}) for row in evaluations if isinstance(row, dict)]
    treatment_hashes = [
        outputs.get(arm, {}).get("sha256")
        for outputs in output_rows
        for arm in ("scalar", "avx")
    ]
    wrong_layout_hashes = [outputs.get("wrong_layout", {}).get("sha256") for outputs in output_rows]
    negated_hashes = [outputs.get("negated", {}).get("sha256") for outputs in output_rows]
    package_ok, package_members = package_pass()
    build_argv = decision.get("build", {}).get("argv", [])
    work_root = Path(build_argv[-1]).parent if isinstance(build_argv, list) and build_argv else Path("/")
    gates = decision.get("gates", {})

    checks = {
        "adaptive_environment_bound": verify_adaptive_environment(),
        "fixed_evidence_hashes": evidence_hashes_pass,
        "source_job_identity": (
            job.get("candidate_id") == SOURCE_ID
            and job.get("job_id") == SOURCE_JOB_ID
            and job.get("state") == "failed"
            and job.get("returncode") == 1
        ),
        "source_reflection_identity": (
            source_reflection.get("candidateId") == SOURCE_ID
            and source_reflection.get("job", {}).get("path")
            == SOURCE_JOB.relative_to(ROOT).as_posix()
        ),
        "terminal_decision_identity": (
            decision.get("candidate_id") == SOURCE_ID
            and decision.get("operational_status") == "terminal"
            and decision.get("arithmetic_edge_pass") is False
            and decision.get("promotion_authorized") is False
        ),
        "complete_population": all(
            comparisons.get(name, {}).get("elements") == OUTPUT_ELEMENTS
            for name in (
                "scalar_source",
                "avx_source",
                "scalar_avx",
                "wrong_layout_source",
                "negated_source",
            )
        ),
        "independent_treatment_mismatch_count": treatment_mismatches == 5_197_470,
        "recorded_treatment_mismatch_count": (
            comparisons.get("scalar_source", {}).get("mismatch_count") == treatment_mismatches
            and comparisons.get("avx_source", {}).get("mismatch_count") == treatment_mismatches
        ),
        "scalar_avx_and_replay_hash_identity": (
            len(treatment_hashes) == 4
            and set(treatment_hashes) == {EXPECTED[TREATMENT]}
            and execution.get("replay_identity") is True
            and comparisons.get("scalar_avx", {}).get("mismatch_count") == 0
        ),
        "layout_permutation_repeat": permutation_a == permutation_b,
        "layout_permutation_source_identity": (
            permutation_mismatches == 0
            and permutation_sha256 == EXPECTED[COMPARATOR]
            and len(wrong_layout_hashes) == 2
            and set(wrong_layout_hashes) == {EXPECTED[COMPARATOR]}
        ),
        "negated_control_live_and_repeated": (
            len(negated_hashes) == 2
            and len(set(negated_hashes)) == 1
            and negated_hashes[0] != EXPECTED[COMPARATOR]
            and comparisons.get("negated_source", {}).get("mismatch_count", 0) > 0
        ),
        "resource_receipts_pass": all(guard_pass(guard) for guard in guards),
        "dependency_closure_pass": (
            execution.get("forbidden_dynamic_dependencies") == []
            and not any(token in LDD.read_text(errors="replace").lower() for token in FORBIDDEN)
        ),
        "source_package_pass": package_ok,
        "work_cleanup_pass": not work_root.exists(),
        "registered_gate_pattern": gates
        == {
            "avx_source_exact": False,
            "complete_population": True,
            "dependency_closure_pass": True,
            "external_resource_receipts_pass": True,
            "negated_control_live": True,
            "repeat_byte_identity": True,
            "scalar_avx_exact": True,
            "scalar_source_exact": False,
            "source_package_pass": True,
            "work_cleanup_pass": True,
            "wrong_layout_control_live": False,
        },
    }
    verified = all(checks.values())
    receipt = {
        "schema": "gamma.enwiki9.nncp-probability-adjoint-negative-terminal-verification.v1",
        "candidate_id": CANDIDATE_ID,
        "source_candidate_id": SOURCE_ID,
        "source_job_id": SOURCE_JOB_ID,
        "verified": verified,
        "scientific_execution_valid": verified,
        "hypothesis_refuted": verified,
        "layout_bridge_verified": verified,
        "source_layout": "state,stream,head,key",
        "treatment_layout": "state,head,stream,key",
        "objective_credit_bytes": 0,
        "compression_credit_bytes": 0,
        "checks": checks,
        "computed": {
            "elements": OUTPUT_ELEMENTS,
            "treatment_source_mismatch_count": treatment_mismatches,
            "permutation_source_mismatch_count": permutation_mismatches,
            "treatment_sha256": hashlib.sha256(treatment).hexdigest(),
            "permutation_sha256": permutation_sha256,
            "source_sha256": hashlib.sha256(comparator).hexdigest(),
            "package_member_count": len(package_members),
        },
        "artifacts": [artifact(path) for path in EXPECTED],
        "terminal_decision": (
            "retire-v3-preserve-layout-bridge" if verified else "invalidate-terminal-interpretation"
        ),
    }
    temporary = RESULT / ".verification.json.tmp"
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, RESULT / "verification.json")
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
