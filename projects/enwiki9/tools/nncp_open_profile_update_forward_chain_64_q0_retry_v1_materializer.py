#!/usr/bin/env python3
"""Freeze the canonical-emitter retry of the joint open segment transition."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_update_forward_chain_64_q0_retry_v1"
PARENT_ID = "nncp_open_profile_update_forward_chain_64_q0_v1"
PARENT_EXPERIMENT = ROOT / f"operations/adaptive/experiments/{PARENT_ID}.json"
RUNNER = ROOT / "tools/nncp_open_profile_update_forward_chain_64_q0_retry_v1.py"
MATERIALIZER = Path(__file__).resolve()
PATCHER = ROOT / "tools/materialize_nncp_open_profile_update_forward_chain_64_q0_retry_v1.py"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"
FAILED_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
FAILED_CHAIN = ROOT / f"results/{PARENT_ID}/chain-receipt.json"
FAILED_GUARD = ROOT / f"results/{PARENT_ID}/guard.json"
FAILED_REFLECTION = ROOT / (
    "operations/adaptive/reflections/20260816T023511Z_83fa6c7a64.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"retry input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def source_id(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    slug = "".join(character if character.isalnum() else "-" for character in relative)
    return f"runtime-source-{slug}-{sha256(path)[:12]}"


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = json.loads(PARENT_EXPERIMENT.read_text())
    revisions = sorted(
        (ROOT / "operations/adaptive/candidate-revisions" / PARENT_ID).glob("*.json")
    )
    if not revisions:
        raise ValueError("failed parent has no frozen revision")
    parent_revision = revisions[-1]
    excluded_ids = {
        "runner",
        "materializer",
        "open-adam-payload-source",
        "program-descriptor",
    }
    inputs = [row for row in experiment["inputs"] if row["id"] not in excluded_ids]
    inputs.extend(
        [
            reference(RUNNER, "runner"),
            reference(MATERIALIZER, "materializer"),
            reference(PATCHER, "canonical-emitter-patcher"),
            reference(PROGRAM / "adam_payloads.cpp", "open-adam-payload-source"),
            reference(PROGRAM / "program.py", "program-descriptor"),
            reference(FAILED_DECISION, "failed-emitter-decision"),
            reference(FAILED_CHAIN, "failed-emitter-chain-receipt"),
            reference(FAILED_GUARD, "failed-emitter-guard"),
            reference(FAILED_REFLECTION, "failed-emitter-reflection"),
        ]
    )
    present = {row["path"] for row in inputs}
    sources = set(local_source_closure((RUNNER, MATERIALIZER, PATCHER)))
    sources.add((PROGRAM / "adam_payloads.cpp").resolve())
    sources.add((PROGRAM / "program.py").resolve())
    for path in sorted(sources, key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_id(path)))
            present.add(relative)

    experiment.update(
        {
            "experimentId": CANDIDATE_ID,
            "proposalId": CANDIDATE_ID,
            "parent": {
                "candidateId": PARENT_ID,
                "revision": {
                    "path": parent_revision.relative_to(ROOT).as_posix(),
                    "sha256": f"sha256:{sha256(parent_revision)}",
                },
            },
            "hypothesis": {
                "claim": "Writing predicted parameter payloads directly from the canonical exact Adam replay functions, then chaining those outputs with the already exact open recurrent-memory transition and unchanged exact next-forward, reproduces every retained payload, tensor, and arithmetic branch.",
                "falsification": "Any source-generation drift, canonical Adam comparison error, emitted parameter or recurrent-state mismatch, pre-forward or next-forward error, replay difference, dependency violation, guard failure, or source overflow prevents promotion.",
            },
            "changedMechanism": "Delete the duplicated parameter-update emitter and inject deterministic payload writes at the canonical replay functions immediately before their existing exact word comparisons; retain every input, population, memory transition, forward, predicate, and resource boundary.",
            "inputs": inputs,
            "outputs": [
                f"results/{CANDIDATE_ID}/decision.json",
                f"results/{CANDIDATE_ID}/chain-receipt.json",
                f"results/{CANDIDATE_ID}/execution.json",
                f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
            ],
            "generatedUtc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "pythonSourceClosureEntries": ["runner", "materializer"],
        }
    )
    experiment["invariants"] = [
        value
        for value in experiment["invariants"]
        if not value.startswith("Open parameter payloads are written before")
    ]
    experiment["invariants"].extend(
        [
            "Each emitted parameter word is the canonical replay function's predicted value and is written immediately before comparison with the retained final word; the retained word never influences the prediction.",
            "The generated C++ source must be the exact deterministic patch of the digest-bound promoted Adam replay source; hand-edited or duplicated update arithmetic is forbidden.",
            "The failed parent remains implementation evidence only: its exact memory and pre-forward controls are retained, while its duplicated parameter emitter is not reused.",
        ]
    )
    experiment["controls"].append(
        {
            "id": "failed-duplicated-emitter",
            "role": "negative",
            "definition": "The reflected parent had exact canonical Adam reports but 203 mismatched separately emitted parameter payloads; only the emitter dataflow changes in this retry.",
        }
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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
