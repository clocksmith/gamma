#!/usr/bin/env python3
"""Seal official Hutter score and Gamma expanded-closure package accounting."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA = "gamma.enwiki9.submission-package-manifest.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.submission-package-receipt.v1"
EVIDENCE_KINDS = {
    "build",
    "inverse",
    "determinism",
    "resource",
    "dependency",
    "license",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def reject_symlink_components(path: Path) -> None:
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"symlink path components are forbidden: {path}")


def resolve_file(raw: str) -> Path:
    path = Path(raw)
    if ".." in path.parts:
        raise ValueError(f"parent traversal is forbidden: {raw}")
    candidate = path if path.is_absolute() else ROOT / path
    reject_symlink_components(candidate)
    resolved = candidate.resolve(strict=True)
    if not path.is_absolute():
        try:
            resolved.relative_to(ROOT.resolve(strict=True))
        except ValueError as error:
            raise ValueError(f"relative artifact escapes project root: {raw}") from error
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def verify_resource_guard_v3(value: dict[str, Any]) -> tuple[bool, str]:
    if value.get("schema") != "gamma.enwiki9.resource-guard-receipt.v3":
        return False, "resource evidence is not a resource-guard v3 receipt"
    measurements = value.get("measurements")
    guards = value.get("guards")
    cgroup = value.get("cgroup")
    passed = (
        value.get("status") == "complete"
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
    return passed, "verified resource-guard v3 terminal pass" if passed else "resource-guard v3 terminal fields do not pass"


def verify_evidence(kind: str, path: Path) -> tuple[bool, str, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return False, f"evidence is not readable canonical JSON: {type(error).__name__}", None
    if not isinstance(value, dict):
        return False, "evidence root is not an object", None
    schema = value.get("schema") if isinstance(value.get("schema"), str) else None
    if kind == "resource":
        passed, reason = verify_resource_guard_v3(value)
        return passed, reason, schema
    return False, f"no schema-specific verifier is registered for evidence kind {kind}", schema


def load_object(path: Path, schema: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError(f"expected {schema}: {path}")
    return value


def artifact(entry: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    path = resolve_file(entry["path"])
    observed = {
        "id": entry["id"],
        "path": str(path),
        "roles": entry["roles"],
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "officialMultiplier": entry["officialMultiplier"],
        "gammaMultiplier": entry["gammaMultiplier"],
        "runtimeRequired": entry["runtimeRequired"],
    }
    if entry["expectedBytes"] is not None and entry["expectedBytes"] != observed["bytes"]:
        raise ValueError(f"byte identity mismatch: {entry['id']}")
    if (
        entry["expectedSha256"] is not None
        and entry["expectedSha256"] != observed["sha256"]
    ):
        raise ValueError(f"SHA-256 identity mismatch: {entry['id']}")
    if entry["runtimeRequired"] and entry["officialMultiplier"] == 0:
        raise ValueError(
            f"runtime-required physical artifact is omitted from official score: {entry['id']}"
        )
    return observed, path


def hash_slice(path: Path, offset: int, length: int) -> str:
    value = hashlib.sha256()
    remaining = length
    with path.open("rb") as stream:
        stream.seek(offset)
        while remaining:
            block = stream.read(min(1 << 20, remaining))
            if not block:
                raise ValueError(f"truncated embedded component in {path}")
            value.update(block)
            remaining -= len(block)
    return value.hexdigest()


def validate_formula(
    formula: str,
    artifacts: list[dict[str, Any]],
) -> None:
    role_to_artifacts: dict[str, list[dict[str, Any]]] = {}
    for item in artifacts:
        for role in item["roles"]:
            role_to_artifacts.setdefault(role, []).append(item)

    compressors = role_to_artifacts.get("compressor", []) + role_to_artifacts.get(
        "source_package", []
    )
    archives = role_to_artifacts.get("self_extracting_archive", [])
    payloads = role_to_artifacts.get("compressed_payload", [])
    decompressors = role_to_artifacts.get("decompressor", [])

    if not compressors:
        raise ValueError("selected formula has no compressor or source package")
    if formula == "official_primary":
        if not archives:
            raise ValueError("primary formula requires a self-extracting archive")
        if any(item["officialMultiplier"] < 1 for item in compressors + archives):
            raise ValueError("primary compressor and archive must each be counted")
    elif formula == "official_separate_archive":
        if not payloads or not decompressors:
            raise ValueError(
                "separate formula requires compressed payload and decompressor"
            )
        if any(item["officialMultiplier"] < 1 for item in compressors + payloads):
            raise ValueError("separate compressor and payload must each be counted")
        for item in decompressors:
            shared = "compressor" in item["roles"] or "source_package" in item["roles"]
            minimum = 1 if shared else 2
            if item["officialMultiplier"] < minimum:
                raise ValueError(
                    f"decompressor multiplier undercounts formula: {item['id']}"
                )
    else:
        raise ValueError(f"unknown score formula: {formula}")


def build_receipt(manifest_path: Path) -> dict[str, Any]:
    manifest = load_object(manifest_path, MANIFEST_SCHEMA)
    physical_entries = manifest["physicalArtifacts"]
    ids = [entry["id"] for entry in physical_entries]
    paths = [str(resolve_file(entry["path"])) for entry in physical_entries]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate physical artifact id")
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate physical artifact path")

    observed: list[dict[str, Any]] = []
    observed_paths: dict[str, Path] = {}
    for entry in physical_entries:
        item, path = artifact(entry)
        observed.append(item)
        observed_paths[item["id"]] = path

    validate_formula(manifest["selectedFormula"], observed)

    component_ids: set[str] = set()
    components: list[dict[str, Any]] = []
    for entry in manifest["embeddedComponents"]:
        if entry["id"] in component_ids:
            raise ValueError(f"duplicate embedded component id: {entry['id']}")
        component_ids.add(entry["id"])
        container = observed_paths.get(entry["containerArtifactId"])
        if container is None:
            raise ValueError(
                f"unknown embedded container: {entry['containerArtifactId']}"
            )
        offset = entry["offset"]
        length = entry["length"]
        if offset + length > container.stat().st_size:
            raise ValueError(f"embedded range escapes container: {entry['id']}")
        observed_sha = hash_slice(container, offset, length)
        if observed_sha != entry["sha256"]:
            raise ValueError(f"embedded component hash mismatch: {entry['id']}")
        components.append(
            {
                **entry,
                "observedSha256": observed_sha,
                "countedSeparately": False,
            }
        )

    text_ids: set[str] = set()
    texts: list[dict[str, Any]] = []
    for entry in manifest["countedText"]:
        if entry["id"] in text_ids:
            raise ValueError(f"duplicate counted text id: {entry['id']}")
        text_ids.add(entry["id"])
        try:
            encoded = entry["text"].encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError(f"counted text must be ASCII: {entry['id']}") from error
        texts.append({**entry, "bytes": len(encoded)})

    evidence_ids: set[str] = set()
    evidence: list[dict[str, Any]] = []
    terminal_kinds: set[str] = set()
    failed_evidence: list[str] = []
    for entry in manifest["evidence"]:
        if entry["id"] in evidence_ids:
            raise ValueError(f"duplicate evidence id: {entry['id']}")
        evidence_ids.add(entry["id"])
        path = resolve_file(entry["path"])
        observed_sha = sha256(path)
        if observed_sha != entry["sha256"]:
            raise ValueError(f"evidence hash mismatch: {entry['id']}")
        verifier_pass, verification_reason, observed_schema = verify_evidence(
            entry["kind"], path
        )
        verified_terminal_pass = entry["terminalPass"] is True and verifier_pass
        evidence.append(
            {
                **entry,
                "path": str(path),
                "observedSha256": observed_sha,
                "declaredTerminalPass": entry["terminalPass"],
                "verifiedTerminalPass": verified_terminal_pass,
                "observedSchema": observed_schema,
                "verificationReason": verification_reason,
            }
        )
        if verified_terminal_pass:
            terminal_kinds.add(entry["kind"])
        elif entry["terminalPass"]:
            failed_evidence.append(
                f"evidence {entry['id']} is not independently verified: {verification_reason}"
            )

    official_physical = sum(
        item["bytes"] * item["officialMultiplier"] for item in observed
    )
    gamma_physical = sum(
        item["bytes"] * item["gammaMultiplier"] for item in observed
    )
    official_text = sum(
        item["bytes"] for item in texts if item["officialCounted"]
    )
    gamma_text = sum(item["bytes"] for item in texts if item["gammaCounted"])
    official_total = official_physical + official_text
    gamma_total = gamma_physical + gamma_text

    thresholds = manifest["thresholds"]
    missing_evidence = sorted(EVIDENCE_KINDS - terminal_kinds)
    reasons = [
        f"terminal {kind} evidence is absent" for kind in missing_evidence
    ]
    reasons.extend(failed_evidence)
    record_improving = official_total < thresholds["previousRecordBytes"]
    minimum_award = official_total <= thresholds["minimumAwardMaximumBytes"]
    gamma_target = gamma_total <= thresholds["gammaTargetBytes"]
    if not record_improving:
        reasons.append("official total does not improve the published record")
    if not minimum_award:
        reasons.append("official total does not meet the minimum-award size threshold")
    if not gamma_target:
        reasons.append("Gamma expanded closure exceeds the 105M objective")

    submission_authority = not missing_evidence and minimum_award
    gamma_authority = submission_authority and gamma_target

    return {
        "schema": RECEIPT_SCHEMA,
        "packageId": manifest["packageId"],
        "selectedFormula": manifest["selectedFormula"],
        "manifest": {
          "path": str(manifest_path),
          "bytes": manifest_path.stat().st_size,
          "sha256": sha256(manifest_path)
        },
        "physicalArtifacts": observed,
        "embeddedComponents": components,
        "countedText": texts,
        "scores": {
            "officialPhysicalBytes": official_physical,
            "officialCountedTextBytes": official_text,
            "officialTotalBytes": official_total,
            "gammaPhysicalClosureBytes": gamma_physical,
            "gammaCountedTextBytes": gamma_text,
            "gammaExpandedClosureBytes": gamma_total,
            "recordImprovingBySize": record_improving,
            "minimumAwardEligibleBySize": minimum_award,
            "gammaTargetMetBySize": gamma_target,
        },
        "evidence": evidence,
        "authority": {
            "artifactIdentityPass": True,
            "embeddedInventoryPass": True,
            "formulaShapePass": True,
            "requiredEvidenceKinds": sorted(EVIDENCE_KINDS),
            "terminalEvidenceKinds": sorted(terminal_kinds),
            "submissionAuthority": submission_authority,
            "gammaCompletionAuthority": gamma_authority,
            "reasons": reasons,
        },
        "generatedUtc": utc_now(),
    }


def canonical_without_time(value: dict[str, Any]) -> bytes:
    normalized = dict(value)
    normalized.pop("generatedUtc", None)
    return (
        json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def command_seal(args: argparse.Namespace) -> int:
    manifest = args.manifest.resolve()
    receipt = build_receipt(manifest)
    if args.output is None:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        write_new(args.output.resolve(), receipt)
    return 0


def command_verify(args: argparse.Namespace) -> int:
    observed = load_object(args.receipt.resolve(), RECEIPT_SCHEMA)
    manifest = Path(observed["manifest"]["path"]).resolve()
    expected = build_receipt(manifest)
    if canonical_without_time(observed) != canonical_without_time(expected):
        raise ValueError("package receipt differs from current declared artifacts")
    print("submission package receipt verified")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seal = subparsers.add_parser("seal")
    seal.add_argument("--manifest", type=Path, required=True)
    seal.add_argument("--output", type=Path)
    seal.set_defaults(handler=command_seal)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--receipt", type=Path, required=True)
    verify.set_defaults(handler=command_verify)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
