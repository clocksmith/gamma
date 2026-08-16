#!/usr/bin/env python3
"""Freeze the source-exact streaming-dot open top-FF2 gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1"
PARENT_ID = "nncp_open_profile_top_ff2_gradient_64_q0_retry_v1"
PARENT_EXPERIMENT = ROOT / (
    f"operations/adaptive/experiments/{PARENT_ID}.json"
)
PARENT_REVISION = ROOT / (
    "operations/adaptive/candidate-revisions/"
    f"{PARENT_ID}/20260816T061820040240Z_b914054b9184.json"
)
PARENT_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
PARENT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json"
)
DOT_RESULT = ROOT / "results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1"
DOT_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T075342Z_b33521b4a0.json"
)
RUNNER = ROOT / (
    "tools/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1.py"
)
MATERIALIZER = Path(__file__).resolve()
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"experiment input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def source_identifier(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(relative.encode()).hexdigest()[:12]
    return f"runtime-source-{path.stem}-{digest}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["parent"] = {
        "candidateId": PARENT_ID,
        "revision": {
            "path": PARENT_REVISION.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{sha256(PARENT_REVISION)}",
        },
    }
    experiment["hypothesis"] = {
        "claim": (
            "Installing only the source-attributed streaming eight-lane BF16 "
            "g*y dot in the otherwise unchanged open final-RMSNorm backward "
            "makes the complete normalization-input residual and ff2_19 "
            "parameter gradient source-exact while preserving every inherited "
            "forward, output-head, normalization-parameter, projection, replay, "
            "control, dependency, source, and resource predicate."
        ),
        "falsification": (
            "Any inherited predicate failure, nonzero source residual or ff2_19 "
            "mismatch, replay drift, dead control, dependency violation, source "
            "overflow, or guard failure prevents promotion."
        ),
    }
    experiment["changedMechanism"] = (
        "Replace only the generic 64-block g*y product reduction in the open "
        "final-RMSNorm input backward with the source-attributed ordered "
        "eight-lane streaming BF16 FMA dot; preserve the mean-scaled expression "
        "and every other forward, backward, FF2, and control operation."
    )
    experiment["invariants"].extend(
        [
            "The source-attributed streaming dot is applied uniformly to every one of the 2,048 samples and no source adjoint word is available during calculation.",
            "The complete open normalization-input residual is compared directly with the independently captured source-exact adjoint only after both open populations are complete.",
            "The final-RMSNorm expression remains mean-scaled because the attribution gate proved mean- and width-scaled forms BF16-identical on the complete retained population.",
        ]
    )
    experiment["controls"].append(
        {
            "id": "independent-source-final-rms-adjoint",
            "role": "comparator",
            "definition": "The separately captured and exactly reconstructed source final-RMSNorm input adjoint is read only after both open residuals are complete.",
        }
    )
    experiment["causalBoundary"]["availableInformation"].append(
        "The terminal four-cell attribution proves the streaming BF16 dot, not scalar placement, explains the entire eight-word residual boundary."
    )
    experiment["causalBoundary"]["forbiddenInformation"].extend(
        [
            "Using the source-exact adjoint as a calculation input, applying coordinate-specific corrections, changing FF2 reduction, or tolerating any mismatch.",
            "Claiming any deeper activation residual, GEGLU/FF1 gradient, complete transformer backward, recursive update, compression, transfer, package, or Hutter result.",
        ]
    )
    replacements = {
        "runner": reference(RUNNER, "runner"),
        "materializer": reference(MATERIALIZER, "materializer"),
    }
    inputs = [replacements.get(item["id"], item) for item in experiment["inputs"]]
    additions = [
        reference(PARENT_DECISION, "stream-dot-parent-decision"),
        reference(PARENT_REFLECTION, "stream-dot-parent-reflection"),
        reference(DOT_RESULT / "decision.json", "stream-dot-decision"),
        reference(DOT_RESULT / "execution.json", "stream-dot-execution"),
        reference(DOT_REFLECTION, "stream-dot-reflection"),
        reference(
            DOT_RESULT / "source-exact-final-rms-adjoint.bf16",
            "source-exact-final-rms-adjoint",
        ),
    ]
    existing_ids = {item["id"] for item in inputs}
    for item in additions:
        if item["id"] not in existing_ids:
            inputs.append(item)
            existing_ids.add(item["id"])
    present_paths = {item["path"] for item in inputs}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present_paths:
            inputs.append(reference(path, source_identifier(path)))
            present_paths.add(relative)
    experiment["inputs"] = inputs
    experiment["measurements"].extend(
        [
            {
                "id": "sourceFinalNormResidualMismatchCount",
                "unit": "BF16 gradient elements",
                "definition": "Complete open normalization-input residual words differing from the independent source-exact final-RMSNorm adjoint.",
            },
            {
                "id": "maximumSourceFinalNormResidualAbsoluteError",
                "unit": "float32 value",
                "definition": "Maximum complete open versus source-exact normalization-input residual absolute difference.",
            },
        ]
    )
    experiment["promotionPredicates"].extend(
        [
            {
                "id": "p-source-final-rms-residual",
                "measurement": "sourceFinalNormResidualMismatchCount",
                "operator": "eq",
                "threshold": 0,
            },
            {
                "id": "p-source-final-rms-maximum",
                "measurement": "maximumSourceFinalNormResidualAbsoluteError",
                "operator": "eq",
                "threshold": 0,
            },
        ]
    )
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
