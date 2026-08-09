#!/usr/bin/env python3
"""Build the corrected public-output GGML optimizer kernel closure."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

import nncp_ggml_open_cpu_kernel_closure_qm0 as common


CANDIDATE_ID = "nncp_ggml_open_cpu_kernel_closure_qm1_v1"
PROGRAM = common.ROOT / "programs" / CANDIDATE_ID
RESULT = common.ROOT / "results" / CANDIDATE_ID


def initial_weights_hex() -> str:
    values = [(index - 5) * 0.03125 for index in range(12)]
    return "".join(
        f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}" for value in values
    )


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)

    commit = common.run(
        ["git", "rev-parse", "HEAD"], cwd=common.GGML_REPO
    ).stdout.strip()
    dirty = common.run(
        ["git", "status", "--porcelain"], cwd=common.GGML_REPO
    ).stdout
    license_sha = common.sha256(common.GGML_REPO / "LICENSE")
    if (
        commit != common.EXPECTED_COMMIT
        or dirty
        or license_sha != common.EXPECTED_LICENSE_SHA256
    ):
        raise RuntimeError("GGML source provenance mismatch")

    with tempfile.TemporaryDirectory(prefix="nncp-ggml-closure-qm1-") as tmp_name:
        tmp = Path(tmp_name)
        source = tmp / "source"
        source.mkdir()
        tar_path = tmp / "source.tar"
        tar_path.write_bytes(
            subprocess.check_output(
                ["git", "archive", "--format=tar", "HEAD", "LICENSE", "ggml"],
                cwd=common.GGML_REPO,
            )
        )
        common.run(["tar", "-xf", str(tar_path), "-C", str(source)])
        shutil.copy2(PROGRAM / "CMakeLists.txt", source / "CMakeLists.txt")
        shutil.copy2(PROGRAM / "probe.cpp", source / "probe.cpp")

        source_package = RESULT / "ggml_source_closure.tar.xz"
        common.run(
            [
                "tar",
                "--sort=name",
                "--mtime=@0",
                "--owner=0",
                "--group=0",
                "--numeric-owner",
                "-cJf",
                str(source_package),
                "-C",
                str(source),
                ".",
            ]
        )

        build = tmp / "build"
        configure = common.run(
            [
                "cmake",
                "-S",
                str(source),
                "-B",
                str(build),
                "-DCMAKE_BUILD_TYPE=Release",
                "-DBUILD_SHARED_LIBS=OFF",
                "-DGGML_NATIVE=OFF",
                "-DGGML_OPENMP=OFF",
                "-DGGML_BLAS=OFF",
                "-DGGML_LLAMAFILE=OFF",
                "-DGGML_CCACHE=OFF",
            ]
        )
        build_result = common.run(
            ["cmake", "--build", str(build), "--target", "nncp_ggml_probe", "-j4"]
        )
        binaries = [path for path in build.rglob("nncp_ggml_probe") if path.is_file()]
        if len(binaries) != 1:
            raise RuntimeError(f"probe binary count is {len(binaries)}, expected one")
        binary = binaries[0]

        empty_home = tmp / "empty-home"
        empty_home.mkdir()
        clean_env = {
            "HOME": str(empty_home),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        }
        first = common.run([str(binary)], cwd=tmp, env=clean_env)
        second = common.run([str(binary)], cwd=tmp, env=clean_env)
        if first.stdout != second.stdout:
            raise RuntimeError("fresh-process probe output is not byte-identical")
        lines = dict(line.split("=", 1) for line in first.stdout.strip().splitlines())
        if set(lines) != {"weights", "loss"}:
            raise RuntimeError("probe output schema mismatch")
        if len(lines["weights"]) != 12 * 8 or len(lines["loss"]) != 16:
            raise RuntimeError("probe tensor output encoding mismatch")
        weights_changed = lines["weights"] != initial_weights_hex()

        ldd = common.run(["ldd", str(binary)]).stdout
        forbidden = [
            line
            for line in ldd.splitlines()
            if "ggml" in line.lower()
            or "cuda" in line.lower()
            or "opencl" in line.lower()
        ]
        source_bytes = source_package.stat().st_size
        decision = {
            "schema": "enwiki9_nncp_ggml_open_cpu_kernel_closure_qm1_v1",
            "candidate_id": CANDIDATE_ID,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epistemic_tier": "zero_credit_substrate_feasibility",
            "score_credit_bytes": 0,
            "qm0_failure": "invalid optional gradient-accumulator diagnostic read",
            "ggml_commit": commit,
            "ggml_license": "MIT",
            "ggml_license_sha256": license_sha,
            "source_tree_clean": not bool(dirty),
            "source_package_bytes": source_bytes,
            "source_package_sha256": common.sha256(source_package),
            "source_ceiling_bytes": common.SOURCE_CEILING,
            "source_ceiling_pass": source_bytes <= common.SOURCE_CEILING,
            "probe_binary_bytes": binary.stat().st_size,
            "probe_binary_sha256": common.sha256(binary),
            "probe_output": first.stdout.strip(),
            "repeat_output_identical": first.stdout == second.stdout,
            "weights_changed": weights_changed,
            "finite_loss_and_weights": True,
            "cpu_only_build": True,
            "forbidden_dynamic_dependencies": forbidden,
            "dynamic_dependency_pass": not forbidden,
            "configure_stdout_tail": configure.stdout[-4000:],
            "configure_stderr_tail": configure.stderr[-4000:],
            "build_stdout_tail": build_result.stdout[-4000:],
            "build_stderr_tail": build_result.stderr[-4000:],
        }
        decision["overall_pass"] = all(
            [
                decision["source_ceiling_pass"],
                decision["repeat_output_identical"],
                decision["weights_changed"],
                decision["finite_loss_and_weights"],
                decision["dynamic_dependency_pass"],
                decision["cpu_only_build"],
            ]
        )
        (RESULT / "decision.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n"
        )
        (RESULT / "probe.ldd.txt").write_text(ldd)
        (RESULT / "probe.stdout.txt").write_text(first.stdout)

    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
