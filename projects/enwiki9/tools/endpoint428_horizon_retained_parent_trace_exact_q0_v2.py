#!/usr/bin/env python3
"""Reanalyze terminal HORIZON v1 evidence with exact Q63 division."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_exact_q0_v2"
V1_ID = "endpoint428_horizon_retained_parent_trace_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID
V1_RESULT = PROJECT / "results" / V1_ID
V1_DECISION = V1_RESULT / "decision.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PLAN = PROJECT / "operations/planning" / f"{CANDIDATE_ID}.json"
SOURCE_BINDING: Path
ANALYZER_SOURCE: Path
FIXTURE_SOURCE: Path
REFERENCE: Path
ARITHMETIC_HEADER: Path
ANALYSIS_SCHEMA: Path
FIXTURE_SCHEMA: Path
DECISION_SCHEMA: Path
INTERFACE: Path
GUARD = PROJECT / "tools/run_with_rss_guard.py"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")
TASKSET = Path("/usr/bin/taskset")

TRACE_ROWS = 5_182_388_736
TRACE_BYTES = 16 + 2 * TRACE_ROWS
ACTIVE_BYTES = 2_331_505
MANIFEST_BYTES = 32 + 13 * ACTIVE_BYTES
GROSS_GATE_BITS = 40_163_160.0
TREE_LIMIT_KIB = 1_048_576
V1_EXPERIMENT_SHA256 = (
    "1ee83f431531f05654ac0990de302acbbbde36fa4ac42acd3bebbd9dd26f20aa"
)
V1_ANALYZER_SHA256 = (
    "0dbff9c0a989981c4ce982951a5b05cb94c8cce884ebe7f6cf0db0ab23537ed9"
)

BASE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}
COMPILE_FLAGS = [
    "-std=c++17",
    "-O2",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-pedantic",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-march=x86-64",
    "-mtune=generic",
    "-Wl,--build-id=none",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT).as_posix()
    except ValueError:
        return str(resolved)


def assert_regular_no_symlink(path: Path, *, one_link: bool = False) -> None:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise RuntimeError(f"artifact must be a regular non-symlink: {path}")
    if one_link and metadata.st_nlink != 1:
        raise RuntimeError(f"artifact must have one hard link: {path}")


def artifact(path: Path, known_hash: str | None = None) -> dict[str, Any]:
    assert_regular_no_symlink(path)
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "sha256": known_hash or sha256(path),
    }


def load_json(path: Path) -> dict[str, Any]:
    assert_regular_no_symlink(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return value


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    raw = json.dumps(
        value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(raw):
            written = os.write(descriptor, raw[cursor:])
            if written <= 0:
                raise OSError("short write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate(value: dict[str, Any], schema_path: Path) -> None:
    jsonschema.Draft202012Validator(load_json(schema_path)).validate(value)


def active_v1_jobs() -> list[str]:
    matches: list[str] = []
    for state in ("running", "pending"):
        root = PROJECT / "operations/adaptive" / state
        for path in sorted(root.glob("*.json")):
            try:
                value = load_json(path)
            except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
                continue
            if value.get("candidate_id") == V1_ID:
                matches.append(display_path(path))
    return matches


def require_v1_terminal() -> dict[str, Any]:
    """Reject before touching v1 trace/manifest or the v2 result directory."""
    active = active_v1_jobs()
    if active:
        raise RuntimeError(
            "v1 is nonterminal; exact v2 refuses while active jobs exist: "
            + ", ".join(active)
        )
    if not V1_DECISION.is_file() or V1_DECISION.is_symlink():
        raise RuntimeError("v1 is nonterminal: terminal decision.json is absent")
    decision_hash = sha256(V1_DECISION)
    decision = load_json(V1_DECISION)
    if (
        decision.get("schema")
        != "gamma.enwiki9.endpoint428-horizon-retained-parent-trace-decision.v1"
        or decision.get("candidate_id") != V1_ID
    ):
        raise RuntimeError("v1 terminal decision identity mismatch")

    reflection_path: Path | None = None
    reflection: dict[str, Any] | None = None
    for path in sorted((PROJECT / "operations/adaptive/reflections").glob("*.json")):
        value = load_json(path)
        if value.get("candidateId") != V1_ID:
            continue
        validity = value.get("validity", {})
        if validity.get("valid") is not True or validity.get("classification") != "valid":
            continue
        evidence = value.get("evidence", [])
        if any(
            row.get("path") == f"results/{V1_ID}/decision.json"
            and row.get("sha256") == f"sha256:{decision_hash}"
            for row in evidence
            if isinstance(row, dict)
        ):
            reflection_path = path
            reflection = value
    if reflection_path is None or reflection is None:
        raise RuntimeError(
            "v1 is nonterminal: no validated reflection binds the terminal decision"
        )
    return {
        "decision": decision,
        "decision_artifact": artifact(V1_DECISION, decision_hash),
        "reflection": reflection,
        "reflection_artifact": artifact(reflection_path),
    }


def bind_snapshot_candidate() -> dict[str, Any]:
    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    snapshot_raw = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    revision_raw = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    if snapshot_id != CANDIDATE_ID or not snapshot_raw or not revision_raw:
        raise RuntimeError("adaptive snapshot candidate binding is required")
    root = Path(snapshot_raw)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise RuntimeError("adaptive snapshot root is invalid")
    revision_binding = json.loads(revision_raw)
    if not isinstance(revision_binding, dict) or revision_binding.get("candidateId") != CANDIDATE_ID:
        raise RuntimeError("adaptive revision binding candidate mismatch")
    receipt_record = revision_binding.get("receipt")
    if not isinstance(receipt_record, dict):
        raise RuntimeError("adaptive revision receipt binding missing")
    receipt_path = PROJECT / str(receipt_record.get("path", ""))
    receipt_hash = str(receipt_record.get("sha256", "")).removeprefix("sha256:")
    receipt_artifact = artifact(receipt_path)
    if receipt_artifact["sha256"] != receipt_hash:
        raise RuntimeError("adaptive revision receipt hash mismatch")
    receipt = load_json(receipt_path)
    tree = str(revision_binding.get("candidateTreeSha256", ""))
    if (
        receipt.get("candidateId") != CANDIDATE_ID
        or receipt.get("candidateTreeSha256") != tree
        or not receipt.get("immutableBlobsComplete")
    ):
        raise RuntimeError("adaptive revision tree binding mismatch")
    records = receipt.get("files")
    if not isinstance(records, list):
        raise RuntimeError("adaptive revision file closure missing")
    expected: set[str] = set()
    for record in records:
        relative = str(record.get("path", ""))
        path = root / relative
        assert_regular_no_symlink(path, one_link=True)
        if path.stat().st_size != record.get("bytes") or sha256(path) != record.get("sha256"):
            raise RuntimeError(f"adaptive snapshot file mismatch: {relative}")
        expected.add(relative)
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if observed != expected:
        raise RuntimeError("adaptive snapshot file-set closure mismatch")

    global SOURCE_BINDING, ANALYZER_SOURCE, FIXTURE_SOURCE, REFERENCE
    global ARITHMETIC_HEADER, ANALYSIS_SCHEMA, FIXTURE_SCHEMA
    global DECISION_SCHEMA, INTERFACE
    SOURCE_BINDING = root / "source-binding.json"
    ANALYZER_SOURCE = root / "horizon-retained-analyze-exact.cpp"
    FIXTURE_SOURCE = root / "horizon-exact-fixture.cpp"
    REFERENCE = root / "horizon-exact-reference.py"
    ARITHMETIC_HEADER = root / "horizon-exact-arithmetic.h"
    ANALYSIS_SCHEMA = root / "analysis.schema.json"
    FIXTURE_SCHEMA = root / "fixture-verification.schema.json"
    DECISION_SCHEMA = root / "decision.schema.json"
    INTERFACE = root / "interface-contract.json"
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_tree_sha256": tree,
        "revision_receipt": receipt_artifact,
    }


def verify_record(path: Path, record: dict[str, Any], label: str) -> dict[str, Any]:
    assert_regular_no_symlink(path, one_link=True)
    observed = artifact(path)
    recorded_path = Path(str(record.get("path", ""))).resolve()
    if recorded_path != path.resolve():
        raise RuntimeError(f"{label} path mismatch")
    if (
        observed["bytes"] != record.get("bytes")
        or observed["sha256"] != record.get("sha256")
    ):
        raise RuntimeError(f"{label} terminal artifact identity mismatch")
    return observed


def verify_source_binding() -> dict[str, Any]:
    binding = load_json(SOURCE_BINDING)
    if binding.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("source binding candidate mismatch")
    records = binding.get("artifacts")
    if not isinstance(records, list):
        raise RuntimeError("source binding artifact list missing")
    candidate_prefix = f"programs/{CANDIDATE_ID}/"
    expected = {
        "operations/planning/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": PLAN,
        "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": EXPERIMENT,
        candidate_prefix + "horizon-retained-analyze-exact.cpp": ANALYZER_SOURCE,
        candidate_prefix + "horizon-exact-fixture.cpp": FIXTURE_SOURCE,
        candidate_prefix + "horizon-exact-reference.py": REFERENCE,
        candidate_prefix + "horizon-exact-arithmetic.h": ARITHMETIC_HEADER,
        candidate_prefix + "analysis.schema.json": ANALYSIS_SCHEMA,
        candidate_prefix + "fixture-verification.schema.json": FIXTURE_SCHEMA,
        candidate_prefix + "decision.schema.json": DECISION_SCHEMA,
        candidate_prefix + "interface-contract.json": INTERFACE,
        "tools/endpoint428_horizon_retained_parent_trace_exact_q0_v2.py": Path(__file__).resolve(),
    }
    observed_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("malformed source binding record")
        relative = str(record.get("path", ""))
        if relative not in expected or relative in observed_paths:
            raise RuntimeError(f"unexpected source binding path: {relative}")
        path = expected[relative]
        row = artifact(path)
        if row["bytes"] != record.get("bytes") or row["sha256"] != record.get("sha256"):
            raise RuntimeError(f"source binding mismatch: {relative}")
        observed_paths.add(relative)
    if observed_paths != set(expected):
        raise RuntimeError("source binding closure mismatch")
    return artifact(SOURCE_BINDING)


def run_logged(command: list[str], log: Path) -> None:
    with log.open("xb") as output:
        completed = subprocess.run(
            command,
            cwd=PROJECT,
            env=BASE_ENVIRONMENT,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed returncode={completed.returncode}: {command}")


def run_guarded(label: str, command: list[str], limit_kib: int) -> dict[str, Any]:
    available = sorted(os.sched_getaffinity(0))
    if not available:
        raise RuntimeError("no available logical CPU")
    guard_path = RESULT / f"{label}-guard.json"
    log_path = RESULT / f"{label}.log"
    invocation = [
        sys.executable,
        str(GUARD),
        "--limit-kib",
        str(limit_kib),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "1",
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard_path),
        "--label",
        f"{CANDIDATE_ID}_{label}",
        "--phase",
        "diagnostic",
        "--",
        str(TASKSET),
        "-c",
        str(available[0]),
        *command,
    ]
    run_logged(invocation, log_path)
    receipt = load_json(guard_path)
    if (
        receipt.get("returncode") != 0
        or receipt.get("status") != "complete"
        or receipt.get("rss_guard_exceeded") is not False
    ):
        raise RuntimeError(f"guard failed for {label}: {receipt}")
    return {
        "guard": artifact(guard_path),
        "log": artifact(log_path),
        "receipt": receipt,
    }


def compare_legacy(exact: dict[str, Any], legacy: dict[str, Any]) -> None:
    for field in (
        "active_bytes",
        "parent_trace_rows",
        "parent_truth_bits",
        "parent_truth_bits_by_third",
        "coordinate_fnv1a64",
    ):
        if exact.get(field) != legacy.get(field):
            raise RuntimeError(f"legacy parity failed at {field}")
    if (
        exact.get("legacy_minimum_third_mixture_gain_bits")
        != legacy.get("minimum_third_mixture_gain_bits")
        or exact.get("legacy_minimum_control_margin_bits")
        != legacy.get("minimum_control_margin_bits")
    ):
        raise RuntimeError("legacy aggregate margin parity failed")
    for arm_id in ("D", "S", "R", "N"):
        new = exact["arms"][arm_id]
        old = legacy["arms"][arm_id]
        for field in ("raw_truth_bits", "raw_gain_bits", "raw_gain_by_third"):
            if new.get(field) != old.get(field):
                raise RuntimeError(f"legacy raw parity failed at {arm_id}.{field}")
        mapping = {
            "legacy_mixture_truth_bits": "mixture_truth_bits",
            "legacy_mixture_gain_bits": "mixture_gain_bits",
            "legacy_mixture_gain_by_third": "mixture_gain_by_third",
            "terminal_legacy_parent_weight_q63": "terminal_parent_weight_q63",
        }
        for new_field, old_field in mapping.items():
            if new.get(new_field) != old.get(old_field):
                raise RuntimeError(
                    f"legacy mixture parity failed at {arm_id}.{new_field}"
                )
        if new.get("legacy_exact_kt_identity_pass") is not True:
            raise RuntimeError(f"exact/legacy KT state diverged for {arm_id}")


def result_manifest() -> dict[str, Any]:
    roles = [
        ("build", "build.json"),
        ("compile-log", "compile-analyzer.log"),
        ("compile-log", "compile-fixture.log"),
        ("fixture-vectors", "arithmetic-vectors.tsv"),
        ("resource-guard", "fixture-guard.json"),
        ("execution-log", "fixture.log"),
        ("resource-guard", "fixture-reference-guard.json"),
        ("execution-log", "fixture-reference.log"),
        ("fixture-verification", "fixture-verification.json"),
        ("resource-guard", "analysis-a-guard.json"),
        ("execution-log", "analysis-a.log"),
        ("analysis", "analysis-a.json"),
        ("resource-guard", "analysis-b-guard.json"),
        ("execution-log", "analysis-b.log"),
        ("analysis", "analysis-b.json"),
        ("decision", "decision.json"),
    ]
    observed = sorted(path.name for path in RESULT.iterdir())
    expected = {name for _, name in roles}
    exact = set(observed) == expected and all(
        path.is_file() and not path.is_symlink() for path in RESULT.iterdir()
    )
    artifacts: list[dict[str, Any]] = []
    for role, name in roles:
        row = artifact(RESULT / name)
        row["path"] = name
        row["role"] = role
        artifacts.append(row)
    return {
        "schema": "gamma.enwiki9.horizon-retained-exact-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "result_root": f"results/{CANDIDATE_ID}",
        "pre_manifest_exact_file_set_pass": exact,
        "complete_result_artifacts_pass": exact and len(artifacts) == len(roles),
        "artifacts": artifacts,
    }


def main() -> int:
    terminal = require_v1_terminal()
    snapshot = bind_snapshot_candidate()

    required = (
        PLAN,
        EXPERIMENT,
        SOURCE_BINDING,
        ANALYZER_SOURCE,
        FIXTURE_SOURCE,
        REFERENCE,
        ARITHMETIC_HEADER,
        ANALYSIS_SCHEMA,
        FIXTURE_SCHEMA,
        DECISION_SCHEMA,
        INTERFACE,
        GUARD,
        COMPILER,
        TASKSET,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing required inputs: {missing}")
    if not RESULT.is_dir() or RESULT.is_symlink() or any(RESULT.iterdir()):
        raise RuntimeError(f"result directory must be precreated and empty: {RESULT}")

    if sha256(
        PROJECT / "operations/adaptive/experiments" / f"{V1_ID}.json"
    ) != V1_EXPERIMENT_SHA256:
        raise RuntimeError("immutable v1 experiment changed")
    if sha256(
        PROJECT / "programs" / V1_ID / "horizon-retained-analyze.cpp"
    ) != V1_ANALYZER_SHA256:
        raise RuntimeError("immutable v1 analyzer changed")
    binding_artifact = verify_source_binding()

    v1 = terminal["decision"]
    trace_path = V1_RESULT / "parent.p1"
    manifest_path = V1_RESULT / "manifest-a.bin"
    legacy_analysis_path = V1_RESULT / "analysis-a.json"
    trace = verify_record(trace_path, v1["parent"]["trace"], "v1 trace")
    manifest = verify_record(
        manifest_path, v1["manifests"]["a"]["manifest"], "v1 manifest"
    )
    legacy_analysis_artifact = verify_record(
        legacy_analysis_path,
        v1["analyses"]["a"]["artifact"],
        "v1 analysis",
    )
    if trace["bytes"] != TRACE_BYTES or manifest["bytes"] != MANIFEST_BYTES:
        raise RuntimeError("terminal v1 trace/manifest geometry mismatch")
    legacy_analysis = load_json(legacy_analysis_path)
    if legacy_analysis != v1["analyses"]["a"]["values"]:
        raise RuntimeError("v1 embedded analysis does not match artifact")

    with tempfile.TemporaryDirectory(prefix="gamma-horizon-exact-") as temporary:
        build = Path(temporary)
        analyzer_binary = build / "horizon-retained-analyze-exact"
        fixture_binary = build / "horizon-exact-fixture"
        run_logged(
            [str(COMPILER), *COMPILE_FLAGS, str(ANALYZER_SOURCE), "-o", str(analyzer_binary)],
            RESULT / "compile-analyzer.log",
        )
        run_logged(
            [str(COMPILER), *COMPILE_FLAGS, str(FIXTURE_SOURCE), "-o", str(fixture_binary)],
            RESULT / "compile-fixture.log",
        )
        write_json_exclusive(
            RESULT / "build.json",
            {
                "schema": "gamma.enwiki9.horizon-retained-exact-build.v1",
                "candidate_id": CANDIDATE_ID,
                "flags": COMPILE_FLAGS,
                "compiler": artifact(COMPILER),
                "analyzer_binary": artifact(analyzer_binary),
                "fixture_binary": artifact(fixture_binary),
                "archive_authority": False,
                "score_credit_bytes": 0,
            },
        )

        vectors = RESULT / "arithmetic-vectors.tsv"
        fixture_phase = run_guarded(
            "fixture", [str(fixture_binary), str(vectors)], 131_072
        )
        fixture_receipt_path = RESULT / "fixture-verification.json"
        fixture_reference_phase = run_guarded(
            "fixture-reference",
            [
                sys.executable,
                str(REFERENCE),
                "--native",
                str(vectors),
                "--receipt",
                str(fixture_receipt_path),
            ],
            131_072,
        )
        fixture_receipt = load_json(fixture_receipt_path)
        validate(fixture_receipt, FIXTURE_SCHEMA)
        if fixture_receipt.get("terminal_pass") is not True:
            raise RuntimeError("exact arithmetic fixture failed")

        analyses: dict[str, dict[str, Any]] = {}
        for repeat in ("a", "b"):
            output = RESULT / f"analysis-{repeat}.json"
            phase = run_guarded(
                f"analysis-{repeat}",
                [str(analyzer_binary), str(trace_path), str(manifest_path), str(output)],
                TREE_LIMIT_KIB,
            )
            values = load_json(output)
            validate(values, ANALYSIS_SCHEMA)
            analyses[repeat] = {
                "artifact": artifact(output),
                "values": values,
                "phase": phase,
            }
        if analyses["a"]["values"] != analyses["b"]["values"]:
            raise RuntimeError("exact full-trace analyzer repeat identity failed")

    values = analyses["a"]["values"]
    compare_legacy(values, legacy_analysis)
    treatment_gain = float(values["arms"]["D"]["mixture_gain_bits"])
    minimum_third = float(values["minimum_third_mixture_gain_bits"])
    minimum_control = float(values["minimum_control_margin_bits"])
    gates = {
        "completeActivePopulationPass": values["active_bytes"] == ACTIVE_BYTES,
        "completeParentTracePass": values["parent_trace_rows"] == TRACE_ROWS,
        "targetBearingMixturePass": treatment_gain >= GROSS_GATE_BITS,
        "everyThirdPositivePass": minimum_third > 0.0,
        "controlsSeparatedPass": minimum_control > 0.0,
        "analysisRepeatPass": analyses["a"]["values"] == analyses["b"]["values"],
        "legacyParityPass": True,
        "arbitraryPrecisionFixturePass": fixture_receipt["terminal_pass"] is True,
        "parentReadOnlyPass": bool(v1["gates"]["parentReadOnlyPass"]),
    }
    scientific_pass = all(gates.values())
    decision = {
        "schema": "gamma.enwiki9.endpoint428-horizon-retained-exact-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal",
        "evidence_class": "causal-shadow",
        "claim_boundary": (
            "Exact integer reanalysis of immutable v1 probabilities and donors. "
            "It proves no changed arithmetic archive, inverse, package score, "
            "composite eligibility, or Hutter result."
        ),
        "inputs": {
            "candidate_snapshot": snapshot,
            "plan": artifact(PLAN),
            "experiment": artifact(EXPERIMENT),
            "source_binding": binding_artifact,
            "v1_decision": terminal["decision_artifact"],
            "v1_reflection": terminal["reflection_artifact"],
            "v1_parent_trace": trace,
            "v1_manifest_a": manifest,
            "v1_analysis_a": legacy_analysis_artifact,
        },
        "fixture": {
            "receipt": artifact(RESULT / "fixture-verification.json"),
            "values": fixture_receipt,
            "native_phase": fixture_phase,
            "reference_phase": fixture_reference_phase,
        },
        "analyses": analyses,
        "measurements": {
            "activeBytes": int(values["active_bytes"]),
            "parentTraceRows": int(values["parent_trace_rows"]),
            "treatmentMixtureGainBits": treatment_gain,
            "minimumThirdMixtureGainBits": minimum_third,
            "minimumControlMarginBits": minimum_control,
            "firstLegacyDivergence": values["first_legacy_divergence"],
        },
        "gates": gates,
        "verdict": (
            "authorize_endpoint428_horizon_a_native_pkd_q0_v1"
            if scientific_pass
            else "retire_endpoint428_physical_horizon_a"
        ),
        "promotion_authorized": scientific_pass,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "verified_full_1g_score_bytes": None,
    }
    validate(decision, DECISION_SCHEMA)
    write_json_exclusive(RESULT / "decision.json", decision)
    manifest_receipt = result_manifest()
    if manifest_receipt["complete_result_artifacts_pass"] is not True:
        raise RuntimeError("result closure failed")
    write_json_exclusive(RESULT / "output-manifest.json", manifest_receipt)
    print(json.dumps({
        "decision": display_path(RESULT / "decision.json"),
        "treatment_mixture_gain_bits": treatment_gain,
        "verdict": decision["verdict"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
