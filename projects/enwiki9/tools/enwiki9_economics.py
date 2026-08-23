#!/usr/bin/env python3
"""Derive evidence-bound enwik9 archive-gain gates without proposal estimates."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "gamma.enwiki9.economics-input.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.economics-receipt.v1"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def exact_int(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def load_input(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"expected {INPUT_SCHEMA}")
    required = {
        "candidateId",
        "objective",
        "parent",
        "scoreFormula",
        "economics",
        "evidence",
        "scopesBytes",
    }
    missing = sorted(required - value.keys())
    if missing:
        raise ValueError(f"missing input fields: {', '.join(missing)}")
    return value


def ceil_scaled(full_value: int, scope: int, corpus: int) -> int:
    return (full_value * scope + corpus - 1) // corpus


def calculate(value: dict[str, Any], input_path: Path) -> dict[str, Any]:
    objective = value["objective"]
    parent = value["parent"]
    score_formula = value["scoreFormula"]
    economics = value["economics"]
    evidence = value["evidence"]

    target = exact_int(
        objective["targetCompleteCountedBytes"],
        "objective.targetCompleteCountedBytes",
        1,
    )
    corpus = exact_int(objective["corpusBytes"], "objective.corpusBytes", 1)
    parent_total = exact_int(
        parent["completeCountedBytes"],
        "parent.completeCountedBytes",
    )
    maximum_package = exact_int(
        economics["maximumAddedPackageBytes"],
        "economics.maximumAddedPackageBytes",
    )
    reserve = exact_int(
        economics["transferReserveBytes"],
        "economics.transferReserveBytes",
    )
    realized = exact_int(
        economics["realizedExactPackageSavingsBytes"],
        "economics.realizedExactPackageSavingsBytes",
    )

    scopes = [
        exact_int(scope, f"scopesBytes[{index}]", 1)
        for index, scope in enumerate(value["scopesBytes"])
    ]
    if len(scopes) != len(set(scopes)):
        raise ValueError("scopesBytes must be unique")
    if any(scope > corpus for scope in scopes):
        raise ValueError("a screening scope exceeds the corpus")
    scopes.sort()

    debt = max(0, parent_total - target)
    required_net = max(0, debt + reserve - realized)
    required_gross = required_net + maximum_package
    scope_gates = [
        {
            "scopeBytes": scope,
            "requiredGrossArchiveSavingsBytes": ceil_scaled(
                required_gross,
                scope,
                corpus,
            ),
        }
        for scope in scopes
    ]

    parent_terminal = require_bool(parent["terminal"], "parent.terminal")
    formula_bound = require_bool(score_formula["bound"], "scoreFormula.bound")
    dependencies_passed = require_bool(
        evidence["dependenciesPassed"],
        "evidence.dependenciesPassed",
    )
    resource_feasible = require_bool(
        evidence["resourceFeasible"],
        "evidence.resourceFeasible",
    )
    oracle = evidence["measuredOracleCeilingBytes"]
    oracle_scope = evidence.get("measuredOracleCeilingScopeBytes")
    lower_bound = evidence["measuredLowerBoundGainBytes"]
    lower_bound_scope = evidence.get("measuredLowerBoundGainScopeBytes")
    transfer = evidence["measuredTransferPassed"]
    if oracle is not None:
        oracle = exact_int(oracle, "evidence.measuredOracleCeilingBytes")
    if lower_bound is not None:
        lower_bound = exact_int(
            lower_bound,
            "evidence.measuredLowerBoundGainBytes",
        )
    if oracle is not None and oracle_scope is None:
        raise ValueError(
            "evidence.measuredOracleCeilingScopeBytes is required when measuredOracleCeilingBytes is set"
        )
    if oracle is None and oracle_scope is not None:
        raise ValueError(
            "evidence.measuredOracleCeilingScopeBytes requires measuredOracleCeilingBytes"
        )
    if lower_bound is not None and lower_bound_scope is None:
        raise ValueError(
            "evidence.measuredLowerBoundGainScopeBytes is required when measuredLowerBoundGainBytes is set"
        )
    if lower_bound is None and lower_bound_scope is not None:
        raise ValueError(
            "evidence.measuredLowerBoundGainScopeBytes requires measuredLowerBoundGainBytes"
        )
    if oracle_scope is not None:
        oracle_scope = exact_int(
            oracle_scope,
            "evidence.measuredOracleCeilingScopeBytes",
            1,
        )
        if oracle_scope > corpus:
            raise ValueError("evidence.measuredOracleCeilingScopeBytes exceeds corpus")
    if lower_bound_scope is not None:
        lower_bound_scope = exact_int(
            lower_bound_scope,
            "evidence.measuredLowerBoundGainScopeBytes",
            1,
        )
        if lower_bound_scope > corpus:
            raise ValueError("evidence.measuredLowerBoundGainScopeBytes exceeds corpus")
    if transfer is not None:
        transfer = require_bool(transfer, "evidence.measuredTransferPassed")

    oracle_required = (
        ceil_scaled(required_gross, oracle_scope, corpus)
        if oracle_scope is not None
        else None
    )
    lower_bound_required = (
        ceil_scaled(required_gross, lower_bound_scope, corpus)
        if lower_bound_scope is not None
        else None
    )

    reasons: list[str] = []
    if not parent_terminal:
        reasons.append("parent evidence is nonterminal")
    if not formula_bound:
        reasons.append("official or expanded-closure score formula is unbound")
    if not dependencies_passed:
        reasons.append("candidate dependencies have not passed")
    if not resource_feasible:
        reasons.append("candidate resource feasibility is unproven")
    if oracle is None:
        reasons.append("measured oracle ceiling is absent")
    elif oracle_required is not None and oracle < oracle_required:
        reasons.append(
            f"measured oracle ceiling {oracle} bytes is below the "
            f"scope-adjusted requirement {oracle_required} bytes at "
            f"{oracle_scope} corpus bytes"
        )
    if lower_bound is None:
        reasons.append("measured lower-bound archive gain is absent")
    elif lower_bound_required is not None and lower_bound < lower_bound_required:
        reasons.append(
            f"measured lower-bound archive gain {lower_bound} bytes is below "
            f"the scope-adjusted requirement {lower_bound_required} bytes at "
            f"{lower_bound_scope} corpus bytes"
        )
    if transfer is not True:
        reasons.append("measured transfer pass is absent")

    base_authority = (
        parent_terminal
        and formula_bound
        and dependencies_passed
        and resource_feasible
    )
    screening_authorized = (
        base_authority
        and oracle is not None
        and oracle_required is not None
        and oracle >= oracle_required
    )
    promotion_authorized = (
        screening_authorized
        and lower_bound is not None
        and lower_bound_required is not None
        and lower_bound >= lower_bound_required
        and transfer is True
    )

    return {
        "schema": RECEIPT_SCHEMA,
        "candidateId": value["candidateId"],
        "input": {
            "path": input_path.as_posix(),
            "sha256": f"sha256:{digest(input_path)}",
        },
        "calculation": {
            "parentCompleteCountedBytes": parent_total,
            "targetCompleteCountedBytes": target,
            "baseDebtBytes": debt,
            "maximumAddedPackageBytes": maximum_package,
            "transferReserveBytes": reserve,
            "realizedExactPackageSavingsBytes": realized,
            "requiredNetSavingsBytes": required_net,
            "requiredGrossArchiveSavingsBytes": required_gross,
        },
        "scopeGates": scope_gates,
        "authority": {
            "parentTerminal": parent_terminal,
            "scoreFormulaBound": formula_bound,
            "dependenciesPassed": dependencies_passed,
            "resourceFeasible": resource_feasible,
            "measuredOraclePresent": oracle is not None,
            "measuredOracleScopeBytes": oracle_scope,
            "measuredOracleRequiredGrossBytes": oracle_required,
            "measuredLowerBoundPresent": lower_bound is not None,
            "measuredLowerBoundScopeBytes": lower_bound_scope,
            "measuredLowerBoundRequiredGrossBytes": lower_bound_required,
            "measuredTransferPassed": transfer,
            "screeningAuthorized": screening_authorized,
            "promotionAuthorized": promotion_authorized,
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
    path.parent.mkdir(parents=True, exist_ok=False)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def command_compute(args: argparse.Namespace) -> int:
    input_path = args.input.resolve()
    value = load_input(input_path)
    receipt = calculate(value, input_path)
    if args.output is None:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        write_new(args.output.resolve(), receipt)
    return 0


def command_verify(args: argparse.Namespace) -> int:
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError(f"expected {RECEIPT_SCHEMA}")
    input_path = Path(receipt["input"]["path"]).resolve()
    expected = calculate(load_input(input_path), input_path)
    if canonical_without_time(receipt) != canonical_without_time(expected):
        raise ValueError("economics receipt does not match derived values")
    print("economics receipt verified")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compute = subparsers.add_parser("compute")
    compute.add_argument("--input", type=Path, required=True)
    compute.add_argument("--output", type=Path)
    compute.set_defaults(handler=command_compute)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--receipt", type=Path, required=True)
    verify.set_defaults(handler=command_verify)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
