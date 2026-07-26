from __future__ import annotations

import base64
import copy
import importlib.util
import sys
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "projects" / "enwiki9" / "tools" / "clockwork_contracts.py"
SPEC = importlib.util.spec_from_file_location("clockwork_contracts", MODULE_PATH)
assert SPEC and SPEC.loader
contracts = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contracts
SPEC.loader.exec_module(contracts)

DIGEST = "sha256:" + ("a" * 64)
CONTRACT_SET_DIGEST = "sha256:d97c9fc90434bfddb1168d1013ae071af1b995abbdcefa3b4113af811b152384"


def candidate() -> dict:
    genome = {"fallback": "identity", "correction": 0}
    genome_bytes = contracts.canonical_bytes(genome)
    return {
        "schema": "clockwork.candidate.v1",
        "contractSetDigest": CONTRACT_SET_DIGEST,
        "challengeDigest": DIGEST,
        "candidateKind": "residual-expert",
        "canonicalGenomeBase64": base64.b64encode(genome_bytes).decode("ascii"),
        "candidateDigest": contracts.sha256_digest(genome_bytes),
        "genome": genome,
        "genomeSchemaDigest": DIGEST,
        "parentCandidateDigests": [],
        "lineage": {
            "system": "reploid",
            "shadowId": "shadow-1",
            "evidenceDigests": [],
        },
        "resourceDeclaration": {"stateBytes": 0, "tableBytes": 0},
        "traceClosureDeclaration": {
            "closed": True,
            "consumedFeatures": ["baseline_probability"],
            "mutatesUpstream": False,
        },
        "literalIdentityFallback": True,
        "createdBy": {"tool": "test", "version": "1"},
    }


def test_contract_set_is_digest_bound_and_well_formed() -> None:
    result = contracts.verify_contract_set()
    assert result["contractSetDigest"] == CONTRACT_SET_DIGEST
    assert len(result["verifiedSchemas"]) == 6


def test_canonical_json_is_order_independent_and_rejects_nan() -> None:
    assert contracts.canonical_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    with pytest.raises(ValueError):
        contracts.canonical_bytes({"bad": float("nan")})


def test_candidate_schema_accepts_trace_closed_identity_fixture() -> None:
    schema = contracts.load_json(contracts.CONTRACT_ROOT / "candidate.schema.json")
    jsonschema.Draft202012Validator(schema).validate(candidate())


def test_candidate_schema_rejects_upstream_mutation() -> None:
    value = candidate()
    value["traceClosureDeclaration"]["mutatesUpstream"] = True
    schema = contracts.load_json(contracts.CONTRACT_ROOT / "candidate.schema.json")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(value)


def test_candidate_identity_detects_tampered_canonical_bytes() -> None:
    value = candidate()
    tampered = copy.deepcopy(value)
    tampered["canonicalGenomeBase64"] = base64.b64encode(b'{"correction":1}').decode("ascii")
    actual = contracts.sha256_digest(base64.b64decode(tampered["canonicalGenomeBase64"]))
    assert actual != tampered["candidateDigest"]


def test_candidate_semantic_validation_binds_genome_bytes(tmp_path: Path) -> None:
    path = tmp_path / "candidate.json"
    path.write_bytes(contracts.canonical_bytes(candidate()))
    contracts.validate_artifact(path)
    value = candidate()
    value["genome"]["correction"] = 1
    path.write_bytes(contracts.canonical_bytes(value))
    with pytest.raises(ValueError, match="canonicalGenomeBase64"):
        contracts.validate_artifact(path)


def test_route_binding_schema_forbids_private_certificate_material() -> None:
    value = {
        "schema": "clockwork.route_binding.v1",
        "routeBindingId": "route-c",
        "disposition": "draft",
        "sealVersion": "ACS-MATH-SEAL-2",
        "theoremStatementDigest": DIGEST,
        "hypothesisIds": ["C1"],
        "conclusionIds": ["C4"],
        "applicationCertificateDigest": DIGEST,
        "extractor": {
            "id": "route-c-extractor",
            "sourceDigest": DIGEST,
            "inputSchemaDigest": DIGEST,
            "outputSchemaDigest": DIGEST,
        },
        "accounting": {
            "packageExpression": "base + theorem_payload",
            "runtimeExpression": "base_cycles + extracted_cycles",
            "memoryExpression": "base_memory + extracted_state",
        },
        "requiredMargins": {"bytes": 1},
        "privateVerifierDigest": DIGEST,
        "syntheticWitnessReceiptDigests": [],
        "createdAt": "2026-07-26T00:00:00Z",
        "artifactDigest": DIGEST,
    }
    schema = contracts.load_json(contracts.CONTRACT_ROOT / "route-binding.schema.json")
    jsonschema.Draft202012Validator(schema).validate(value)
    value["privateApplicationCertificate"] = {"secret": True}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(value)
