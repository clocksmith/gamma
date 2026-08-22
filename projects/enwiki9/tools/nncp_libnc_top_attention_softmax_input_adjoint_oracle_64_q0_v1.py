#!/usr/bin/env python3
"""Capture the layer-19 pre-softmax score and score adjoint twice."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
import re

import nncp_libnc_top_attention_product_oracle_64_q0_v1 as source
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = (
    "nncp_libnc_top_attention_softmax_input_adjoint_oracle_64_q0_v1"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
WORK = RESULT / "work"
PROBE_SOURCE = (
    ROOT / "tools/nncp_libnc_top_attention_softmax_input_adjoint_probe_q0.c"
)
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_top_attention_softmax_input_adjoint_oracle_64_q0_v1_"
    "materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
SCORE_ELEMENTS = source.PROBABILITY_ELEMENTS

_original_patch_teacher = source.patch_teacher
_original_evaluate = source.oracle.evaluate
_score_repeat_identical = False


def patch_teacher(teacher_source: str) -> str:
    """Apply the proven product probes and mark the pre-softmax score."""
    patched = _original_patch_teacher(teacher_source)
    pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)t1\s*=\s*nc_soft_max\(t0(?:,\s*[^)]*)?\);[ \t]*$"
    )
    matches = list(pattern.finditer(patched))
    if len(matches) != 1:
        raise ValueError(
            "expected exactly one layer-19 softmax assignment after product patch, "
            f"found {len(matches)}"
        )
    match = matches[0]
    indent = match.group("indent")
    replacement = (
        f"{indent}t0 = gamma_top_attn_probe_attach(\n"
        f"{indent}    t0, GAMMA_TOP_ATTN_SCORE);\n"
        f"{match.group(0)}"
    )
    return patched[: match.start()] + replacement + patched[match.end() :]


def expected_probe_paths() -> set[str]:
    expected: set[str] = set()
    for kind in ("attended", "probability", "score"):
        for phase in ("input", "adjoint"):
            for state in range(source.STATES):
                stem = f"top_attn_{kind}_{phase}_s{state:03d}"
                expected.add(f"{stem}.bin")
                expected.add(f"{stem}.meta")
    return expected


def combine_score(directory: Path, phase: str, output: Path) -> None:
    bytes_per_state = (
        source.POSITION * source.STREAMS * source.HEADS * 2
    )
    expected_dimensions = (
        f"{source.POSITION},1,{source.HEADS},{source.STREAMS}"
    )
    with output.open("wb") as destination:
        for state in range(source.STATES):
            stem = f"top_attn_score_{phase}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": "score",
                "phase": phase,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": expected_dimensions,
                "byte_order": "little",
            }
            observed_meta = (
                source.capture_base.source_capture.capture.parse_meta(metadata)
                if metadata.is_file()
                else None
            )
            if (
                not payload.is_file()
                or payload.stat().st_size != bytes_per_state
                or observed_meta != expected_meta
            ):
                raise ValueError(
                    f"top attention score {phase} population differs: {state}"
                )
            with payload.open("rb") as raw:
                shutil.copyfileobj(raw, destination, 8 * 1024 * 1024)
    if output.stat().st_size != SCORE_ELEMENTS * 2:
        raise ValueError(f"combined top attention score {phase} differs")


def combine_probe(
    directory: Path, kind: str, phase: str, output: Path
) -> None:
    global _score_repeat_identical
    if kind == "attended":
        axis = source.HEAD_WIDTH
    elif kind == "probability":
        axis = source.POSITION
    else:
        raise ValueError(f"unexpected inherited probe kind: {kind}")
    bytes_per_state = axis * source.HEADS * source.STREAMS * 2
    dimensions = f"{axis},1,{source.HEADS},{source.STREAMS}"
    with output.open("wb") as destination:
        for state in range(source.STATES):
            stem = f"top_attn_{kind}_{phase}_s{state:03d}"
            payload = directory / f"{stem}.bin"
            metadata = directory / f"{stem}.meta"
            expected_meta = {
                "kind": kind,
                "phase": phase,
                "state": str(state),
                "item_type": "1",
                "item_size": "2",
                "dims": dimensions,
                "byte_order": "little",
            }
            observed_meta = (
                source.capture_base.source_capture.capture.parse_meta(metadata)
                if metadata.is_file()
                else None
            )
            if (
                not payload.is_file()
                or payload.stat().st_size != bytes_per_state
                or observed_meta != expected_meta
            ):
                raise ValueError(
                    f"top attention {kind} {phase} population differs: {state}"
                )
            with payload.open("rb") as raw:
                shutil.copyfileobj(raw, destination, 8 * 1024 * 1024)
    expected_elements = (
        source.ATTENDED_ELEMENTS
        if kind == "attended"
        else source.PROBABILITY_ELEMENTS
    )
    if output.stat().st_size != expected_elements * 2:
        raise ValueError(f"combined top attention {kind} {phase} differs")
    if kind != "attended" or phase != "input":
        return
    label = output.name.split("-", 1)[0]
    combined: dict[str, Path] = {}
    for score_phase in ("input", "adjoint"):
        path = WORK / f"{label}-score-{score_phase}.bf16"
        combine_score(directory, score_phase, path)
        combined[score_phase] = path
    destinations = {
        "input": RESULT / "source-attention-score-input.bf16",
        "adjoint": RESULT / "source-attention-score-adjoint.bf16",
    }
    if label == "a":
        for score_phase, destination in destinations.items():
            shutil.copyfile(combined[score_phase], destination)
    elif label == "b":
        _score_repeat_identical = all(
            combined[score_phase].read_bytes()
            == destinations[score_phase].read_bytes()
            for score_phase in destinations
        )
    else:
        raise ValueError(f"unexpected source capture label: {label}")


def add_score_measurements(
    measurements: dict[str, bool | int | float],
) -> None:
    score_input = RESULT / "source-attention-score-input.bf16"
    score_adjoint = RESULT / "source-attention-score-adjoint.bf16"
    measurements.update(
        {
            "scoreInputElementCount": (
                score_input.stat().st_size // 2 if score_input.is_file() else 0
            ),
            "scoreAdjointElementCount": (
                score_adjoint.stat().st_size // 2
                if score_adjoint.is_file()
                else 0
            ),
            "scoreInputLive": (
                score_input.is_file() and any(score_input.read_bytes())
            ),
            "scoreAdjointLive": (
                score_adjoint.is_file() and any(score_adjoint.read_bytes())
            ),
            "scoreCaptureDeterministic": _score_repeat_identical,
        }
    )


def evaluate(
    predicates: list[dict[str, object]],
    measurements: dict[str, bool | int | float],
) -> list[dict[str, object]]:
    add_score_measurements(measurements)
    return _original_evaluate(predicates, measurements)


def append_score_artifacts() -> None:
    decision = RESULT / "decision.json"
    result = json.loads(decision.read_text())
    artifacts = result["artifacts"]
    existing_ids = {item.get("id") for item in artifacts}
    for path, identifier in (
        (RESULT / "source-attention-score-input.bf16", "score-input"),
        (RESULT / "source-attention-score-adjoint.bf16", "score-adjoint"),
    ):
        if path.is_file() and identifier not in existing_ids:
            artifacts.append(source.reference(path, identifier))
    decision.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    research_contracts.validate_artifact(decision)


def configure_source_runner() -> None:
    source.CANDIDATE_ID = CANDIDATE_ID
    source.PROGRAM = PROGRAM
    source.RESULT = RESULT
    source.WORK = WORK
    source.PROBE_SOURCE = PROBE_SOURCE
    source.RUNNER = RUNNER
    source.MATERIALIZER = MATERIALIZER
    source.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    source.patch_teacher = patch_teacher
    source.expected_probe_paths = expected_probe_paths
    source.combine_probe = combine_probe
    source.oracle.evaluate = evaluate
    source.attended_to_concat = lambda input_path, output_path: shutil.copyfile(
        input_path, output_path
    )
    source.capture_base.PROBE_SOURCE = PROBE_SOURCE
    source.capture_base.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    source.capture_base.RUNNER = RUNNER
    source.capture_base.MATERIALIZER = MATERIALIZER
    source.capture_base.patch_teacher = patch_teacher


def main() -> int:
    configure_source_runner()
    returncode = source.main()
    if returncode == 0:
        append_score_artifacts()
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
