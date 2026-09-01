#!/usr/bin/env python3
"""Close the terminal HORIZON-v1 output namespace without rerunning science.

This dormant, zero-credit tool accepts only the prospectively routed
``CORRECTION_RETRY_ONLY`` outcome caused by HORIZON-v1's undeclared result
artifacts.  It replays the sealed terminal router, binds every immutable v1
result file, and copies the v1 decision bytes unchanged into a clean successor
namespace.  It never invokes CMIX, the manifest producer, or the analyzer.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
from types import ModuleType
from typing import Any

import jsonschema


PROJECT = Path(__file__).absolute().parents[1]
SOURCE_CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_q0_v1"
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_output_closure_q0_v2"
SOURCE_RESULT_ROOT = f"results/{SOURCE_CANDIDATE_ID}"
RESULT_ROOT = f"results/{CANDIDATE_ID}"
SOURCE_DECISION_PATH = f"{SOURCE_RESULT_ROOT}/decision.json"
PRESERVED_DECISION_NAME = "decision.v1.json"
RECEIPT_NAME = "receipt.json"

ROUTER_PATH = "tools/endpoint428_horizon_terminal_route_v1.py"
ROUTER_SHA256 = "e93e6fd61b80c22caac0cb331ad63b780e674d9017433e0f2d089571d237e223"
ROUTER_SCHEMA_PATH = (
    "contracts/research/v1/endpoint428-horizon-terminal-route.schema.json"
)
ROUTER_SCHEMA_SHA256 = (
    "c032cda7b92b4014a441e357c6511f3af885616ed677c8f99570084a63743c60"
)
RECEIPT_SCHEMA_PATH = (
    "contracts/research/v1/"
    "endpoint428-horizon-output-closure-receipt-v1.schema.json"
)
TOOL_PATH = f"tools/{CANDIDATE_ID}.py"

DECLARED_V1_NAMES = frozenset(
    {
        "analysis-a.json",
        "analysis-b.json",
        "decision.json",
        "manifest-a.bin",
        "manifest-b.bin",
        "parent.archive",
        "parent.p1",
    }
)
UNDECLARED_V1_NAMES = frozenset(
    {
        "analysis-a-guard.json",
        "analysis-a.log",
        "analysis-b-guard.json",
        "analysis-b.log",
        "build.json",
        "compile-analyzer.log",
        "compile-manifest.log",
        "manifest-a-guard.json",
        "manifest-a.log",
        "manifest-b-guard.json",
        "manifest-b.log",
        "materialize.log",
        "parent-trace-guard.json",
        "parent-trace.log",
        "scan-a.json",
        "scan-b.json",
    }
)
SOURCE_NAMES = DECLARED_V1_NAMES | UNDECLARED_V1_NAMES
OUTPUT_NAMES = frozenset({PRESERVED_DECISION_NAME, RECEIPT_NAME})
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
JSON_LIMIT = 64 * 1024 * 1024


class ClosureError(RuntimeError):
    """The terminal activation or immutable closure is not exact."""


def _digest_text(value: str) -> str:
    if not SHA256_RE.fullmatch(value):
        raise ClosureError("expected SHA-256 must be 64 lowercase hexadecimal digits")
    return value.removeprefix("sha256:")


def _canonical_json(value: Any) -> bytes:
    try:
        return (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ClosureError("receipt is not finite canonical JSON") from error


def _load_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"nonfinite JSON constant: {value}")

    try:
        value = json.loads(raw, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ClosureError(f"{label} is not finite JSON") from error
    if not isinstance(value, dict):
        raise ClosureError(f"{label} root must be an object")
    return value


def _relative(project_root: Path, path: Path) -> str:
    try:
        return path.absolute().relative_to(project_root.absolute()).as_posix()
    except ValueError as error:
        raise ClosureError(f"path escapes project root: {path}") from error


def _load_router(project_root: Path) -> ModuleType:
    router_path = project_root / ROUTER_PATH
    schema_path = project_root / ROUTER_SCHEMA_PATH
    for path, expected, label in (
        (router_path, ROUTER_SHA256, "terminal router"),
        (schema_path, ROUTER_SCHEMA_SHA256, "terminal router schema"),
    ):
        metadata = os.lstat(path)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ClosureError(f"{label} is not a regular non-symlink file")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise ClosureError(f"{label} identity mismatch")
    spec = importlib.util.spec_from_file_location(
        "_endpoint428_horizon_terminal_route_for_closure", router_path
    )
    if spec is None or spec.loader is None:
        raise ClosureError("cannot load the pinned terminal router")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _artifact_map(rows: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ClosureError(f"{label} must be an artifact list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "bytes", "sha256"}
            or not isinstance(row.get("path"), str)
        ):
            raise ClosureError(f"{label} contains a malformed artifact")
        path = row["path"]
        if path in result:
            raise ClosureError(f"{label} repeats artifact path: {path}")
        result[path] = row
    return result


def _verify_route_activation(
    project_root: Path,
    route_receipt_path: Path,
    expected_sha256: str,
    router: ModuleType,
) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence_root = (project_root / "operations/evidence").absolute()
    route_receipt_path = route_receipt_path.absolute()
    try:
        route_receipt_path.relative_to(evidence_root)
    except ValueError as error:
        raise ClosureError("terminal router receipt must be below operations/evidence") from error

    with router.ProjectReader(project_root) as reader:
        relative = _relative(project_root, route_receipt_path)
        artifact = reader.artifact(relative)
        if artifact["sha256"] != "sha256:" + _digest_text(expected_sha256):
            raise ClosureError("terminal router receipt hash argument mismatch")
        raw = reader.read_file(relative, max_bytes=JSON_LIMIT)
    if len(raw) != artifact["bytes"] or hashlib.sha256(raw).hexdigest() != artifact[
        "sha256"
    ][7:]:
        raise ClosureError("terminal router receipt changed while being read")
    supplied = _load_json_bytes(raw, "terminal router receipt")

    recomputed = router.route(project_root)
    if supplied != recomputed:
        raise ClosureError("terminal router receipt differs from pinned router recomputation")
    closure = supplied.get("output_closure")
    if (
        supplied.get("schema")
        != "gamma.enwiki9.endpoint428-horizon-terminal-route.v1"
        or supplied.get("candidate_id") != SOURCE_CANDIDATE_ID
        or supplied.get("status") != "TERMINAL_ROUTED"
        or supplied.get("terminal_state") != "completed"
        or supplied.get("terminal_returncode") != 0
        or supplied.get("branch") != "CORRECTION_RETRY_ONLY"
        or supplied.get("branch_reason")
        != "terminal result root contains undeclared artifacts"
        or supplied.get("host_lane_release") is not True
        or supplied.get("decision_accessed") is not True
        or supplied.get("result_root_accessed") is not True
        or supplied.get("claim_authority")
        != "zero-credit-terminal-routing-only"
        or not isinstance(closure, dict)
        or closure.get("complete") is not False
        or closure.get("failure_class") != "undeclared-extras"
        or closure.get("namespace_safe") is not True
        or closure.get("declared_output_count") != len(DECLARED_V1_NAMES)
        or closure.get("bound_output_count") != len(DECLARED_V1_NAMES)
        or closure.get("missing") != []
        or closure.get("nonregular") != []
        or set(closure.get("extras", [])) != UNDECLARED_V1_NAMES
        or set(closure.get("artifact_names", [])) != DECLARED_V1_NAMES
    ):
        raise ClosureError("terminal route is not the exact undeclared-extras correction")
    return supplied, artifact


def _bind_source_namespace(
    project_root: Path, router: ModuleType, route: dict[str, Any]
) -> list[dict[str, Any]]:
    with router.ProjectReader(project_root) as reader:
        observed = reader.list_dir(SOURCE_RESULT_ROOT)
        if set(observed) != SOURCE_NAMES or len(observed) != len(SOURCE_NAMES):
            missing = sorted(SOURCE_NAMES - set(observed))
            extra = sorted(set(observed) - SOURCE_NAMES)
            raise ClosureError(
                f"source result namespace mismatch: missing={missing} extra={extra}"
            )
        artifacts: list[dict[str, Any]] = []
        identities: dict[str, tuple[int, int, int, int, int]] = {}
        for name in sorted(SOURCE_NAMES):
            mode = reader.entry_mode(SOURCE_RESULT_ROOT, name)
            if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                raise ClosureError(f"source result is nonregular or symlinked: {name}")
            path = f"{SOURCE_RESULT_ROOT}/{name}"
            artifact, identity = reader.artifact_snapshot(path)
            artifacts.append(artifact)
            identities[path] = identity
        if reader.list_dir(SOURCE_RESULT_ROOT) != observed:
            raise ClosureError("source result namespace changed while it was bound")
        for path, identity in identities.items():
            reader.assert_identity(path, identity)

    observed_map = _artifact_map(artifacts, "source namespace")
    route_map = _artifact_map(
        route["output_closure"]["artifacts"], "terminal route output closure"
    )
    expected_declared_paths = {
        f"{SOURCE_RESULT_ROOT}/{name}" for name in DECLARED_V1_NAMES
    }
    if set(route_map) != expected_declared_paths:
        raise ClosureError("terminal route does not bind every declared v1 output")
    for path, row in route_map.items():
        if observed_map.get(path) != row:
            raise ClosureError(f"terminal route artifact changed: {path}")
    return artifacts


def _verify_route_bindings(
    project_root: Path, router: ModuleType, route: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    bindings = route.get("bindings")
    expected_keys = {
        "terminal_job",
        "reflection",
        "experiment",
        "proposal",
        "candidate_revision",
        "runner",
        "decision",
    }
    if not isinstance(bindings, dict) or set(bindings) != expected_keys:
        raise ClosureError("terminal route bindings are incomplete")
    verified: dict[str, dict[str, Any]] = {}
    with router.ProjectReader(project_root) as reader:
        identities: dict[str, tuple[int, int, int, int, int]] = {}
        for role in sorted(expected_keys):
            row = bindings[role]
            if (
                not isinstance(row, dict)
                or set(row) != {"path", "bytes", "sha256"}
                or not isinstance(row.get("path"), str)
            ):
                raise ClosureError(f"terminal {role} binding is malformed")
            observed, identity = reader.artifact_snapshot(row["path"])
            if observed != row:
                raise ClosureError(f"terminal {role} binding changed")
            verified[role] = observed
            identities[row["path"]] = identity
        for path, identity in identities.items():
            reader.assert_identity(path, identity)
    if verified["decision"]["path"] != SOURCE_DECISION_PATH:
        raise ClosureError("terminal decision binding points outside the v1 result")
    return verified


def _decision_and_branch(
    project_root: Path,
    router: ModuleType,
    route: dict[str, Any],
    decision_artifact: dict[str, Any],
) -> tuple[bytes, dict[str, Any], str]:
    with router.ProjectReader(project_root) as reader:
        raw = reader.read_file(SOURCE_DECISION_PATH, max_bytes=JSON_LIMIT)
    if (
        len(raw) != decision_artifact["bytes"]
        or "sha256:" + hashlib.sha256(raw).hexdigest()
        != decision_artifact["sha256"]
    ):
        raise ClosureError("source decision changed after terminal binding")
    decision = _load_json_bytes(raw, "source decision")
    promotion, kill, consistency = router._decision_consistency(decision)
    if (
        route.get("predicate_evaluations")
        != {"promotion": promotion, "kill": kill}
        or route.get("consistency") != consistency
    ):
        raise ClosureError("terminal route scientific recomputation changed")
    branch = (
        "EXACT_REPRICE_Q0_V2"
        if consistency["promotion_predicates_pass"]
        else "RETIRE_PHYSICAL_HORIZON"
    )
    expected_verdict = (
        "authorize_one_native_horizon_pkd_finite_coder"
        if branch == "EXACT_REPRICE_Q0_V2"
        else "retire_endpoint428_physical_horizon_a"
    )
    if decision.get("verdict") != expected_verdict:
        raise ClosureError("source decision verdict and recomputed branch differ")
    for value in decision.get("measurements", {}).values():
        if isinstance(value, float) and not math.isfinite(value):
            raise ClosureError("source decision contains a nonfinite measurement")
    return raw, decision, branch


def _write_new(path: Path, payload: bytes, mode: int = 0o644) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        mode,
    )
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validate_receipt(receipt: dict[str, Any]) -> None:
    schema_raw = (PROJECT / RECEIPT_SCHEMA_PATH).read_bytes()
    schema = _load_json_bytes(schema_raw, "output closure receipt schema")
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(receipt),
        key=lambda row: list(row.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ClosureError(
            f"output closure receipt fails schema at {location}: {errors[0].message}"
        )


def salvage(
    *,
    project_root: Path,
    terminal_route_receipt: Path,
    terminal_route_sha256: str,
    execution_mode: str,
) -> dict[str, Any]:
    project_root = project_root.absolute()
    root_metadata = os.lstat(project_root)
    if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_ISLNK(root_metadata.st_mode):
        raise ClosureError("project root must be a non-symlink directory")
    if execution_mode not in {"canonical", "synthetic"}:
        raise ClosureError("execution mode must be canonical or synthetic")
    if execution_mode == "canonical" and project_root != PROJECT:
        raise ClosureError("canonical execution cannot override the project root")

    router = _load_router(project_root)
    route, route_artifact = _verify_route_activation(
        project_root, terminal_route_receipt, terminal_route_sha256, router
    )
    source_artifacts = _bind_source_namespace(project_root, router, route)
    bindings = _verify_route_bindings(project_root, router, route)
    decision_raw, decision, scientific_branch = _decision_and_branch(
        project_root, router, route, bindings["decision"]
    )

    with router.ProjectReader(project_root) as reader:
        dependency_artifacts = {
            "closure_tool": reader.artifact(TOOL_PATH),
            "closure_schema": reader.artifact(RECEIPT_SCHEMA_PATH),
            "terminal_router": reader.artifact(ROUTER_PATH),
            "terminal_router_schema": reader.artifact(ROUTER_SCHEMA_PATH),
        }
    if dependency_artifacts["terminal_router"]["sha256"] != "sha256:" + ROUTER_SHA256:
        raise ClosureError("terminal router drifted after recomputation")
    if dependency_artifacts["terminal_router_schema"]["sha256"] != (
        "sha256:" + ROUTER_SCHEMA_SHA256
    ):
        raise ClosureError("terminal router schema drifted after recomputation")

    preserved_artifact = {
        "path": f"{RESULT_ROOT}/{PRESERVED_DECISION_NAME}",
        "bytes": len(decision_raw),
        "sha256": "sha256:" + hashlib.sha256(decision_raw).hexdigest(),
    }
    if preserved_artifact["sha256"] != bindings["decision"]["sha256"]:
        raise ClosureError("preserved decision bytes differ from the v1 decision")

    receipt = {
        "schema": "gamma.enwiki9.endpoint428-horizon-output-closure-receipt.v1",
        "candidate_id": CANDIDATE_ID,
        "status": "closed",
        "execution_mode": execution_mode,
        "source_candidate_id": SOURCE_CANDIDATE_ID,
        "activation": {
            "terminal_route_receipt": route_artifact,
            "terminal_route_receipt_hash_argument": "sha256:"
            + _digest_text(terminal_route_sha256),
            "terminal_route_object_matches_recomputation": True,
            "incoming_branch": "CORRECTION_RETRY_ONLY",
            "incoming_failure_class": "undeclared-extras",
        },
        "dependencies": dependency_artifacts,
        "immutable_bindings": bindings,
        "source_namespace": {
            "path": SOURCE_RESULT_ROOT,
            "expected_artifact_count": len(SOURCE_NAMES),
            "observed_artifact_count": len(source_artifacts),
            "expected_names": sorted(SOURCE_NAMES),
            "exact_names_pass": True,
            "all_regular_non_symlink_pass": True,
            "artifacts": source_artifacts,
        },
        "decision_preservation": {
            "source": bindings["decision"],
            "preserved_copy": preserved_artifact,
            "byte_identical": True,
            "source_verdict": decision["verdict"],
            "source_promotion_authorized": decision["promotion_authorized"],
            "scientific_values_modified": False,
        },
        "routing": {
            "incoming_branch": "CORRECTION_RETRY_ONLY",
            "recomputed_scientific_branch": scientific_branch,
            "branch_recomputed_from_unchanged_decision": True,
            "predicate_evaluations": route["predicate_evaluations"],
            "consistency": route["consistency"],
        },
        "output_manifest": {
            "policy": "complete-result-artifacts-v1",
            "declared_names": sorted(OUTPUT_NAMES),
            "decision_entry": preserved_artifact,
            "receipt_self_exclusion": {
                "path": f"{RESULT_ROOT}/{RECEIPT_NAME}",
                "reason": "terminal receipt is published last and cannot hash itself",
            },
            "exact_names_pass": True,
            "receipt_published_last": True,
            "no_clobber": True,
        },
        "authority": {
            "archive_authority": False,
            "score_credit_bytes": 0,
            "verified_full_1g_score_bytes": None,
            "hutter_result_authority": False,
            "corpus_accessed": False,
            "cmix_invoked": False,
            "analyzer_invoked": False,
            "source_result_mutated": False,
        },
        "claim_boundary": [
            "Output-namespace closure only; every v1 scientific byte is immutable.",
            "No CMIX, manifest, analysis, archive, inverse, package, resource, or score claim is produced.",
            "The preserved branch may be acted on only by separately registered terminal governance.",
        ],
    }
    _validate_receipt(receipt)

    output_root = project_root / RESULT_ROOT
    try:
        os.lstat(output_root)
    except FileNotFoundError:
        pass
    else:
        raise ClosureError("successor result root already exists or is symlinked")
    output_parent = output_root.parent
    parent_metadata = os.lstat(output_parent)
    if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_ISLNK(parent_metadata.st_mode):
        raise ClosureError("successor result parent must be a non-symlink directory")
    os.mkdir(output_root, mode=0o700)
    preserved_path = output_root / PRESERVED_DECISION_NAME
    _write_new(preserved_path, decision_raw)
    receipt_path = output_root / RECEIPT_NAME
    _write_new(receipt_path, _canonical_json(receipt))
    directory_fd = os.open(output_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    if set(os.listdir(output_root)) != OUTPUT_NAMES:
        raise ClosureError("successor output namespace differs after receipt publication")
    if preserved_path.read_bytes() != decision_raw:
        raise ClosureError("preserved decision changed after receipt publication")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal-route-receipt", type=Path, required=True)
    parser.add_argument("--terminal-route-sha256", required=True)
    arguments = parser.parse_args(argv)
    if Path.cwd().absolute() != PROJECT:
        raise ClosureError(f"runner must execute from {PROJECT}")
    receipt = salvage(
        project_root=PROJECT,
        terminal_route_receipt=arguments.terminal_route_receipt,
        terminal_route_sha256=arguments.terminal_route_sha256,
        execution_mode="canonical",
    )
    receipt_path = PROJECT / RESULT_ROOT / RECEIPT_NAME
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "receipt": {
                    "path": _relative(PROJECT, receipt_path),
                    "bytes": receipt_path.stat().st_size,
                    "sha256": "sha256:" + hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                },
                "recomputed_scientific_branch": receipt["routing"][
                    "recomputed_scientific_branch"
                ],
                "score_credit_bytes": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
