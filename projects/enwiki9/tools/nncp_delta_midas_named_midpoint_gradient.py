#!/usr/bin/env python3
"""Run the frozen F-arm named midpoint-gradient localization experiment."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import re
import shutil
import tarfile
import time
from typing import Any

import nncp_libnc_output_head_midpoint_attribution_65536_qm0 as q0
import nncp_libnc_output_head_midpoint_attribution_65536_qm1 as q1
import research_contracts
from materialize_nncp_named_midpoint_gradient import materialize


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "delta_midas_named_midpoint_gradient_65536_q0_v1"
Q1_RESULT = ROOT / "results/nncp_libnc_output_head_midpoint_attribution_65536_qm1_v1/decision.json"
BRIDGE_RESULT = ROOT / "results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/decision.json"
RETAINED_F = ROOT / "results/nncp_libnc_output_head_midpoint_attribution_65536_qm1_v1/F_clean.nncp"
MATERIALIZER = ROOT / "tools/materialize_nncp_named_midpoint_gradient.py"
NAMED_RE = re.compile(
    r"ATTR_NAMED_GRAD block=(\d+) name=([A-Za-z0-9_]+) grad=([0-9a-f]{8}) "
    r"grad_elems=(\d+) param_elems=(\d+) energy=([^ ]+) finite=(\d+)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str | None = None) -> dict[str, str]:
    value = {
        "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(path)}",
    }
    if identifier is not None:
        value["id"] = identifier
    return value


def execute(command: list[str], *, cwd: Path, environment: dict[str, str], log: Path) -> dict[str, Any]:
    started = time.monotonic()
    completed = q0.subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=q0.subprocess.PIPE,
        stderr=q0.subprocess.PIPE,
        check=True,
    )
    log.write_bytes(completed.stderr)
    return {
        "command": command,
        "elapsedSeconds": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr": reference(log),
    }


def gradient_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in NAMED_RE.finditer(path.read_text(errors="replace")):
        energy = float.fromhex(match.group(6))
        rows.append(
            {
                "block": int(match.group(1)),
                "name": match.group(2),
                "gradientHash": match.group(3),
                "gradientElements": int(match.group(4)),
                "parameterElements": int(match.group(5)),
                "energy": energy,
                "finite": match.group(7) == "1" and math.isfinite(energy),
            }
        )
    if not rows:
        raise ValueError(f"named gradient witness is empty: {path}")
    return rows


def parameter_group(name: str) -> str:
    if name in {"embed_out", "out_bias"}:
        return "output-head"
    if name == "embed":
        return "input-embedding"
    if name.startswith(("w_q_", "b_q_", "w_kv_", "w_o_", "w_r_", "b_r_")):
        return "attention"
    if name.startswith(("ff1_", "ff2_", "ff_bias1_", "ff_bias2_")):
        return "feed-forward"
    if name.startswith(("ln_g_", "ln_b_")):
        return "normalization"
    if name.startswith("alpha_"):
        return "residual-scale"
    return "other"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocks = sorted({row["block"] for row in rows})
    names_by_block = {
        block: {row["name"] for row in rows if row["block"] == block}
        for block in blocks
    }
    expected_names = names_by_block[blocks[0]]
    group_energy: dict[str, float] = {}
    third_energy: list[dict[str, float]] = [{}, {}, {}]
    for row in rows:
        group = parameter_group(row["name"])
        group_energy[group] = group_energy.get(group, 0.0) + row["energy"]
        block_index = blocks.index(row["block"])
        third = min(2, block_index * 3 // len(blocks))
        third_energy[third][group] = third_energy[third].get(group, 0.0) + row["energy"]
    total = sum(group_energy.values())
    non_head = {key: value for key, value in group_energy.items() if key != "output-head"}
    dominant = max(non_head, key=non_head.get)
    third_dominant = [
        max(
            (key for key in energy if key != "output-head"),
            key=lambda key: energy[key],
        )
        for energy in third_energy
    ]
    shares = []
    for energy in third_energy:
        denominator = sum(value for key, value in energy.items() if key != "output-head")
        shares.append(energy.get(dominant, 0.0) / denominator if denominator else 0.0)
    return {
        "blockCount": len(blocks),
        "parameterCount": len(expected_names),
        "allBlocksSameParameterSet": all(names == expected_names for names in names_by_block.values()),
        "allGradientFinite": all(row["finite"] for row in rows),
        "groupEnergy": group_energy,
        "thirdGroupEnergy": third_energy,
        "dominantNonHeadGroup": dominant,
        "thirdDominantNonHeadGroups": third_dominant,
        "stableDominantNonHeadGroup": all(group == dominant for group in third_dominant),
        "minimumThirdDominantNonHeadShare": min(shares),
        "headGroupShare": group_energy.get("output-head", 0.0) / total if total else 1.0,
    }


def evaluate(predicates: list[dict[str, Any]], measurements: dict[str, Any]) -> list[dict[str, Any]]:
    operations = {
        "eq": lambda value, threshold: value == threshold,
        "gt": lambda value, threshold: value > threshold,
        "gte": lambda value, threshold: value >= threshold,
        "lt": lambda value, threshold: value < threshold,
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


def source_package(path: Path) -> None:
    members = [Path(__file__), MATERIALIZER, q0.MATERIALIZER, Path(q0.__file__), Path(q1.__file__)]
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in members:
            archive.add(member, arcname=member.relative_to(ROOT))
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment_path = args.experiment.resolve()
    output = args.output.resolve()
    experiment = json.loads(experiment_path.read_text())
    research_contracts.validate_artifact(experiment_path)
    if experiment["proposalId"] != CANDIDATE_ID:
        raise ValueError("experiment does not identify this candidate")
    job_experiment = json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    if reference(experiment_path) != job_experiment:
        raise ValueError("job and tool experiment bindings differ")
    candidate_revision = json.loads(os.environ["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"])
    if candidate_revision["candidateId"] != CANDIDATE_ID:
        raise ValueError("job candidate revision identifies another candidate")
    bridge_decision = json.loads(BRIDGE_RESULT.read_text())
    for identifier, path in (
        ("source_tar", q0.SOURCE_TAR),
        ("preprocessed", q0.PREPROCESSED),
        ("dictionary", q0.DICTIONARY),
    ):
        expected = bridge_decision["inputs"][identifier]
        if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            raise ValueError(f"external closed-teacher input differs: {identifier}")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite result: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = output.parent / "scratch"
    source = scratch / "source"
    source.mkdir(parents=True)
    q1.extract_into_existing(source)
    q0.bridge.run(["patch", "-p1", "-i", str(q1.PROGRAM / "nncp_midsegment32.patch")], cwd=source)
    materialize(source)
    build = q0.bridge.run(["make", "-j4"], cwd=source)
    binary = source / "nncp"
    executions: list[dict[str, Any]] = []
    rows: list[list[dict[str, Any]]] = []
    archives: list[Path] = []
    logs: list[Path] = []
    for run_index in range(2):
        archive = output.parent / f"F_named_gradient_{run_index + 1}.nncp"
        log = output.parent / f"F_named_gradient_{run_index + 1}.stderr"
        executions.append(
            execute(
                q0.encode_command(binary, archive, q0.ARMS["F"]),
                cwd=source,
                environment=q0.environment(source),
                log=log,
            )
        )
        archives.append(archive)
        logs.append(log)
        rows.append(gradient_rows(log))
    shutil.rmtree(scratch)
    package = output.parent / "incremental_source.tar.xz"
    source_package(package)
    q1_decision = json.loads(Q1_RESULT.read_text())
    summary = summarize(rows[0])
    archive_identity = all(path.read_bytes() == RETAINED_F.read_bytes() for path in archives)
    gradient_identity = rows[0] == rows[1]
    localization_failed = not (
        summary["stableDominantNonHeadGroup"]
        and summary["minimumThirdDominantNonHeadShare"] >= 0.35
        and summary["headGroupShare"] <= 0.5
    )
    measurements = {
        "retainedArchiveIdentity": archive_identity,
        "rawInverseExact": bool(q1_decision["integrity"]["raw_inverse_exact"]["F"] and archive_identity),
        "namedGradientDeterministic": gradient_identity,
        "allBlocksSameParameterSet": summary["allBlocksSameParameterSet"],
        "allGradientFinite": summary["allGradientFinite"],
        "stableDominantNonHeadGroup": summary["stableDominantNonHeadGroup"],
        "minimumThirdDominantNonHeadShare": summary["minimumThirdDominantNonHeadShare"],
        "headGroupShare": summary["headGroupShare"],
        "localizationFailed": localization_failed,
        "blockCount": summary["blockCount"],
        "parameterCount": summary["parameterCount"],
    }
    promotion = evaluate(experiment["promotionPredicates"], measurements)
    kill = evaluate(experiment["killPredicates"], measurements)
    promotion_pass = all(row["passed"] for row in promotion)
    kill_pass = all(row["passed"] for row in kill)
    decision = "authorize-successor" if promotion_pass else "retire" if kill_pass else "retry"
    detail = {
        "schema": "gamma.enwiki9.named-gradient-detail.v1",
        "experiment": reference(experiment_path),
        "candidateRevision": candidate_revision,
        "summary": summary,
        "build": build,
        "executions": executions,
        "runs": rows,
    }
    detail_path = output.parent / "gradient-detail.json"
    detail_path.write_text(json.dumps(detail, indent=2, sort_keys=True) + "\n")
    artifacts = [
        reference(archives[0], "archive-1"),
        reference(archives[1], "archive-2"),
        reference(logs[0], "gradient-log-1"),
        reference(logs[1], "gradient-log-2"),
        reference(package, "source-package"),
        reference(detail_path, "gradient-detail"),
    ]
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
        "decision": decision,
        "artifacts": artifacts,
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(output)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
