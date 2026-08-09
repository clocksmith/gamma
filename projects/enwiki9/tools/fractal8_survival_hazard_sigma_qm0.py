#!/usr/bin/env python3
"""Build and execute the frozen FRACTAL-8 survival-hazard screen."""

from __future__ import annotations

import hashlib
import json
import lzma
from pathlib import Path
import resource
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fractal8_survival_hazard_sigma_qm0_v1"
PARENT_ID = "fractal7_endpoint_sigma_latent_qm0_v1"
CPP_PATH = ROOT / "tools/fractal8_survival_hazard_sigma_qm0.cpp"
STORE_PATH = Path(
    "/home/x/enwiki9-nonproof/results/fx2_order_original_10m.store"
)
P1_PATH = ROOT / "results/fractal2_endpoint428_trace_10m_v1/endpoint428.p1"
PARENT_DECISION = ROOT / f"results/{PARENT_ID}/decision.json"
SOURCE_LIMIT_BYTES = 65_536
EXPECTED_SHA256 = {
    "store": "867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b",
    "p1": "b292ac9b7cf37beafd345a735374162f2a915c4ad2a3d3520755ceb086bada9e",
    "parent_decision": "dd707e7ffbbc22944e280403e21a0d92860b156325bf5d2832cd76d1fea3bdc2",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    output_dir = ROOT / "results" / CANDIDATE_ID
    if output_dir.exists():
        raise SystemExit(
            f"refusing to replace existing output directory: {output_dir}"
        )

    actual_sha256 = {
        "store": sha256_file(STORE_PATH),
        "p1": sha256_file(P1_PATH),
        "parent_decision": sha256_file(PARENT_DECISION),
    }
    if actual_sha256 != EXPECTED_SHA256:
        raise ValueError("FRACTAL-8 antecedent or input identity mismatch")
    parent = json.loads(PARENT_DECISION.read_text())
    if parent.get("schema") != PARENT_ID:
        raise ValueError("FRACTAL-7 parent schema mismatch")
    if parent.get("arms", {}).get("SIGMA", {}).get(
        "free_selector_ceiling_bytes", 0
    ) < 100_000:
        raise ValueError("FRACTAL-7 parent lacks the required hindsight reservoir")

    output_dir.mkdir(parents=True)
    binary_path = output_dir / CANDIDATE_ID
    compile_command = [
        "g++",
        "-std=c++20",
        "-O3",
        "-DNDEBUG",
        "-o",
        str(binary_path),
        str(CPP_PATH),
    ]
    compiler = subprocess.run(
        ["g++", "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    subprocess.run(compile_command, check=True, cwd=ROOT)
    run = subprocess.run(
        [str(binary_path), str(STORE_PATH), str(P1_PATH)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    (output_dir / "stdout.log").write_text(run.stdout)
    (output_dir / "stderr.log").write_text(run.stderr)
    decision = json.loads(run.stdout)
    if decision.get("schema") != CANDIDATE_ID:
        raise ValueError("compiled screen emitted the wrong schema")
    scope = decision.get("scope", {})
    if scope != {
        "wrt_stream_bytes": 6_251_852,
        "wrt_events": 5_139_821,
        "p1_rows": 50_014_816,
    }:
        raise ValueError("compiled screen consumed the wrong exact population")
    gates = decision.get("gates", {})
    required_gates = {
        "sigma_ceiling_at_least_100000",
        "sigma_causal_gain_at_least_75000",
        "all_chronological_thirds_positive",
        "passed",
    }
    if not required_gates.issubset(gates):
        raise ValueError("compiled screen omitted frozen decision gates")

    source_paths = (
        Path(__file__),
        CPP_PATH,
        ROOT / "docs/fractal8_survival_hazard_sigma_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/program.py",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
        ROOT
        / f"operations/adaptive/proposals/developed/000_{CANDIDATE_ID}.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(
        source_blob, preset=9 | lzma.PRESET_EXTREME
    )
    source_path = output_dir / "diagnostic_source_package.lzma"
    source_path.write_bytes(source_package)

    decision.update(
        {
            "candidate_id": CANDIDATE_ID,
            "parent_candidate_id": PARENT_ID,
            "inputs": {
                "store": {
                    "path": str(STORE_PATH),
                    "bytes": STORE_PATH.stat().st_size,
                    "sha256": actual_sha256["store"],
                },
                "endpoint428_p1": {
                    "path": str(P1_PATH.relative_to(ROOT)),
                    "bytes": P1_PATH.stat().st_size,
                    "sha256": actual_sha256["p1"],
                },
                "parent_decision": {
                    "path": str(PARENT_DECISION.relative_to(ROOT)),
                    "sha256": actual_sha256["parent_decision"],
                },
            },
            "build": {
                "compiler": compiler,
                "command": compile_command,
                "cpp_sha256": sha256_file(CPP_PATH),
                "driver_sha256": sha256_file(Path(__file__)),
                "binary_bytes": binary_path.stat().st_size,
                "binary_sha256": sha256_file(binary_path),
            },
            "artifacts": {
                "diagnostic_source_package": {
                    "path": str(source_path.relative_to(ROOT)),
                    "bytes": len(source_package),
                    "sha256": sha256_file(source_path),
                    "limit_bytes": SOURCE_LIMIT_BYTES,
                }
            },
            "conditions": {
                "compiled_screen_completed": True,
                "source_at_most_65536": len(source_package)
                <= SOURCE_LIMIT_BYTES,
                "frozen_scientific_gates_passed": bool(gates["passed"]),
            },
            "decision": {
                "promotion_authorized": False,
                "paid_codec_authorized": bool(gates["passed"]),
                "verified_full_1g_score_bytes": None,
                "forecast_bytes": 109_389_323,
            },
            "resource": {
                "driver_max_rss_kib": resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss,
                "child_max_rss_kib": resource.getrusage(
                    resource.RUSAGE_CHILDREN
                ).ru_maxrss,
            },
        }
    )
    decision_path = output_dir / "decision.json"
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "causal_gain_bytes": decision["arms"]["SIGMA_HAZARD"][
                    "causal_gain_bytes"
                ],
                "control_margin_bytes": gates[
                    "minimum_causal_control_margin_bytes"
                ],
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
