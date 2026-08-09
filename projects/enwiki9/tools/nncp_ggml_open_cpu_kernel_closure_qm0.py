#!/usr/bin/env python3
"""Build and certify a source-counted, CPU-only GGML optimizer closure."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_ggml_open_cpu_kernel_closure_qm0_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
GGML_REPO = Path("/home/x/src/llama.cpp")
EXPECTED_COMMIT = "f4884293809b5227d7307140a942f1bc4176a603"
EXPECTED_LICENSE_SHA256 = "94f29bbed6a22c35b992c5c6ebf0e7c92f13b836b90f36f461c9cf2f0f1d010d"
SOURCE_CEILING = 2_000_000


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)

    commit = run(["git", "rev-parse", "HEAD"], cwd=GGML_REPO).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], cwd=GGML_REPO).stdout
    license_sha = sha256(GGML_REPO / "LICENSE")
    if commit != EXPECTED_COMMIT or dirty or license_sha != EXPECTED_LICENSE_SHA256:
        raise RuntimeError("GGML source provenance mismatch")

    with tempfile.TemporaryDirectory(prefix="nncp-ggml-closure-") as tmp_name:
        tmp = Path(tmp_name)
        source = tmp / "source"
        source.mkdir()
        tar_path = tmp / "source.tar"
        tar_path.write_bytes(
            subprocess.check_output(
                ["git", "archive", "--format=tar", "HEAD", "LICENSE", "ggml"],
                cwd=GGML_REPO,
            )
        )
        run(["tar", "-xf", str(tar_path), "-C", str(source)])
        shutil.copy2(PROGRAM / "CMakeLists.txt", source / "CMakeLists.txt")
        shutil.copy2(PROGRAM / "probe.cpp", source / "probe.cpp")

        source_package = RESULT / "ggml_source_closure.tar.xz"
        run(
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
        configure = run(
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
        build_result = run(
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
        first = run([str(binary)], cwd=tmp, env=clean_env)
        second = run([str(binary)], cwd=tmp, env=clean_env)
        if first.stdout != second.stdout:
            raise RuntimeError("fresh-process probe output is not byte-identical")
        lines = dict(line.split("=", 1) for line in first.stdout.strip().splitlines())
        if set(lines) != {"weights", "grad"}:
            raise RuntimeError("probe output schema mismatch")
        if not all(lines[name] and len(lines[name]) % 8 == 0 for name in lines):
            raise RuntimeError("probe tensor output encoding mismatch")

        ldd = run(["ldd", str(binary)]).stdout
        forbidden = [
            line
            for line in ldd.splitlines()
            if "ggml" in line.lower()
            or "cuda" in line.lower()
            or "opencl" in line.lower()
        ]
        source_bytes = source_package.stat().st_size
        decision = {
            "schema": "enwiki9_nncp_ggml_open_cpu_kernel_closure_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epistemic_tier": "zero_credit_substrate_feasibility",
            "score_credit_bytes": 0,
            "ggml_commit": commit,
            "ggml_license": "MIT",
            "ggml_license_sha256": license_sha,
            "source_tree_clean": not bool(dirty),
            "source_package_bytes": source_bytes,
            "source_package_sha256": sha256(source_package),
            "source_ceiling_bytes": SOURCE_CEILING,
            "source_ceiling_pass": source_bytes <= SOURCE_CEILING,
            "probe_binary_bytes": binary.stat().st_size,
            "probe_binary_sha256": sha256(binary),
            "probe_output": first.stdout.strip(),
            "repeat_output_identical": first.stdout == second.stdout,
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
