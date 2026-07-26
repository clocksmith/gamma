#!/usr/bin/env python3
"""Build and verify the private Atlas-Clockwork Seal commitment."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "operations" / "atlas_clockwork_seal_v2"
STATUS = OPS / "binding_status.json"
COMMITMENT = OPS / "commitment.json"
ROUTES = ("A", "B", "C", "D")
ROUTE_FILES = {r: OPS / f"route-{r.lower()}.rejection.json" for r in ROUTES}
FROZEN = (
    ROOT / "docs" / "atlas_clockwork_seal_problem_set.md",
    ROOT / "docs" / "atlas_clockwork_seal_specification.md",
    ROOT / "docs" / "atlas_clockwork_seal_rubric.md",
    ROOT / "docs" / "atlas_clockwork_seal_binding_audit.md",
    ROOT / "docs" / "target_revision_20260725.md",
    STATUS,
    OPS / "route-binding.schema.json",
    *ROUTE_FILES.values(),
    ROOT
    / "operations"
    / "adaptive"
    / "proposals"
    / "proposed"
    / "881_seal2_route_c_under_target_teacher_v1.json",
    ROOT
    / "operations"
    / "adaptive"
    / "proposals"
    / "proposed"
    / "929_seal2_route_a_paid_predictor_partition_v1.json",
    Path(__file__).resolve(),
)


class SealError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SealError(f"{path}: root must be an object")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def artifact(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SealError(f"missing artifact: {rel(path)}")
    payload = path.read_bytes()
    return {"path": rel(path), "bytes": len(payload), "sha256": digest(payload)}


def validate_route(route: str, decision: dict[str, Any]) -> None:
    if decision.get("schema") != "atlas_clockwork.route_decision/v1":
        raise SealError(f"Route {route}: wrong schema")
    if decision.get("route_id") != route:
        raise SealError(f"Route {route}: route mismatch")
    state = decision.get("binding_status")
    if state == "rejected":
        if decision.get("publication_status") != "removed":
            raise SealError(f"Route {route}: rejected route is not removed")
        if decision.get("score_credit_bytes") != 0:
            raise SealError(f"Route {route}: rejected route has score credit")
        if not decision.get("missing_antecedents") or not decision.get("reason"):
            raise SealError(f"Route {route}: incomplete rejection")
        return
    if state != "bound" or decision.get("publication_status") != "authorized":
        raise SealError(f"Route {route}: invalid binding state")
    fields = (
        "hypothesis_certificate",
        "conditional_reduction",
        "canonical_map",
        "verification_receipt",
    )
    for field in fields:
        value = decision.get(field)
        if not isinstance(value, str) or not (ROOT / value).is_file():
            raise SealError(f"Route {route}: missing {field}")
    receipt = load(ROOT / decision["verification_receipt"])
    truths = (
        "conditional_implication_verified",
        "target_bound_verified",
        "resource_bounds_verified",
        "independent_audit_verified",
    )
    if any(receipt.get(field) is not True for field in truths):
        raise SealError(f"Route {route}: incomplete verification receipt")
    if receipt.get("target_score_bytes") != 108000000:
        raise SealError(f"Route {route}: wrong target")


def state() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    status = load(STATUS)
    decisions = {route: load(path) for route, path in ROUTE_FILES.items()}
    for route, decision in decisions.items():
        validate_route(route, decision)
    authorized = sorted(
        route for route, value in decisions.items()
        if value["binding_status"] == "bound"
    )
    removed = sorted(set(ROUTES) - set(authorized))
    if status.get("authorized_routes") != authorized:
        raise SealError("authorized route drift")
    if status.get("removed_routes") != removed:
        raise SealError("removed route drift")
    activation = status.get("activation_status")
    distribution = status.get("public_distribution_authorized")
    if activation == "BOUND":
        if not authorized or distribution is not True:
            raise SealError("invalid BOUND state")
    elif activation == "UNBOUND":
        if distribution is not False:
            raise SealError("UNBOUND state authorizes distribution")
    else:
        raise SealError("invalid activation status")
    return status, decisions


def build() -> dict[str, Any]:
    status, decisions = state()
    value: dict[str, Any] = {
        "schema": "atlas_clockwork.commitment/v1",
        "seal_version": status["seal_version"],
        "activation_status": status["activation_status"],
        "public_distribution_authorized": status[
            "public_distribution_authorized"
        ],
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "target": status["target"],
        "authorized_routes": status["authorized_routes"],
        "removed_routes": status["removed_routes"],
        "route_decision_sha256": {
            route: digest(canonical(decision))
            for route, decision in decisions.items()
        },
        "artifacts": [artifact(path) for path in FROZEN],
    }
    value["commitment_sha256"] = digest(canonical(value))
    COMMITMENT.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return value


def verify(require_bound: bool) -> dict[str, Any]:
    status, decisions = state()
    manifest = load(COMMITMENT)
    claimed = manifest.pop("commitment_sha256", None)
    if claimed != digest(canonical(manifest)):
        raise SealError("commitment hash mismatch")
    if manifest.get("activation_status") != status["activation_status"]:
        raise SealError("activation status drift")
    if manifest.get("authorized_routes") != status["authorized_routes"]:
        raise SealError("authorized route manifest drift")
    route_hashes = {
        route: digest(canonical(decision))
        for route, decision in decisions.items()
    }
    if manifest.get("route_decision_sha256") != route_hashes:
        raise SealError("route decision hash drift")
    if manifest.get("artifacts") != [artifact(path) for path in FROZEN]:
        raise SealError("artifact hash, size, order, or path drift")
    if require_bound and status["activation_status"] != "BOUND":
        raise SealError("Seal is integrity-valid but UNBOUND")
    return {
        "verdict": (
            "VALID_BOUND"
            if status["activation_status"] == "BOUND"
            else "VALID_UNBOUND"
        ),
        "commitment_sha256": claimed,
        "authorized_routes": status["authorized_routes"],
        "public_distribution_authorized": status[
            "public_distribution_authorized"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build")
    verify_command = commands.add_parser("verify")
    verify_command.add_argument("--require-bound", action="store_true")
    args = parser.parse_args()
    try:
        result = build() if args.command == "build" else verify(args.require_bound)
    except (OSError, ValueError, SealError) as exc:
        print(f"INVALID: {exc}")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
