#!/usr/bin/env python3
"""Capture and replay the first post-update forward with export receipts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import tarfile
from typing import Any

from enwiki9_python_source_closure import local_source_closure
import nncp_ggml_profile_forward_parity_64_qm18 as q18
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_ggml_postupdate_forward_parity_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
ARTIFACTS = RESULT / "artifacts"
PARENT_ID = "nncp_open_profile_adam_replay_64_q0_retry_v2"
PARENT_DECISION = ROOT / "results" / PARENT_ID / "decision.json"
PARENT_GUARD = ROOT / "results" / PARENT_ID / "guard.json"
PARENT_REFLECTION = (
    ROOT / "operations/adaptive/reflections/20260816T003855Z_aab09244b0.json"
)
Q3_DECISION = (
    ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/decision.json"
)
Q18_DECISION = (
    ROOT / "results/nncp_ggml_profile_forward_parity_64_qm18_v1/decision.json"
)
FAILED_REFLECTION = (
    ROOT / "operations/adaptive/reflections/20260816T005343Z_d612abab3e.json"
)
EXPORT_RECEIPTS = RESULT / "export-receipts.json"
SOURCE_CEILING = 2_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents:
        raise ValueError(f"reference escapes enwiki9 project: {path}")
    if not resolved.is_file():
        raise FileNotFoundError(f"referenced file is missing: {path}")
    row = {
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }
    if identifier is not None:
        row["id"] = identifier
    return row


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"capture coordinate marker is not unique: {old}")
    return source.replace(old, new, 1)


def write_export_receipts(rows: list[dict[str, Any]]) -> None:
    RESULT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "gamma.enwiki9.nncp-export-receipts.v1",
        "objective": research_contracts.objective_binding(),
        "candidateId": CANDIDATE_ID,
        "exports": rows,
    }
    EXPORT_RECEIPTS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def configure_base() -> tuple[Any, list[dict[str, Any]]]:
    base = q18.base
    base.CANDIDATE_ID = CANDIDATE_ID
    base.PROGRAM = PROGRAM
    base.RESULT = ARTIFACTS
    helper = base.CAPTURE_HELPER
    helper = replace_once(helper, "block_idx != 256", "block_idx != 320")
    helper = replace_once(helper, "local_position < 256", "local_position < 320")
    helper = replace_once(helper, "local_position >= 320", "local_position >= 384")
    helper = replace_once(helper, "local_position - 256", "local_position - 320")
    base.CAPTURE_HELPER = helper
    base.PROFILE = {
        **base.PROFILE,
        "target_block_position": 320,
        "target_original_symbol_start": 320,
        "target_original_symbol_end": 384,
    }
    export_receipts: list[dict[str, Any]] = []
    original_run = base.run

    def receipt_run(command: list[str], **kwargs: object):
        if Path(command[0]).name != "nncp_libnc_export":
            return original_run(command, **kwargs)
        source = Path(command[1])
        output_directory = Path(command[2])
        row: dict[str, Any] = {
            "input": source.name,
            "inputBytes": source.stat().st_size,
            "inputSha256": f"sha256:{sha256(source)}",
        }
        try:
            completed = original_run(command, **kwargs)
        except subprocess.CalledProcessError as error:
            row.update(
                {
                    "status": "failed",
                    "returncode": error.returncode,
                    "stdout": error.stdout or "",
                    "stderr": error.stderr or "",
                }
            )
            export_receipts.append(row)
            write_export_receipts(export_receipts)
            raise RuntimeError(
                f"{source.name} export failed with status {error.returncode}: "
                f"{(error.stderr or '').strip()}"
            ) from error
        manifest_path = output_directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        row.update(
            {
                "status": "passed",
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "manifestBytes": manifest_path.stat().st_size,
                "manifestSha256": f"sha256:{sha256(manifest_path)}",
                "tensorCount": manifest["tensor_count"],
            }
        )
        export_receipts.append(row)
        return completed

    base.run = receipt_run
    original_extract = base.extract_fixture

    def extract_fixture(temporary: Path, executable: Path, exporter: Path, hook: Path):
        fixture, manifest = original_extract(temporary, executable, exporter, hook)
        manifest["selection"] = {
            "reason": "first complete segment after the production train-step-four update",
            "startup_padding": False,
            "remainder_behavior": False,
            "input_original_symbol_start": 319,
            "input_original_symbol_end": 383,
            "truth_original_symbol_start": 320,
            "truth_original_symbol_end": 384,
        }
        (fixture / "fixture_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        return fixture, manifest

    base.extract_fixture = extract_fixture
    return base, export_receipts


def require_inputs(experiment: dict[str, Any]) -> None:
    inputs = {item["id"]: item for item in experiment["inputs"]}
    for identifier, path in (
        ("open-update-decision", PARENT_DECISION),
        ("open-update-guard", PARENT_GUARD),
        ("open-update-reflection", PARENT_REFLECTION),
        ("q3-update-decision", Q3_DECISION),
        ("q18-forward-decision", Q18_DECISION),
        ("failed-export-reflection", FAILED_REFLECTION),
    ):
        if inputs.get(identifier) != reference(path, identifier):
            raise ValueError(f"experiment does not bind {identifier}")
    parent = json.loads(PARENT_DECISION.read_text())
    reflection = json.loads(PARENT_REFLECTION.read_text())
    q3 = json.loads(Q3_DECISION.read_text())
    q18_decision = json.loads(Q18_DECISION.read_text())
    failed_reflection = json.loads(FAILED_REFLECTION.read_text())
    if not (
        parent.get("promotionPass") is True
        and parent.get("measurements", {}).get("openReplayExact") is True
        and reflection.get("decision", {}).get("verdict") == "promote"
        and q3.get("promotionPass") is True
        and q18_decision.get("overall_pass") is True
        and q18_decision.get("maximum_tensor_absolute_error") == 0
        and failed_reflection.get("decision", {}).get("verdict") == "retry"
        and failed_reflection.get("hypothesis", {}).get("verdict") == "not-tested"
    ):
        raise ValueError("post-update forward antecedents are not satisfied")


def source_package(path: Path, experiment: dict[str, Any]) -> None:
    members = [
        *local_source_closure((Path(__file__),)),
        (PROGRAM / "CMakeLists.txt").resolve(),
        (PROGRAM / "profile_forward_parity.cpp").resolve(),
        (PROGRAM / "program.py").resolve(),
    ]
    members = sorted(set(members), key=lambda item: item.relative_to(ROOT).as_posix())
    declared = {item["path"]: item for item in experiment["inputs"]}
    for member in members:
        relative = member.relative_to(ROOT).as_posix()
        expected = declared.get(relative)
        if expected is None or expected != reference(member, expected["id"]):
            raise ValueError(f"runtime source closure drifted: {relative}")
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            info = archive.gettarinfo(
                str(member), arcname=member.relative_to(ROOT).as_posix()
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as stream:
                archive.addfile(info, stream)
    compressed = lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME)
    tar_path.unlink()
    if len(compressed) > SOURCE_CEILING:
        raise ValueError("post-update forward Python/source closure exceeds ceiling")
    path.write_bytes(compressed)


def evaluate(
    predicates: list[dict[str, Any]], measurements: dict[str, bool | int | float]
) -> list[dict[str, Any]]:
    operations = {
        "eq": lambda value, threshold: value == threshold,
        "lte": lambda value, threshold: value <= threshold,
    }
    return [
        {
            **predicate,
            "observed": measurements[predicate["measurement"]],
            "passed": bool(
                operations[predicate["operator"]](
                    measurements[predicate["measurement"]], predicate["threshold"]
                )
            ),
        }
        for predicate in predicates
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    output = args.output.resolve()
    research_contracts.validate_artifact(experiment_path)
    experiment = json.loads(experiment_path.read_text())
    if experiment["proposalId"] != CANDIDATE_ID:
        raise ValueError("experiment identifies another candidate")
    if reference(experiment_path) != json.loads(
        os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]
    ):
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(
        os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
    )
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    require_inputs(experiment)
    if output != RESULT / "decision.json" or ARTIFACTS.exists() or output.exists():
        raise ValueError("post-update forward result boundary is not fresh")
    RESULT.mkdir(parents=True, exist_ok=True)

    base, export_receipts = configure_base()
    returncode = base.main()
    if returncode:
        raise RuntimeError("legacy post-update forward comparison failed")
    legacy_path = ARTIFACTS / "decision.json"
    legacy = json.loads(legacy_path.read_text())
    write_export_receipts(export_receipts)
    incremental = RESULT / "incremental_source.tar.xz"
    source_package(incremental, experiment)
    measurements: dict[str, bool | int | float] = {
        "antecedentsPass": True,
        "coordinatePass": legacy["profile"]["target_block_position"] == 320
        and legacy["profile"]["target_original_symbol_end"] == 384,
        "fixtureComplete": legacy["fixture_complete"] is True,
        "exportReceiptPass": len(export_receipts) == 2
        and all(row["status"] == "passed" for row in export_receipts),
        "exportedParameterTensorCount": export_receipts[0]["tensorCount"],
        "exportedStateTensorCount": export_receipts[1]["tensorCount"],
        "openForwardOverallPass": legacy["overall_pass"] is True,
        "openForwardDeterministic": legacy["repeat_open_outputs_byte_identical"] is True,
        "maximumTensorAbsoluteError": legacy["maximum_tensor_absolute_error"],
        "maximumBranchCountDifference": legacy["branch_comparison"][
            "maximum_integer_probability_count_difference"
        ],
        "forbiddenDynamicDependencyCount": len(
            legacy["open_build"]["forbidden_dynamic_dependencies"]
        ),
        "incrementalSourceBytes": incremental.stat().st_size,
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    result = {
        "schema": "gamma.enwiki9.adaptive-experiment-result.v1",
        "objective": research_contracts.objective_binding(),
        "experiment": reference(experiment_path),
        "candidateId": CANDIDATE_ID,
        "candidateRevision": candidate_revision,
        "evidenceClass": experiment["evidenceClass"],
        "objectiveCreditBytes": 0,
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "promotionPass": promotion_pass,
        "killPass": kill_pass,
        "decision": "authorize-successor" if promotion_pass else "retire",
        "artifacts": [
            reference(legacy_path, "post-update-forward-decision"),
            reference(EXPORT_RECEIPTS, "export-receipts"),
            reference(ARTIFACTS / "production_forward_fixture.tar.xz", "fixture"),
            reference(
                ARTIFACTS / "ggml_profile_forward_source_closure.tar.xz",
                "open-source-package",
            ),
            reference(incremental, "incremental-source-package"),
        ],
        "generatedUtc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if promotion_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
