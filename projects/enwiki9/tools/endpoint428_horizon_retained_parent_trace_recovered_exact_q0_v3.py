#!/usr/bin/env python3
"""Run frozen exact HORIZON science on the sealed orphan-recovery trace."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
from typing import Any

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3"
ADOPTION_ID = "endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1"
SOURCE_ID = "endpoint428_horizon_retained_parent_trace_q0_v1"
EXACT_V2_ID = "endpoint428_horizon_retained_parent_trace_exact_q0_v2"
RESULT = PROJECT / "results" / CANDIDATE_ID
ADOPTION_RESULT = PROJECT / "results" / ADOPTION_ID / "result.json"
ADOPTION_TERMINAL = PROJECT / "results" / ADOPTION_ID / "terminal-source.json"
PLAN = PROJECT / "operations/planning" / f"{CANDIDATE_ID}.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
EXACT_ROOT = PROJECT / "programs" / EXACT_V2_ID
LEGACY_ROOT = PROJECT / "programs" / SOURCE_ID
EXACT_ANALYZER = EXACT_ROOT / "horizon-retained-analyze-exact.cpp"
EXACT_FIXTURE = EXACT_ROOT / "horizon-exact-fixture.cpp"
EXACT_REFERENCE = EXACT_ROOT / "horizon-exact-reference.py"
EXACT_HEADER = EXACT_ROOT / "horizon-exact-arithmetic.h"
EXACT_SCHEMA = EXACT_ROOT / "analysis.schema.json"
FIXTURE_SCHEMA = EXACT_ROOT / "fixture-verification.schema.json"
LEGACY_ANALYZER = LEGACY_ROOT / "horizon-retained-analyze.cpp"
V2_RUNNER = PROJECT / "tools/endpoint428_horizon_retained_parent_trace_exact_q0_v2.py"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")

TRACE_MAGIC = b"CMIX21P1"
TRACE_ROWS = 5_182_388_736
TRACE_BYTES = 16 + 2 * TRACE_ROWS
ACTIVE_BYTES = 2_331_505
MANIFEST_BYTES = 32 + 13 * ACTIVE_BYTES
GROSS_GATE_BITS = 40_163_160.0
TREE_LIMIT_KIB = 1_048_576

EXPECTED_HASHES = {
    "operations/planning/endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3.json": "ef3a0de1dc9198d15c2db8e5d4a53184b70c84eaf9d20c0b47dd3a758a9093cb",
    "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3.json": "0e22050718281c80ed99d97b84b8ac80b122e9863d5f4e9133dc8dc8a75c0732",
    "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json": "2f94fdaecef558ae292eebe3315bbcc604b4d86ee2c7d3a38cc59fd064dd8aa2",
    "operations/planning/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": "48d37ae1006feedcc78f6bb28975ade7b96343c9874bda9207a6636e24d00f1b",
    "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": "286fc55420be2416478c819ec9b848b1de655d2408370aefcd70d9ea67ccfade",
    "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2/horizon-retained-analyze-exact.cpp": "32e8602189be3c7024a0560d0e01e19bbc5bee48f07cc17678da81a641339029",
    "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2/horizon-exact-fixture.cpp": "126d1ed89cd264da304a6bbfa2ec479993bcbc42e07e2adce5788b0d9ee24318",
    "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2/horizon-exact-reference.py": "437ea4e282b0c446dbe12811165b9b0c78f984ffcc89e68b2443f974ebbed7af",
    "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2/horizon-exact-arithmetic.h": "e078e662bf68c5ef09fef846fcfef93941b5f395e3a4bb3ccebcc072d34268b5",
    "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2/analysis.schema.json": "cd076e490a3c242096e91c18bf14eba3f6c6f5f0019496798ecbb3bc6a5e1cb1",
    "programs/endpoint428_horizon_retained_parent_trace_exact_q0_v2/fixture-verification.schema.json": "a4f9bc396f476450cd948ad048f6e23874c17866dfb2bdd915df85f6a0e8d104",
    "programs/endpoint428_horizon_retained_parent_trace_q0_v1/horizon-retained-analyze.cpp": "0dbff9c0a989981c4ce982951a5b05cb94c8cce884ebe7f6cf0db0ab23537ed9",
    "tools/endpoint428_horizon_retained_parent_trace_exact_q0_v2.py": "92b415c928fedb5dea8b59059e209dbc2437aba4a2288d7d1e4d6db0a5857287",
}


def load_v2() -> Any:
    spec = importlib.util.spec_from_file_location("gamma_horizon_exact_v2", V2_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen exact-v2 runner library")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.CANDIDATE_ID = CANDIDATE_ID
    module.RESULT = RESULT
    return module


V2 = load_v2()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return value


def assert_regular(path: Path, *, one_link: bool = False) -> os.stat_result:
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"artifact must be a regular non-symlink: {path}")
    if one_link and info.st_nlink != 1:
        raise RuntimeError(f"artifact must have one hard link: {path}")
    return info


def artifact(path: Path, known_hash: str | None = None) -> dict[str, Any]:
    info = assert_regular(path)
    try:
        display = path.resolve().relative_to(PROJECT).as_posix()
    except ValueError:
        display = str(path.resolve())
    return {
        "path": display,
        "bytes": info.st_size,
        "sha256": known_hash or sha256(path),
    }


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


def active_adoption_jobs() -> list[str]:
    matches: list[str] = []
    for state in ("running", "pending"):
        root = PROJECT / "operations/adaptive" / state
        for path in sorted(root.glob("*.json")):
            try:
                value = load_json(path)
            except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
                continue
            if value.get("candidate_id") == ADOPTION_ID:
                matches.append(path.relative_to(PROJECT).as_posix())
    return matches


def bind_candidate_snapshot() -> tuple[Path, dict[str, Any]]:
    candidate = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    root_raw = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    revision_raw = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    if candidate != CANDIDATE_ID or not root_raw or not revision_raw:
        raise RuntimeError("adaptive snapshot candidate binding is required")
    root = Path(root_raw).resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("adaptive snapshot root is invalid")
    revision = json.loads(revision_raw)
    if not isinstance(revision, dict) or revision.get("candidateId") != CANDIDATE_ID:
        raise RuntimeError("adaptive revision candidate mismatch")
    receipt_ref = revision.get("receipt")
    if not isinstance(receipt_ref, dict):
        raise RuntimeError("adaptive revision receipt is missing")
    receipt_path = PROJECT / str(receipt_ref.get("path", ""))
    receipt = load_json(receipt_path)
    receipt_hash = str(receipt_ref.get("sha256", "")).removeprefix("sha256:")
    if sha256(receipt_path) != receipt_hash:
        raise RuntimeError("adaptive revision receipt hash mismatch")
    if (
        receipt.get("candidateId") != CANDIDATE_ID
        or receipt.get("candidateTreeSha256")
        != revision.get("candidateTreeSha256")
        or receipt.get("immutableBlobsComplete") is not True
    ):
        raise RuntimeError("adaptive revision tree mismatch")
    expected: set[str] = set()
    for row in receipt.get("files", []):
        relative = str(row.get("path", ""))
        path = root / relative
        assert_regular(path, one_link=True)
        if path.stat().st_size != row.get("bytes") or sha256(path) != row.get("sha256"):
            raise RuntimeError(f"adaptive snapshot file mismatch: {relative}")
        expected.add(relative)
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if observed != expected:
        raise RuntimeError("adaptive snapshot file-set closure mismatch")
    return root, {
        "candidate_id": CANDIDATE_ID,
        "candidate_tree_sha256": revision["candidateTreeSha256"],
        "revision_receipt": artifact(receipt_path, receipt_hash),
    }


def verify_source_binding(snapshot_root: Path) -> dict[str, Any]:
    binding_path = snapshot_root / "source-binding.json"
    binding = load_json(binding_path)
    if binding.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("source-binding candidate mismatch")
    own_prefix = f"programs/{CANDIDATE_ID}/"
    expected_paths: dict[str, Path] = {
        "operations/planning/endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3.json": PLAN,
        "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3.json": EXPERIMENT,
        "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1.json": PROJECT / "operations/adaptive/experiments" / f"{ADOPTION_ID}.json",
        "operations/planning/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": PROJECT / "operations/planning" / f"{EXACT_V2_ID}.json",
        "operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json": PROJECT / "operations/adaptive/experiments" / f"{EXACT_V2_ID}.json",
        f"programs/{EXACT_V2_ID}/horizon-retained-analyze-exact.cpp": EXACT_ANALYZER,
        f"programs/{EXACT_V2_ID}/horizon-exact-fixture.cpp": EXACT_FIXTURE,
        f"programs/{EXACT_V2_ID}/horizon-exact-reference.py": EXACT_REFERENCE,
        f"programs/{EXACT_V2_ID}/horizon-exact-arithmetic.h": EXACT_HEADER,
        f"programs/{EXACT_V2_ID}/analysis.schema.json": EXACT_SCHEMA,
        f"programs/{EXACT_V2_ID}/fixture-verification.schema.json": FIXTURE_SCHEMA,
        f"programs/{SOURCE_ID}/horizon-retained-analyze.cpp": LEGACY_ANALYZER,
        "tools/endpoint428_horizon_retained_parent_trace_exact_q0_v2.py": V2_RUNNER,
        f"tools/{Path(__file__).name}": Path(__file__).resolve(),
        own_prefix + "interface-contract.json": snapshot_root / "interface-contract.json",
        own_prefix + "decision.schema.json": snapshot_root / "decision.schema.json",
    }
    records = binding.get("artifacts")
    if not isinstance(records, list):
        raise RuntimeError("source-binding artifacts are missing")
    seen: set[str] = set()
    for row in records:
        relative = str(row.get("path", ""))
        if relative not in expected_paths or relative in seen:
            raise RuntimeError(f"unexpected source-binding path: {relative}")
        path = expected_paths[relative]
        info = assert_regular(path)
        digest = sha256(path)
        if info.st_size != row.get("bytes") or digest != row.get("sha256"):
            raise RuntimeError(f"source-binding mismatch: {relative}")
        if relative in EXPECTED_HASHES and digest != EXPECTED_HASHES[relative]:
            raise RuntimeError(f"frozen dependency changed: {relative}")
        seen.add(relative)
    if seen != set(expected_paths):
        raise RuntimeError("source-binding file-set closure mismatch")
    return artifact(binding_path)


def referenced_artifact(result: dict[str, Any], identifier: str) -> dict[str, Any]:
    matches = [
        row
        for row in result.get("artifacts", [])
        if isinstance(row, dict) and row.get("id") == identifier
    ]
    if len(matches) != 1:
        raise RuntimeError(f"recovery result lacks one {identifier} artifact")
    return matches[0]


def verify_terminal_file(record: dict[str, Any], expected_path: Path) -> dict[str, Any]:
    path = PROJECT / str(record.get("path", ""))
    if path.resolve(strict=True) != expected_path.resolve(strict=True):
        raise RuntimeError(f"terminal artifact path mismatch: {expected_path}")
    info = assert_regular(path, one_link=True)
    digest = sha256(path)
    if (
        info.st_size != record.get("bytes")
        or digest != str(record.get("sha256", "")).removeprefix("sha256:")
        or info.st_dev != record.get("device")
        or info.st_ino != record.get("inode")
        or info.st_mtime_ns != record.get("mtimeNanoseconds")
        or info.st_ctime_ns != record.get("ctimeNanoseconds")
    ):
        raise RuntimeError(f"terminal artifact identity mismatch: {expected_path}")
    return {
        **artifact(path, digest),
        "device": info.st_dev,
        "inode": info.st_ino,
        "mtimeNanoseconds": info.st_mtime_ns,
        "ctimeNanoseconds": info.st_ctime_ns,
    }


def require_recovery_terminal() -> dict[str, Any]:
    active = active_adoption_jobs()
    if active:
        raise RuntimeError("orphan adoption remains nonterminal: " + ", ".join(active))
    assert_regular(ADOPTION_RESULT, one_link=True)
    assert_regular(ADOPTION_TERMINAL, one_link=True)
    result = load_json(ADOPTION_RESULT)
    terminal = load_json(ADOPTION_TERMINAL)
    if (
        result.get("schema") != "gamma.enwiki9.adaptive-experiment-result.v1"
        or result.get("candidateId") != ADOPTION_ID
        or result.get("evidenceClass") != "infrastructure"
        or result.get("objectiveCreditBytes") != 0
        or result.get("promotionPass") is not True
        or result.get("killPass") is not False
        or result.get("decision") != "authorize-successor"
        or result.get("measurements", {}).get("recoveryIntegrityPass") is not True
        or result.get("measurements", {}).get("terminalProcessAbsence") is not True
        or result.get("measurements", {}).get("continuousResourceProofPass") is not False
    ):
        raise RuntimeError("orphan-adoption result does not authorize analysis")
    terminal_ref = referenced_artifact(result, "terminal-source")
    if (
        terminal_ref.get("path")
        != ADOPTION_TERMINAL.relative_to(PROJECT).as_posix()
        or terminal_ref.get("bytes") != ADOPTION_TERMINAL.stat().st_size
        or str(terminal_ref.get("sha256", "")).removeprefix("sha256:")
        != sha256(ADOPTION_TERMINAL)
    ):
        raise RuntimeError("recovery result does not bind terminal-source bytes")
    if (
        terminal.get("schema")
        != "gamma.enwiki9.endpoint428-horizon-orphan-terminal-source.v1"
        or terminal.get("candidateId") != ADOPTION_ID
        or terminal.get("sourceCandidateId") != SOURCE_ID
        or terminal.get("status") != "SEALED_IMMUTABLE_TRACE"
        or terminal.get("scientificValuesAccessed") is not False
        or terminal.get("continuousResourceProofPass") is not False
        or terminal.get("analysisAuthority")
        != "one-separately-frozen-immutable-trace-analysis-only"
        or terminal.get("archiveAuthority") is not False
        or terminal.get("scoreCreditBytes") != 0
    ):
        raise RuntimeError("terminal recovery source is inadmissible")
    trace_path = PROJECT / "results" / SOURCE_ID / "parent.p1"
    archive_path = PROJECT / "results" / SOURCE_ID / "parent.archive"
    manifest_path = PROJECT / "results" / SOURCE_ID / "manifest-a.bin"
    trace = verify_terminal_file(terminal["trace"], trace_path)
    archive = verify_terminal_file(terminal["archive"], archive_path)
    if trace["bytes"] != TRACE_BYTES or archive["bytes"] <= 0:
        raise RuntimeError("recovered trace/archive geometry mismatch")
    with trace_path.open("rb") as stream:
        header = stream.read(16)
    if len(header) != 16 or header[:8] != TRACE_MAGIC or struct.unpack_from("<Q", header, 8)[0] != TRACE_ROWS:
        raise RuntimeError("recovered trace header mismatch")
    static_rows = [
        row
        for row in terminal.get("staticInputs", [])
        if row.get("path") == manifest_path.relative_to(PROJECT).as_posix()
    ]
    if len(static_rows) != 1:
        raise RuntimeError("recovery terminal lacks frozen manifest-a identity")
    manifest_info = assert_regular(manifest_path, one_link=True)
    manifest_hash = sha256(manifest_path)
    manifest_row = static_rows[0]
    if (
        manifest_info.st_size != MANIFEST_BYTES
        or manifest_info.st_size != manifest_row.get("bytes")
        or manifest_hash != str(manifest_row.get("sha256", "")).removeprefix("sha256:")
    ):
        raise RuntimeError("recovered manifest-a identity mismatch")
    return {
        "result": artifact(ADOPTION_RESULT),
        "terminal": artifact(ADOPTION_TERMINAL),
        "trace": trace,
        "archive": archive,
        "manifest": artifact(manifest_path, manifest_hash),
        "trace_path": trace_path,
        "archive_path": archive_path,
        "manifest_path": manifest_path,
    }


def identity(path: Path) -> dict[str, Any]:
    info = assert_regular(path, one_link=True)
    return {
        "bytes": info.st_size,
        "sha256": sha256(path),
        "device": info.st_dev,
        "inode": info.st_ino,
        "mtimeNanoseconds": info.st_mtime_ns,
        "ctimeNanoseconds": info.st_ctime_ns,
    }


def validate_legacy(value: dict[str, Any]) -> None:
    required = {
        "active_bytes",
        "parent_trace_rows",
        "parent_truth_bits",
        "parent_truth_bits_by_third",
        "arms",
        "minimum_third_mixture_gain_bits",
        "minimum_control_margin_bits",
        "gross_gate_bits",
        "coordinate_fnv1a64",
        "promotion_pass",
        "archive_authority",
        "score_credit_bytes",
    }
    if (
        value.get("schema") != "gamma.enwiki9.horizon-retained-parent-analysis.v1"
        or set(value) != required | {"schema"}
        or value.get("active_bytes") != ACTIVE_BYTES
        or value.get("parent_trace_rows") != TRACE_ROWS
        or value.get("gross_gate_bits") != GROSS_GATE_BITS
        or value.get("archive_authority") is not False
        or value.get("score_credit_bytes") != 0
        or set(value.get("arms", {})) != {"D", "S", "R", "N"}
    ):
        raise RuntimeError("legacy analyzer output contract mismatch")


def analysis_record(path: Path, values: dict[str, Any], phase: dict[str, Any]) -> dict[str, Any]:
    return {"artifact": artifact(path), "values": values, "phase": phase}


def output_manifest() -> dict[str, Any]:
    names = [
        "compile-exact-a.log",
        "compile-exact-b.log",
        "compile-legacy-a.log",
        "compile-legacy-b.log",
        "compile-fixture.log",
        "build.json",
        "arithmetic-vectors.tsv",
        "fixture-guard.json",
        "fixture.log",
        "fixture-reference-guard.json",
        "fixture-reference.log",
        "fixture-verification.json",
        "legacy-a-guard.json",
        "legacy-a.log",
        "legacy-a.json",
        "legacy-b-guard.json",
        "legacy-b.log",
        "legacy-b.json",
        "exact-a-guard.json",
        "exact-a.log",
        "exact-a.json",
        "exact-b-guard.json",
        "exact-b.log",
        "exact-b.json",
        "decision.json",
    ]
    observed = sorted(path.name for path in RESULT.iterdir())
    exact = observed == sorted(names) and all(
        path.is_file() and not path.is_symlink() for path in RESULT.iterdir()
    )
    artifacts: list[dict[str, Any]] = []
    for name in names:
        row = artifact(RESULT / name)
        row["path"] = name
        artifacts.append(row)
    return {
        "schema": "gamma.enwiki9.horizon-retained-recovered-exact-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "result_root": f"results/{CANDIDATE_ID}",
        "pre_manifest_exact_file_set_pass": exact,
        "complete_result_artifacts_pass": exact and len(artifacts) == len(names),
        "artifacts": artifacts,
    }


def main() -> int:
    recovery = require_recovery_terminal()
    snapshot_root, snapshot = bind_candidate_snapshot()
    source_binding = verify_source_binding(snapshot_root)
    decision_schema = snapshot_root / "decision.schema.json"
    if not RESULT.is_dir() or RESULT.is_symlink() or any(RESULT.iterdir()):
        raise RuntimeError(f"result directory must be precreated and empty: {RESULT}")
    before = {
        "trace": identity(recovery["trace_path"]),
        "archive": identity(recovery["archive_path"]),
        "manifest": identity(recovery["manifest_path"]),
    }

    with tempfile.TemporaryDirectory(prefix="gamma-horizon-recovered-exact-") as raw:
        build_root = Path(raw)
        binaries: dict[str, Path] = {}
        for family, source in (("legacy", LEGACY_ANALYZER), ("exact", EXACT_ANALYZER)):
            for repeat in ("a", "b"):
                binary = build_root / f"{family}-{repeat}"
                V2.run_logged(
                    [str(COMPILER), *V2.COMPILE_FLAGS, str(source), "-o", str(binary)],
                    RESULT / f"compile-{family}-{repeat}.log",
                )
                binaries[f"{family}-{repeat}"] = binary
        fixture_binary = build_root / "fixture"
        V2.run_logged(
            [str(COMPILER), *V2.COMPILE_FLAGS, str(EXACT_FIXTURE), "-o", str(fixture_binary)],
            RESULT / "compile-fixture.log",
        )
        deterministic_build_pass = (
            sha256(binaries["legacy-a"]) == sha256(binaries["legacy-b"])
            and sha256(binaries["exact-a"]) == sha256(binaries["exact-b"])
        )
        write_json_exclusive(
            RESULT / "build.json",
            {
                "schema": "gamma.enwiki9.horizon-retained-recovered-exact-build.v1",
                "candidate_id": CANDIDATE_ID,
                "flags": V2.COMPILE_FLAGS,
                "compiler": artifact(COMPILER),
                "legacy_a": artifact(binaries["legacy-a"]),
                "legacy_b": artifact(binaries["legacy-b"]),
                "exact_a": artifact(binaries["exact-a"]),
                "exact_b": artifact(binaries["exact-b"]),
                "fixture": artifact(fixture_binary),
                "deterministic_build_pass": deterministic_build_pass,
                "archive_authority": False,
                "score_credit_bytes": 0,
            },
        )
        if not deterministic_build_pass:
            raise RuntimeError("independent analyzer builds differ")

        vectors = RESULT / "arithmetic-vectors.tsv"
        fixture_phase = V2.run_guarded(
            "fixture", [str(fixture_binary), str(vectors)], 131_072
        )
        fixture_receipt_path = RESULT / "fixture-verification.json"
        fixture_reference_phase = V2.run_guarded(
            "fixture-reference",
            [
                sys.executable,
                str(EXACT_REFERENCE),
                "--native",
                str(vectors),
                "--receipt",
                str(fixture_receipt_path),
            ],
            131_072,
        )
        fixture_receipt = load_json(fixture_receipt_path)
        jsonschema.Draft202012Validator(load_json(FIXTURE_SCHEMA)).validate(fixture_receipt)
        if fixture_receipt.get("terminal_pass") is not True:
            raise RuntimeError("exact arithmetic fixture failed")

        legacy: dict[str, dict[str, Any]] = {}
        exact: dict[str, dict[str, Any]] = {}
        all_phases: list[dict[str, Any]] = [fixture_phase, fixture_reference_phase]
        for family, collection in (("legacy", legacy), ("exact", exact)):
            for repeat in ("a", "b"):
                output = RESULT / f"{family}-{repeat}.json"
                phase = V2.run_guarded(
                    f"{family}-{repeat}",
                    [
                        str(binaries[f"{family}-{repeat}"]),
                        str(recovery["trace_path"]),
                        str(recovery["manifest_path"]),
                        str(output),
                    ],
                    TREE_LIMIT_KIB,
                )
                values = load_json(output)
                if family == "legacy":
                    validate_legacy(values)
                else:
                    jsonschema.Draft202012Validator(load_json(EXACT_SCHEMA)).validate(values)
                collection[repeat] = analysis_record(output, values, phase)
                all_phases.append(phase)

    legacy_ab = legacy["a"]["values"] == legacy["b"]["values"]
    exact_ab = exact["a"]["values"] == exact["b"]["values"]
    if not legacy_ab or not exact_ab:
        raise RuntimeError("analysis A/B identity failed")
    V2.compare_legacy(exact["a"]["values"], legacy["a"]["values"])
    legacy_crosscheck = True
    after = {
        "trace": identity(recovery["trace_path"]),
        "archive": identity(recovery["archive_path"]),
        "manifest": identity(recovery["manifest_path"]),
    }
    immutable_identity = before == after
    values = exact["a"]["values"]
    treatment_gain = float(values["arms"]["D"]["mixture_gain_bits"])
    minimum_third = float(values["minimum_third_mixture_gain_bits"])
    minimum_control = float(values["minimum_control_margin_bits"])
    analysis_resources = all(
        phase["receipt"].get("status") == "complete"
        and phase["receipt"].get("returncode") == 0
        and phase["receipt"].get("rss_guard_exceeded") is False
        and phase["receipt"].get("logical_cpu_guard_exceeded") is False
        for phase in all_phases
    )
    gates = {
        "recoveryIntegrityPass": True,
        "immutableIdentityPass": immutable_identity,
        "deterministicBuildPass": deterministic_build_pass,
        "completeActivePopulationPass": values["active_bytes"] == ACTIVE_BYTES,
        "completeParentTracePass": values["parent_trace_rows"] == TRACE_ROWS,
        "targetBearingMixturePass": treatment_gain >= GROSS_GATE_BITS,
        "everyThirdPositivePass": minimum_third > 0.0,
        "controlsSeparatedPass": minimum_control > 0.0,
        "legacyABPass": legacy_ab,
        "exactABPass": exact_ab,
        "legacyCrosscheckPass": legacy_crosscheck,
        "arbitraryPrecisionFixturePass": fixture_receipt["terminal_pass"] is True,
        "analysisResourcePass": analysis_resources,
        "continuousResourceProofPass": False,
    }
    scientific_pass = all(
        value for key, value in gates.items() if key != "continuousResourceProofPass"
    )
    decision = {
        "schema": "gamma.enwiki9.endpoint428-horizon-retained-recovered-exact-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal",
        "evidence_class": "causal-shadow",
        "claim_boundary": (
            "Exact integer reanalysis of a prospectively sealed orphan trace. "
            "The permanently missing parent-run resource interval remains false; "
            "this proves no native archive, inverse, package score, or Hutter result."
        ),
        "inputs": {
            "candidate_snapshot": snapshot,
            "plan": artifact(PLAN),
            "experiment": artifact(EXPERIMENT),
            "source_binding": source_binding,
            "recovery_result": recovery["result"],
            "recovery_terminal": recovery["terminal"],
            "parent_trace": recovery["trace"],
            "parent_archive": recovery["archive"],
            "manifest_a": recovery["manifest"],
            "identity_before": before,
            "identity_after": after,
        },
        "fixture": {
            "receipt": artifact(RESULT / "fixture-verification.json"),
            "values": fixture_receipt,
            "native_phase": fixture_phase,
            "reference_phase": fixture_reference_phase,
        },
        "legacy_analyses": legacy,
        "exact_analyses": exact,
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
        "continuous_resource_proof_pass": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "verified_full_1g_score_bytes": None,
    }
    jsonschema.Draft202012Validator(load_json(decision_schema)).validate(decision)
    write_json_exclusive(RESULT / "decision.json", decision)
    manifest = output_manifest()
    if manifest["complete_result_artifacts_pass"] is not True:
        raise RuntimeError("complete result artifact closure failed")
    write_json_exclusive(RESULT / "output-manifest.json", manifest)
    print(
        json.dumps(
            {
                "candidate_id": CANDIDATE_ID,
                "treatment_mixture_gain_bits": treatment_gain,
                "verdict": decision["verdict"],
                "continuous_resource_proof_pass": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
