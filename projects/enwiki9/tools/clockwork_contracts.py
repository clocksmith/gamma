#!/usr/bin/env python3
"""Validate and digest the public Clockwork contract set."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "clockwork" / "v1"
CONTRACT_SET_PATH = CONTRACT_ROOT / "contract-set.json"


def canonical_bytes(value: Any) -> bytes:
    """Return the frozen Clockwork canonical JSON profile."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def artifact_digest(value: dict[str, Any], digest_field: str) -> str:
    unsigned = dict(value)
    unsigned.pop(digest_field, None)
    return sha256_digest(canonical_bytes(unsigned))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_contract_set() -> dict[str, Any]:
    contract_set = load_json(CONTRACT_SET_PATH)
    schema = load_json(CONTRACT_ROOT / "contract-set.schema.json")
    jsonschema.Draft202012Validator(schema).validate(contract_set)
    return contract_set


def verify_contract_set() -> dict[str, Any]:
    contract_set = load_contract_set()
    verified = []
    for entry in contract_set["schemas"]:
        path = CONTRACT_ROOT / entry["name"]
        schema = load_json(path)
        actual = sha256_digest(canonical_bytes(schema))
        if actual != entry["digest"]:
            raise ValueError(
                f"{entry['name']} digest mismatch: expected {entry['digest']}, got {actual}"
            )
        if schema.get("$id") != entry["schemaId"]:
            raise ValueError(f"{entry['name']} schemaId does not match $id")
        jsonschema.Draft202012Validator.check_schema(schema)
        verified.append({"name": entry["name"], "digest": actual})

    actual_set_digest = artifact_digest(contract_set, "contractSetDigest")
    if actual_set_digest != contract_set["contractSetDigest"]:
        raise ValueError(
            "contractSetDigest mismatch: "
            f"expected {contract_set['contractSetDigest']}, got {actual_set_digest}"
        )
    return {
        "schema": "clockwork.contract_set_verification.v1",
        "contractSetDigest": actual_set_digest,
        "verifiedSchemas": verified,
    }


def validate_artifact(path: Path) -> dict[str, Any]:
    artifact = load_json(path)
    schema_name = {
        "clockwork.route_binding.v1": "route-binding.schema.json",
        "clockwork.proof_receipt.v1": "proof-receipt.schema.json",
        "clockwork.challenge.v1": "challenge.schema.json",
        "clockwork.candidate.v1": "candidate.schema.json",
        "clockwork.search_receipt.v1": "search-receipt.schema.json",
        "gamma.candidate_receipt.v1": "gamma-candidate-receipt.schema.json",
    }.get(artifact.get("schema"))
    if not schema_name:
        raise ValueError(f"unsupported Clockwork schema: {artifact.get('schema')!r}")
    verify_contract_set()
    schema = load_json(CONTRACT_ROOT / schema_name)
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(artifact)
    contract_set = load_contract_set()
    if (
        "contractSetDigest" in artifact
        and artifact["contractSetDigest"] != contract_set["contractSetDigest"]
    ):
        raise ValueError("artifact contractSetDigest does not match canonical contract set")
    if artifact["schema"] == "clockwork.candidate.v1":
        genome_bytes = base64.b64decode(
            artifact["canonicalGenomeBase64"],
            validate=True,
        )
        if genome_bytes != canonical_bytes(artifact["genome"]):
            raise ValueError("canonicalGenomeBase64 does not encode canonical genome")
        if sha256_digest(genome_bytes) != artifact["candidateDigest"]:
            raise ValueError("candidateDigest does not bind canonical genome bytes")
    digest_fields = {
        "clockwork.route_binding.v1": "artifactDigest",
        "clockwork.proof_receipt.v1": "receiptDigest",
        "clockwork.challenge.v1": "challengeDigest",
        "clockwork.search_receipt.v1": "receiptDigest",
        "gamma.candidate_receipt.v1": "receiptDigest",
    }
    digest_field = digest_fields.get(artifact["schema"])
    if digest_field and artifact_digest(artifact, digest_field) != artifact[digest_field]:
        raise ValueError(f"{digest_field} does not bind canonical artifact bytes")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", nargs="?", type=Path)
    args = parser.parse_args()
    result = validate_artifact(args.artifact) if args.artifact else verify_contract_set()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
