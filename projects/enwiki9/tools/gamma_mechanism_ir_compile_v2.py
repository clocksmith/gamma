#!/usr/bin/env python3
"""Compile Mechanism IR through a verified causal closure into exact arm contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


OUTPUT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-compilation-receipt.v2"
ARM_FILES = {
    "P": "P_control.json",
    "K": "K_control.json",
    "D": "D_raw_treatment.json",
    "M": "M_mixed_treatment.json",
    "R": "R_control.json",
    "S": "S_control.json",
}


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path, display: str | None = None) -> dict[str, Any]:
    return {
        "path": display if display is not None else os.fspath(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def regular_file(path: Path, label: str) -> Path:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise SystemExit(f"{label}: symlink component forbidden: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise SystemExit(f"{label}: expected single-link regular file")
    return absolute.resolve(strict=True)


def require_parent(path: Path, label: str) -> None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parent.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise SystemExit(f"{label}: unsafe parent component {current}")


def require_lease_clear(path: Path) -> None:
    lease_path = regular_file(path, "exclusive lease")
    try:
        lease = json.loads(lease_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"exclusive lease parse failure: {exc}") from exc
    if not isinstance(lease, dict):
        raise SystemExit("exclusive lease must be a JSON object")
    if lease.get("active") is not False:
        raise SystemExit("exclusive lease is active or lacks an explicit inactive decision")


def artifact_set_sha256(artifacts: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for artifact in sorted(artifacts, key=lambda item: item["path"]):
        digest.update(artifact["path"].encode("ascii"))
        digest.update(b"\0")
        digest.update(str(artifact["bytes"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(artifact["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def union_access(arm: dict[str, Any], field: str) -> list[str]:
    values: set[str] = set()
    accesses = arm.get("event_access")
    if not isinstance(accesses, list):
        raise SystemExit(f"arm {arm.get('arm')} lacks event_access")
    for access in accesses:
        if not isinstance(access, dict) or not isinstance(access.get(field), list):
            raise SystemExit(f"arm {arm.get('arm')} has malformed {field}")
        for value in access[field]:
            if not isinstance(value, str) or not value:
                raise SystemExit(f"arm {arm.get('arm')} has invalid {field} value")
            values.add(value)
    return sorted(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ir", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    require_lease_clear(args.exclusive_lease)
    ir_path = regular_file(args.ir, "IR")
    closure_path = regular_file(args.closure, "causal closure")
    compiler_v2 = regular_file(Path(__file__), "compiler v2")
    compiler_v1 = regular_file(Path(__file__).with_name("gamma_mechanism_ir_compile.py"), "compiler v1")
    closure_verifier = regular_file(Path(__file__).with_name("gamma_mechanism_causal_closure_verify.py"), "closure verifier")
    for path, label in ((args.evidence_dir, "evidence directory"), (args.output_dir, "output directory")):
        require_parent(path, label)
        if path.exists() or path.is_symlink():
            raise SystemExit(f"{label} must not already exist")
    require_parent(args.receipt, "receipt")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt must not already exist")

    ir_raw = ir_path.read_bytes()
    closure_raw = closure_path.read_bytes()
    try:
        ir = json.loads(ir_raw.decode("utf-8"))
        closure = json.loads(closure_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"input JSON parse failure: {exc}") from exc
    if not isinstance(ir, dict) or not isinstance(closure, dict):
        raise SystemExit("IR and closure must be JSON objects")
    mechanism_id = ir.get("mechanism_id")
    if not isinstance(mechanism_id, str) or closure.get("mechanism_id") != mechanism_id:
        raise SystemExit("IR and closure mechanism identities differ")

    args.evidence_dir.mkdir()
    closure_receipt = args.evidence_dir / "causal-closure-verification.json"
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
    }
    closure_run = subprocess.run(
        [
            sys.executable,
            os.fspath(closure_verifier),
            "--ir",
            os.fspath(ir_path),
            "--closure",
            os.fspath(closure_path),
            "--receipt",
            os.fspath(closure_receipt),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    (args.evidence_dir / "closure-verifier.stdout.bin").write_bytes(closure_run.stdout)
    (args.evidence_dir / "closure-verifier.stderr.bin").write_bytes(closure_run.stderr)
    if closure_run.returncode != 0 or not closure_receipt.is_file():
        raise SystemExit("causal closure verification failed")
    closure_decision = json.loads(closure_receipt.read_text(encoding="utf-8"))
    if (
        not isinstance(closure_decision, dict)
        or closure_decision.get("verified") is not True
        or closure_decision.get("mechanism_ir_sha256") != sha256_bytes(ir_raw)
        or closure_decision.get("closure_sha256") != sha256_bytes(closure_raw)
    ):
        raise SystemExit("causal closure receipt does not bind the supplied inputs")

    legacy_root = args.evidence_dir / "legacy"
    legacy_root.mkdir()
    legacy_artifacts = legacy_root / "artifacts"
    legacy_receipt = legacy_root / "receipt.json"
    legacy_run = subprocess.run(
        [
            sys.executable,
            os.fspath(compiler_v1),
            "--ir",
            os.fspath(ir_path),
            "--output-dir",
            os.fspath(legacy_artifacts),
            "--receipt",
            os.fspath(legacy_receipt),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    (legacy_root / "stdout.bin").write_bytes(legacy_run.stdout)
    (legacy_root / "stderr.bin").write_bytes(legacy_run.stderr)
    if legacy_run.returncode != 0 or not legacy_receipt.is_file() or not legacy_artifacts.is_dir():
        raise SystemExit("preserved compiler v1 failed")

    arms_raw = closure.get("arms")
    if not isinstance(arms_raw, list):
        raise SystemExit("closure arms must be an array")
    arms: dict[str, dict[str, Any]] = {}
    for arm in arms_raw:
        if not isinstance(arm, dict) or not isinstance(arm.get("arm"), str) or arm["arm"] in arms:
            raise SystemExit("closure contains malformed or duplicate arms")
        arms[arm["arm"]] = arm
    if set(arms) != set(ARM_FILES):
        raise SystemExit("closure must contain exactly P/K/D/M/R/S")
    ir_writes = ir.get("state_writes")
    if not isinstance(ir_writes, list):
        raise SystemExit("IR state_writes must be an array")
    writes_by_id: dict[str, dict[str, Any]] = {}
    for value in ir_writes:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str) or value["id"] in writes_by_id:
            raise SystemExit("IR contains malformed or duplicate state writes")
        writes_by_id[value["id"]] = value

    transformed: dict[str, bytes] = {}
    for legacy_path in sorted(legacy_artifacts.iterdir(), key=lambda path: path.name):
        if not legacy_path.is_file() or legacy_path.is_symlink() or legacy_path.stat().st_nlink != 1:
            raise SystemExit(f"legacy artifact is not a single-link regular file: {legacy_path.name}")
        transformed[legacy_path.name] = legacy_path.read_bytes()
    for arm_id, filename in ARM_FILES.items():
        if filename not in transformed:
            raise SystemExit(f"legacy compiler omitted {filename}")
        document = json.loads(transformed[filename].decode("ascii"))
        read_ids = union_access(arms[arm_id], "read_state_ids")
        write_ids = union_access(arms[arm_id], "write_state_ids")
        if not set(write_ids) <= set(writes_by_id):
            raise SystemExit(f"arm {arm_id} closure references unknown writes")
        document["state_read_ids"] = read_ids
        document["state_writes"] = [writes_by_id[state_id] for state_id in write_ids]
        document["causal_closure"] = {
            "sha256": sha256_bytes(closure_raw),
            "event_access": arms[arm_id]["event_access"],
        }
        transformed[filename] = json_bytes(document)

    arm_access = {
        arm_id: {
            "read_state_ids": union_access(arms[arm_id], "read_state_ids"),
            "write_state_ids": union_access(arms[arm_id], "write_state_ids"),
        }
        for arm_id in sorted(arms)
    }
    transformed["arm_difference_manifest.json"] = json_bytes({
        "schema": "gamma.enwiki9.generated-arm-difference-manifest.v2",
        "mechanism_id": mechanism_id,
        "causal_closure_sha256": sha256_bytes(closure_raw),
        "arm_access": arm_access,
        "matched_access_group": ["K", "M", "R", "S"],
        "raw_treatment_posterior_policy": "D must not write mechanism-persistent mixture state",
    })
    state_access = json.loads(transformed["state_access_manifest.json"].decode("ascii"))
    state_access["causal_closure_sha256"] = sha256_bytes(closure_raw)
    state_access["per_arm"] = arm_access
    transformed["state_access_manifest.json"] = json_bytes(state_access)

    matched = [arm_access[arm_id] for arm_id in ("K", "M", "R", "S")]
    if any(value != matched[0] for value in matched[1:]):
        raise SystemExit("K/M/R/S access sets differ after closure compilation")
    role_values = closure.get("state_roles")
    if not isinstance(role_values, list):
        raise SystemExit("closure state_roles must be an array")
    posterior_ids = {
        value["state_id"]
        for value in role_values
        if isinstance(value, dict)
        and value.get("authority") == "mechanism_persistent"
        and isinstance(value.get("state_id"), str)
    }
    if posterior_ids & set(arm_access["D"]["write_state_ids"]):
        raise SystemExit("raw D writes a persistent mixture state")
    if not posterior_ids <= set(arm_access["M"]["write_state_ids"]):
        raise SystemExit("mixed M omits a persistent mixture-state write")

    args.output_dir.mkdir()
    artifacts: list[dict[str, Any]] = []
    for relative, content in sorted(transformed.items()):
        second = json_bytes(json.loads(content.decode("ascii"))) if relative.endswith(".json") else bytes(bytearray(content))
        if second != content:
            raise SystemExit(f"noncanonical transformed artifact {relative}")
        output_path = args.output_dir / relative
        with output_path.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        artifacts.append({"path": relative, "bytes": len(content), "sha256": sha256_bytes(content)})

    receipt = {
        "schema": OUTPUT_SCHEMA,
        "mechanism_id": mechanism_id,
        "operational_status": "compiled_non_authoritative",
        "source_ir": {"path": os.fspath(args.ir), "bytes": len(ir_raw), "sha256": sha256_bytes(ir_raw)},
        "causal_closure": {"path": os.fspath(args.closure), "bytes": len(closure_raw), "sha256": sha256_bytes(closure_raw)},
        "tools": {
            "compiler_v2": file_identity(compiler_v2),
            "compiler_v1": file_identity(compiler_v1),
            "closure_verifier": file_identity(closure_verifier),
        },
        "legacy_compilation": {
            "return_code": legacy_run.returncode,
            "stdout_sha256": sha256_bytes(legacy_run.stdout),
            "stderr_sha256": sha256_bytes(legacy_run.stderr),
            "receipt_sha256": sha256_file(legacy_receipt),
        },
        "artifacts": artifacts,
        "artifact_set_sha256": artifact_set_sha256(artifacts),
        "validation": {
            "closure_verification_pass": True,
            "mechanism_identity_pass": True,
            "arm_set_pass": True,
            "per_arm_access_rewrite_pass": True,
            "matched_control_access_pass": True,
            "raw_treatment_posterior_isolation_pass": True,
            "mixed_treatment_posterior_write_pass": True,
            "artifact_closure_pass": True,
            "canonical_render_pass": True,
        },
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    with args.receipt.open("xb") as stream:
        stream.write(json_bytes(receipt))
        stream.flush()
        os.fsync(stream.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
