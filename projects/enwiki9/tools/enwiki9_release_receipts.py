#!/usr/bin/env python3
"""Generate the canonical router for dependency bundles and release receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import research_contracts


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTPUT = ROOT / "docs" / "release_receipt_index.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def reference(path: Path) -> dict[str, str]:
    return {
        "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{digest(path)}",
    }


def collect() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    manifests = sorted(RESULTS.glob("*/release/*/dependency-closure.json"))
    for manifest_path in manifests:
        manifest_result = research_contracts.validate_artifact(
            manifest_path,
            verify_files=False,
        )
        manifest = load_json(manifest_path)
        bundle = manifest_path.parent
        candidate_id = bundle.parents[1].name
        if manifest["candidateId"] != candidate_id:
            raise ValueError(f"candidate path differs from manifest: {manifest_path}")

        run_path = bundle / "run-receipt.json"
        run_row: dict[str, Any] | None = None
        if run_path.is_file():
            run_result = research_contracts.validate_artifact(
                run_path,
                verify_files=False,
            )
            run = load_json(run_path)
            run_row = {
                "reference": reference(run_path),
                "verdict": run["verdict"],
                "officialScoreBytes": run["accounting"]["officialScoreBytes"],
                "targetDebtBytes": run["accounting"]["targetDebtBytes"],
                "objectiveCriteriaPass": run_result["objectiveCriteriaPass"],
            }

        attempt_path = bundle / "replay" / "attempt.json"
        attempt_row: dict[str, Any] | None = None
        if attempt_path.is_file():
            research_contracts.validate_artifact(
                attempt_path,
                verify_files=False,
            )
            attempt = load_json(attempt_path)
            attempt_row = {
                "reference": reference(attempt_path),
                "error": attempt["error"],
                "scratchCleaned": attempt["scratchCleaned"],
            }
        if run_row is not None and attempt_row is not None:
            raise ValueError(f"bundle has both run and failure receipts: {bundle}")

        rows.append(
            {
                "candidateId": candidate_id,
                "bundlePath": bundle.relative_to(ROOT).as_posix(),
                "manifest": reference(manifest_path),
                "dependencyClosureComplete": manifest_result["complete"],
                "runReceipt": run_row,
                "failedAttempt": attempt_row,
            }
        )
    summary = {
        "bundles": len(rows),
        "completeClosures": sum(row["dependencyClosureComplete"] for row in rows),
        "runReceipts": sum(row["runReceipt"] is not None for row in rows),
        "failedAttempts": sum(row["failedAttempt"] is not None for row in rows),
        "objectiveAchievedReceipts": sum(
            row["runReceipt"] is not None
            and row["runReceipt"]["verdict"] == "objective-achieved"
            for row in rows
        ),
    }
    return {
        "schema": "gamma.enwiki9.release-receipt-index.v1",
        "objective": research_contracts.objective_binding(),
        "validationMode": "structure-only-router",
        "summary": summary,
        "bundles": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = collect()
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != rendered:
            raise SystemExit("release receipt index is stale")
    else:
        temporary = OUTPUT.with_name(f".{OUTPUT.name}.{os.getpid()}.tmp")
        temporary.write_text(rendered)
        os.replace(temporary, OUTPUT)
    research_contracts.validate_artifact(OUTPUT, verify_files=False)
    print(json.dumps(value["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
