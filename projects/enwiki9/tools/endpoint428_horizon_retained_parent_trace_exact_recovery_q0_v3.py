#!/usr/bin/env python3
"""Run exact HORIZON analysis only after reflected orphan-trace recovery."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3"
ADOPTION_ID = "endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1"
BASE_RUNNER = (
    PROJECT
    / "tools/endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3.py"
)
RESULT = PROJECT / "results" / CANDIDATE_ID
PLAN = PROJECT / "operations/planning" / f"{CANDIDATE_ID}.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
ADOPTION_RESULT = PROJECT / "results" / ADOPTION_ID / "result.json"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location(
        "gamma_horizon_recovered_exact_base", BASE_RUNNER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load source-bound recovered-exact base")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base()
BASE.CANDIDATE_ID = CANDIDATE_ID
BASE.RESULT = RESULT
BASE.PLAN = PLAN
BASE.EXPERIMENT = EXPERIMENT
BASE.TREE_LIMIT_KIB = 9_500_000
BASE.TRACE_MAGIC = b"CMX21P1\x00"
BASE.V2.CANDIDATE_ID = CANDIDATE_ID
BASE.V2.RESULT = RESULT

_base_bind_candidate_snapshot = BASE.bind_candidate_snapshot
_base_require_recovery_terminal = BASE.require_recovery_terminal
_base_referenced_artifact = BASE.referenced_artifact
_base_write_json_exclusive = BASE.write_json_exclusive
_reflection_artifact: dict[str, Any] | None = None


def bind_candidate_snapshot() -> tuple[Path, dict[str, Any]]:
    root, snapshot = _base_bind_candidate_snapshot()
    BASE.EXACT_ROOT = root
    BASE.EXACT_ANALYZER = root / "horizon-retained-analyze-exact.cpp"
    BASE.EXACT_FIXTURE = root / "horizon-exact-fixture.cpp"
    BASE.EXACT_REFERENCE = root / "horizon-exact-reference.py"
    BASE.EXACT_HEADER = root / "horizon-exact-arithmetic.h"
    BASE.EXACT_SCHEMA = root / "analysis.schema.json"
    BASE.FIXTURE_SCHEMA = root / "fixture-verification.schema.json"
    return root, snapshot


BASE.bind_candidate_snapshot = bind_candidate_snapshot


def verify_source_binding(snapshot_root: Path) -> dict[str, Any]:
    binding_path = snapshot_root / "source-binding.json"
    binding = BASE.load_json(binding_path)
    if binding.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("source-binding candidate mismatch")
    own = f"programs/{CANDIDATE_ID}/"
    source = "programs/endpoint428_horizon_retained_parent_trace_q0_v1/"
    expected: dict[str, Path] = {
        f"operations/planning/{CANDIDATE_ID}.json": PLAN,
        f"operations/adaptive/experiments/{CANDIDATE_ID}.json": EXPERIMENT,
        "operations/planning/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json": PROJECT / "operations/planning/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json",
        "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json": PROJECT / "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json",
        "operations/planning/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": PROJECT / "operations/planning/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json",
        "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": PROJECT / "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json",
        "operations/planning/evidence_conditioned_mutation_router_v7.json": PROJECT / "operations/planning/evidence_conditioned_mutation_router_v7.json",
        source + "horizon-retained-analyze.cpp": PROJECT / source / "horizon-retained-analyze.cpp",
        own + "horizon-retained-analyze-exact.cpp": snapshot_root / "horizon-retained-analyze-exact.cpp",
        own + "horizon-exact-fixture.cpp": snapshot_root / "horizon-exact-fixture.cpp",
        own + "horizon-exact-reference.py": snapshot_root / "horizon-exact-reference.py",
        own + "horizon-exact-arithmetic.h": snapshot_root / "horizon-exact-arithmetic.h",
        own + "analysis.schema.json": snapshot_root / "analysis.schema.json",
        own + "fixture-verification.schema.json": snapshot_root / "fixture-verification.schema.json",
        own + "decision.schema.json": snapshot_root / "decision.schema.json",
        own + "interface-contract.json": snapshot_root / "interface-contract.json",
        "tools/endpoint428_horizon_retained_parent_trace_exact_q0_v2.py": PROJECT / "tools/endpoint428_horizon_retained_parent_trace_exact_q0_v2.py",
        "tools/endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3.py": BASE_RUNNER,
        f"tools/{Path(__file__).name}": Path(__file__).resolve(),
    }
    records = binding.get("artifacts")
    if not isinstance(records, list):
        raise RuntimeError("source-binding artifacts are missing")
    seen: set[str] = set()
    for row in records:
        relative = str(row.get("path", ""))
        if relative not in expected or relative in seen:
            raise RuntimeError(f"unexpected source-binding path: {relative}")
        path = expected[relative]
        info = BASE.assert_regular(path)
        digest = BASE.sha256(path)
        if info.st_size != row.get("bytes") or digest != row.get("sha256"):
            raise RuntimeError(f"source-binding mismatch: {relative}")
        seen.add(relative)
    if seen != set(expected):
        raise RuntimeError("source-binding file-set closure mismatch")
    return BASE.artifact(binding_path)


BASE.verify_source_binding = verify_source_binding


def referenced_artifact_with_size(
    result: dict[str, Any], identifier: str
) -> dict[str, Any]:
    """Normalize adoption references whose frozen schema omits a byte field."""
    record = dict(_base_referenced_artifact(result, identifier))
    path = Path(str(record.get("path", "")))
    if path.is_absolute():
        raise RuntimeError("adoption artifact reference must be project-relative")
    resolved = (PROJECT / path).resolve(strict=True)
    try:
        resolved.relative_to(PROJECT)
    except ValueError as error:
        raise RuntimeError("adoption artifact reference escapes project") from error
    info = BASE.assert_regular(resolved, one_link=True)
    expected_hash = str(record.get("sha256", "")).removeprefix("sha256:")
    if BASE.sha256(resolved) != expected_hash:
        raise RuntimeError("adoption artifact reference hash mismatch")
    record["bytes"] = info.st_size
    return record


BASE.referenced_artifact = referenced_artifact_with_size


def valid_reflection() -> dict[str, Any]:
    result_hash = BASE.sha256(ADOPTION_RESULT)
    expected_path = ADOPTION_RESULT.relative_to(PROJECT).as_posix()
    matches: list[tuple[Path, dict[str, Any]]] = []
    reflection_root = PROJECT / "operations/adaptive/reflections"
    for path in sorted(reflection_root.glob("*.json")):
        try:
            value = BASE.load_json(path)
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            continue
        validity = value.get("validity", {})
        if (
            value.get("candidateId") != ADOPTION_ID
            or validity.get("valid") is not True
            or validity.get("classification") != "valid"
        ):
            continue
        if not any(
            isinstance(row, dict)
            and row.get("path") == expected_path
            and row.get("sha256") == f"sha256:{result_hash}"
            for row in value.get("evidence", [])
        ):
            continue
        decision = value.get("decision", {})
        if (
            decision.get("promotionPredicatesPass") is not True
            or decision.get("killPredicatesPass") is not False
            or decision.get("verdict") not in {"promote", "next-gate"}
        ):
            continue
        matches.append((path, value))
    if len(matches) != 1:
        raise RuntimeError(
            "exactly one valid reflection must bind the adoption result"
        )
    return BASE.artifact(matches[0][0])


def require_reflected_recovery() -> dict[str, Any]:
    global _reflection_artifact
    if BASE.active_adoption_jobs():
        raise RuntimeError("orphan adoption remains nonterminal")
    if not ADOPTION_RESULT.is_file() or ADOPTION_RESULT.is_symlink():
        raise RuntimeError("orphan-adoption terminal result is absent")
    snapshot_root, _ = bind_candidate_snapshot()
    verify_source_binding(snapshot_root)
    _reflection_artifact = valid_reflection()
    return _base_require_recovery_terminal()


BASE.require_recovery_terminal = require_reflected_recovery


def write_json_with_reflection(path: Path, value: dict[str, Any]) -> None:
    if path == RESULT / "decision.json":
        if _reflection_artifact is None:
            raise RuntimeError("adoption reflection was not retained")
        value.setdefault("inputs", {})["adoption_reflection"] = _reflection_artifact
        foundational = (
            "recoveryIntegrityPass",
            "immutableIdentityPass",
            "deterministicBuildPass",
            "completeActivePopulationPass",
            "completeParentTracePass",
            "legacyABPass",
            "exactABPass",
            "legacyCrosscheckPass",
            "arbitraryPrecisionFixturePass",
            "analysisResourcePass",
        )
        gates = value.get("gates", {})
        if any(gates.get(name) is not True for name in foundational):
            value["verdict"] = "invalidate_endpoint428_horizon_exact_recovery_attempt"
            value["promotion_authorized"] = False
    _base_write_json_exclusive(path, value)


BASE.write_json_exclusive = write_json_with_reflection


def main() -> int:
    return BASE.main()


if __name__ == "__main__":
    raise SystemExit(main())
