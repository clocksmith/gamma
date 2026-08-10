#!/usr/bin/env python3
"""Audit cmix-obias tracked-source and static runtime closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_runtime_closure_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
DONOR = Path("/home/x/enwiki9-nonproof/cmix-obias-donor")
SOURCE = DONOR / "cmix-obias"
Q2 = ROOT / "results/cmix_obias_source_1m_roundtrip_qm2_v1"
Q3 = ROOT / "results/cmix_obias_source_1m_roundtrip_qm3_v1"
EXPECTED_OUTER_COMMIT = "51488a0c1228dbeab7c1be837fc90ceaed351728"
EXPECTED_SOURCE_TREE = "23de249ff899db5ba84dd3514a6a1bb52a83d0f5"
EXPECTED_LICENSE = "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986"
EXPECTED_PROFILE = "5141320933c09c4fd24d7f332da67b1008a3e730dd09c8784ea36769f2fe1e52"
EXPECTED_HEAD = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"
EXPECTED_COMPRESSOR = "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a"
EXPECTED_OPENING_ARCHIVE = "9065eaf54f81e441598fd53c39f909db49d6a9627ae0456eabb8c77099b8ccc4"
REQUIRED_TRACKED = (
    "BUILD.md",
    "MANIFEST.txt",
    "README.md",
    "SUBMISSION.md",
    "cmix-obias/LICENSE",
    "cmix-obias/makefile",
    "cmix-obias/dictionary/english.dic",
    "cmix-obias/models/bitlstm32/refit_golden256_fp16.blob",
    "cmix-obias/pgo_data_asbuilt/default.profdata",
    "cmix-obias/src/runner.cpp",
    "cmix-obias/src/predictor.cpp",
    "cmix-obias/src/preprocess/preprocessor.cpp",
    "cmix-obias/src/readalike_prepr/data/new_article_order",
    "make_archive9.sh",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def command(args: list[str], *, cwd: Path | None = None) -> dict[str, object]:
    completed = subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode(errors="replace"),
        "stderr": completed.stderr.decode(errors="replace"),
    }


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    required_paths = [DONOR / path for path in REQUIRED_TRACKED]
    required_paths.extend(
        [Q2 / "decision.json", Q3 / "decision.json", Q2 / "cmix", Q3 / "cmix", Q3 / "archive9"]
    )
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing source-closure inputs: {missing}")

    outer_commit = command(["git", "rev-parse", "HEAD"], cwd=DONOR)
    source_tree = command(["git", "rev-parse", "HEAD:cmix-obias"], cwd=DONOR)
    tracked_status = command(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=DONOR
    )
    untracked_status = command(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=DONOR
    )
    outer_listing = command(
        ["git", "ls-tree", "-r", "--full-tree", "HEAD"], cwd=DONOR
    )
    source_listing = command(
        ["git", "ls-tree", "-r", "--full-tree", "HEAD:cmix-obias"], cwd=DONOR
    )
    outer_lines = [line for line in outer_listing["stdout"].splitlines() if line]
    source_lines = [line for line in source_listing["stdout"].splitlines() if line]
    tracked_paths = {line.split("\t", 1)[1] for line in outer_lines}

    license_path = SOURCE / "LICENSE"
    license_text = license_path.read_text(errors="replace")
    profile_path = SOURCE / "pgo_data_asbuilt/default.profdata"
    head_path = SOURCE / "models/bitlstm32/refit_golden256_fp16.blob"
    q2_decision = load_json(Q2 / "decision.json")
    q3_decision = load_json(Q3 / "decision.json")
    q2_binary = Q2 / "cmix"
    q3_binary = Q3 / "cmix"
    q3_archive = Q3 / "archive9"
    binary_probes: dict[str, object] = {}
    static_pass = True
    for name, path in (("q2_compressor", q2_binary), ("q3_compressor", q3_binary), ("q3_archive", q3_archive)):
        file_probe = command(["file", str(path)])
        ldd_probe = command(["ldd", str(path)])
        is_static = (
            "statically linked" in file_probe["stdout"]
            and "not a dynamic executable" in (ldd_probe["stdout"] + ldd_probe["stderr"])
        )
        static_pass = static_pass and is_static
        binary_probes[name] = {
            "artifact": artifact(path),
            "file": file_probe,
            "ldd": ldd_probe,
            "static_runtime": is_static,
        }

    build_identity = q3_decision.get("independent_clean_build_identity", {})
    gates = {
        "outer_commit_exact": outer_commit["stdout"].strip() == EXPECTED_OUTER_COMMIT,
        "source_tree_exact": source_tree["stdout"].strip() == EXPECTED_SOURCE_TREE,
        "tracked_tree_clean": tracked_status["stdout"] == "",
        "outer_tracked_file_count_127": len(outer_lines) == 127,
        "source_tracked_file_count_115": len(source_lines) == 115,
        "required_paths_tracked": all(path in tracked_paths for path in REQUIRED_TRACKED),
        "gpl3_license_exact": (
            sha256(license_path) == EXPECTED_LICENSE
            and "GNU GENERAL PUBLIC LICENSE" in license_text
            and "Version 3, 29 June 2007" in license_text
        ),
        "pgo_profile_materialized_exact": sha256(profile_path) == EXPECTED_PROFILE,
        "head_materialized_exact": sha256(head_path) == EXPECTED_HEAD,
        "two_clean_builds_identical": build_identity.get("all_artifacts_byte_identical") is True,
        "q2_q3_program_identity": (
            sha256(q2_binary) == sha256(q3_binary) == EXPECTED_COMPRESSOR
        ),
        "opening_archive_identity": sha256(q3_archive) == EXPECTED_OPENING_ARCHIVE,
        "opening_roundtrip_exact": (
            q2_decision.get("integrity", {}).get("raw_roundtrip_exact") is True
            and q3_decision.get("integrity", {}).get("raw_roundtrip_exact") is True
        ),
        "empty_environment_inverse_exact": (
            q2_decision.get("integrity", {}).get("bare_environment") == {}
            and q3_decision.get("integrity", {}).get("bare_environment") == {}
        ),
        "static_runtime_closure": static_pass,
    }
    failed = [name for name, passed in gates.items() if not passed]
    decision = {
        "schema": "enwiki9_cmix_obias_source_runtime_closure_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "claim_boundary": (
            "Technical tracked-source, license, build-asset, reproducible-build, "
            "and static runtime closure. It is not legal advice, committee acceptance, "
            "isolated official timing, full-corpus score, or 105M evidence."
        ),
        "score_credit_bytes": 0,
        "source": {
            "outer_commit": outer_commit["stdout"].strip(),
            "source_tree": source_tree["stdout"].strip(),
            "outer_tracked_files": len(outer_lines),
            "source_tracked_files": len(source_lines),
            "outer_listing_sha256": hashlib.sha256(outer_listing["stdout"].encode()).hexdigest(),
            "source_listing_sha256": hashlib.sha256(source_listing["stdout"].encode()).hexdigest(),
            "tracked_status": tracked_status,
            "untracked_build_tools_recorded": untracked_status["stdout"].splitlines(),
            "license": artifact(license_path),
            "profile": artifact(profile_path),
            "head": artifact(head_path),
        },
        "runtime": binary_probes,
        "antecedents": {
            "q2_decision": artifact(Q2 / "decision.json"),
            "q3_decision": artifact(Q3 / "decision.json"),
        },
        "gates": gates,
        "failed_conditions": failed,
        "official_source_eligibility_proven": False,
        "overall_pass": not failed,
        "verdict": (
            "technical_source_and_static_runtime_closure_verified_official_eligibility_remains"
            if not failed
            else "source_or_runtime_closure_rejected"
        ),
    }
    RESULT.mkdir(parents=True)
    write_json(RESULT / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
