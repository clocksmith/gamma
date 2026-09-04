#!/usr/bin/env python3
"""Run the correction-only v3 attention-probability-adjoint gate.

The mathematical evaluator, tensor population, controls, compiler flags, and
resource policy are inherited unchanged from v2.  This wrapper corrects only
the snapshot evidence check: candidate revisions normalize ``meta.json`` by
excluding derived reporting fields, so the live and sealed metadata must be
compared under that same semantic normalization rather than as raw bytes.
"""

from __future__ import annotations

import importlib.util
import json
import lzma
import os
from pathlib import Path
import stat
import tarfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools/nncp_open_top_attention_probability_adjoint_64_q0_v2.py"
CANDIDATE_ID = "nncp_open_top_attention_probability_adjoint_64_q0_v3"
EXPERIMENT_ID = CANDIDATE_ID
DERIVED_META_FIELDS = {
    "added",
    "decision",
    "latest_result",
    "measured",
    "promotion",
    "proof",
    "status",
    "triage",
    "verdict",
}


def load_base() -> Any:
    specification = importlib.util.spec_from_file_location(
        "gamma_nncp_probability_adjoint_v2_base", BASE_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load the frozen v2 runner")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


BASE = load_base()
BASE.CANDIDATE_ID = CANDIDATE_ID
BASE.EXPERIMENT_ID = EXPERIMENT_ID
BASE.RESULT = ROOT / "results" / CANDIDATE_ID
BASE.PROGRAM = ROOT / "programs" / CANDIDATE_ID
BASE.SOURCE = BASE.PROGRAM / "attention_probability_adjoint.cpp"
BASE.META = BASE.PROGRAM / "meta.json"
BASE.DESCRIPTOR = BASE.PROGRAM / "program.py"
BASE.CONTRACT = (
    ROOT
    / "operations/planning/nncp_open_top_attention_probability_adjoint_64_q0_v3.json"
)
BASE.TOOLCHAIN_CONTRACT = (
    ROOT
    / "operations/planning/nncp_open_top_attention_probability_adjoint_64_q0_v3_toolchain.json"
)
BASE.EXPERIMENT = ROOT / "operations/adaptive/experiments" / f"{EXPERIMENT_ID}.json"


def normalized_metadata(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in DERIVED_META_FIELDS}


def regular_file(path: Path, label: str) -> Path:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"{label} is not a regular non-symlink file: {path}")
    return path


def verify_adaptive_bindings() -> dict[str, Any]:
    raw_revision = os.environ.get("GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON")
    raw_experiment = os.environ.get("GAMMA_ENWIKI9_EXPERIMENT_JSON")
    snapshot_id = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID")
    snapshot_text = os.environ.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if not all((raw_revision, raw_experiment, snapshot_id, snapshot_text)):
        raise RuntimeError("revision-bound adaptive execution environment is required")

    revision = json.loads(raw_revision)
    experiment_reference = json.loads(raw_experiment)
    if revision.get("candidateId") != CANDIDATE_ID or snapshot_id != CANDIDATE_ID:
        raise RuntimeError("adaptive candidate identity mismatch")
    expected_experiment_path = BASE.EXPERIMENT.relative_to(ROOT).as_posix()
    if experiment_reference.get("path") != expected_experiment_path:
        raise RuntimeError("adaptive experiment path mismatch")
    if experiment_reference.get("sha256") != f"sha256:{BASE.sha256(BASE.EXPERIMENT)}":
        raise RuntimeError("adaptive experiment digest mismatch")

    snapshot = Path(snapshot_text).resolve(strict=True)
    sealed_source = regular_file(
        snapshot / "attention_probability_adjoint.cpp", "sealed evaluator source"
    )
    sealed_descriptor = regular_file(snapshot / "program.py", "sealed descriptor")
    sealed_meta = regular_file(snapshot / "meta.json", "sealed metadata")
    if BASE.sha256(sealed_source) != BASE.sha256(BASE.SOURCE):
        raise RuntimeError("sealed evaluator source differs from live candidate")
    if BASE.sha256(sealed_descriptor) != BASE.sha256(BASE.DESCRIPTOR):
        raise RuntimeError("sealed descriptor differs from live candidate")

    sealed_value = json.loads(sealed_meta.read_text(encoding="utf-8"))
    live_value = json.loads(BASE.META.read_text(encoding="utf-8"))
    if not isinstance(sealed_value, dict) or not isinstance(live_value, dict):
        raise RuntimeError("candidate metadata must be JSON objects")
    if sealed_value != normalized_metadata(live_value):
        raise RuntimeError("sealed semantic metadata differs from live candidate")
    return {
        "candidate_revision": revision,
        "experiment": experiment_reference,
        "snapshot_root": str(snapshot),
        "metadata_normalization": "semantic-meta-v1",
        "derived_fields_ignored": sorted(DERIVED_META_FIELDS),
    }


def source_package(path: Path, proposal: Path) -> None:
    members = {
        BASE.SOURCE,
        BASE.META,
        BASE.DESCRIPTOR,
        BASE_PATH,
        Path(__file__).resolve(),
        BASE.RESOURCE_GUARD,
        ROOT / "tools/research_contracts.py",
        ROOT / "tools/enwiki9_python_source_closure.py",
        ROOT / "contracts/research/v1/objective-contract.json",
        ROOT / "contracts/research/v1/objective-contract.schema.json",
        BASE.CONTRACT,
        BASE.TOOLCHAIN_CONTRACT,
        BASE.EXPERIMENT,
        proposal,
    }
    ordered = sorted(members, key=lambda item: str(item.relative_to(ROOT)))
    tar_path = path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for member in ordered:
            regular_file(member, "source-package member")
            info = archive.gettarinfo(
                str(member), arcname=str(member.relative_to(ROOT))
            )
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with member.open("rb") as handle:
                archive.addfile(info, handle)
    path.write_bytes(lzma.compress(tar_path.read_bytes(), preset=9 | lzma.PRESET_EXTREME))
    tar_path.unlink()
    if path.stat().st_size > BASE.SOURCE_CEILING:
        raise RuntimeError("incremental source package exceeds ceiling")


BASE.verify_adaptive_bindings = verify_adaptive_bindings
BASE.source_package = source_package


def main() -> int:
    return BASE.main()


if __name__ == "__main__":
    raise SystemExit(main())
