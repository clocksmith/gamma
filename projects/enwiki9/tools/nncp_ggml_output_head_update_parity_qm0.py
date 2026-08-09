#!/usr/bin/env python3
"""Certify GGML output-head gradient and first-update parity to LibNC."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

import numpy as np

import nncp_ggml_open_cpu_kernel_closure_qm0 as common


CANDIDATE_ID = "nncp_ggml_output_head_update_parity_qm0_v1"
PROGRAM = common.ROOT / "programs" / CANDIDATE_ID
RESULT = common.ROOT / "results" / CANDIDATE_ID
INITIAL = Path(
    "/home/x/enwiki9-nonproof/results/nncp_v33_relative_parity_v1/run_05/export"
)
BOUND = Path(
    "/home/x/enwiki9-nonproof/results/nncp_v33_online_update_parity_v1/run_07_bound"
)
TRACE = BOUND / "teacher.bin"
GRADIENT_WEIGHTS = BOUND / "gradients/unknown_0000.bin"
GRADIENT_BIAS = BOUND / "gradients/unknown_0017.bin"
FINAL = BOUND / "final_export"
EXPECTED = {
    TRACE: "cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4",
    INITIAL / "manifest.json": "6947405fd472b7401fe3460b037bfc17a788c04582ff5215b21f4821621104cd",
    INITIAL / "00016.bin": "046679838fb9b29d39b4ff26ef3644dbdbf17648887ab100e0bf2f82241da5eb",
    INITIAL / "00017.bin": "5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef",
    GRADIENT_WEIGHTS: "80f76b36533ea232a9715fc457210a28c92b4e177d88f02b9c335ffa6e0d302f",
    GRADIENT_BIAS: "dbf31431581356f26edee7532b0154452cd7e3018813fcf393cca2a039133b56",
    FINAL / "00016.bin": "8adc102b42286e7943f3b9730ec8d49ddb879d288c9302111104aed596f21299",
    FINAL / "00017.bin": "fdd9f52248b0c3f38b04ffa1d4d04c69f3e94a6d4318b8133fe31b386c7cba59",
}
TRACE_HEADER = struct.Struct("<8sQ")
TRACE_ROW = struct.Struct("<QQQQIHHI")
GRADIENT_TOLERANCE = 2.0e-6
UPDATE_TOLERANCE = 2.0e-5


def load_trace(path: Path) -> tuple[np.ndarray, np.ndarray]:
    symbols: list[int] = []
    distributions: list[np.ndarray] = []
    with path.open("rb") as source:
        magic, rows = TRACE_HEADER.unpack(source.read(TRACE_HEADER.size))
        if magic != b"NNTCHD2\0" or rows != 4:
            raise ValueError("unexpected bound teacher trace")
        for index in range(rows):
            fixed = TRACE_ROW.unpack(source.read(TRACE_ROW.size))
            if fixed[1] != index or fixed[-1] != 256:
                raise ValueError("invalid bound teacher row")
            distributions.append(
                np.frombuffer(source.read(4 * fixed[-1]), dtype="<f4").copy()
            )
            symbols.append(fixed[-2])
        if source.read(1):
            raise ValueError("trailing teacher bytes")
    return np.asarray(symbols, dtype=np.int64), np.stack(distributions)


def load_matrix(path: Path) -> np.ndarray:
    return np.fromfile(path, dtype="<f4").reshape((256, 32), order="F").copy()


def comparison(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    difference = candidate.astype(np.float64) - reference.astype(np.float64)
    return {
        "elements": int(reference.size),
        "maximum_absolute_error": float(np.abs(difference).max()),
        "mean_absolute_error": float(np.abs(difference).mean()),
        "sign_mismatches": int(np.count_nonzero(np.signbit(reference) != np.signbit(candidate))),
    }


def aggregate(directory: Path) -> str:
    digest = hashlib.sha256()
    for name in (
        "gradient_weights.bin",
        "gradient_bias.bin",
        "updated_weights.bin",
        "updated_bias.bin",
        "loss.txt",
    ):
        digest.update(name.encode() + b"\0")
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)
    for path, expected in EXPECTED.items():
        if not path.is_file() or common.sha256(path) != expected:
            raise ValueError(f"fixture identity mismatch: {path}")
    commit = common.run(
        ["git", "rev-parse", "HEAD"], cwd=common.GGML_REPO
    ).stdout.strip()
    dirty = common.run(
        ["git", "status", "--porcelain"], cwd=common.GGML_REPO
    ).stdout
    if commit != common.EXPECTED_COMMIT or dirty:
        raise ValueError("GGML source identity mismatch")

    symbols, probabilities = load_trace(TRACE)
    residual = probabilities.copy()
    residual[np.arange(4), symbols] -= 1.0
    expected_gradient_weights = load_matrix(GRADIENT_WEIGHTS)
    expected_gradient_bias = np.fromfile(GRADIENT_BIAS, dtype="<f4")
    hidden = np.linalg.lstsq(
        residual.T.astype(np.float64),
        (4.0 * expected_gradient_weights).astype(np.float64),
        rcond=None,
    )[0].astype("<f4")
    reconstructed = residual.T @ hidden / 4.0
    hidden_reconstruction = comparison(expected_gradient_weights, reconstructed)
    bias_identity = comparison(expected_gradient_bias, residual.mean(axis=0))
    if (
        hidden_reconstruction["maximum_absolute_error"] > GRADIENT_TOLERANCE
        or bias_identity["maximum_absolute_error"] > GRADIENT_TOLERANCE
    ):
        raise ValueError("bound head fixture is not reconstructible")

    initial_weights = load_matrix(INITIAL / "00016.bin")
    initial_bias = np.fromfile(INITIAL / "00017.bin", dtype="<f4")
    expected_final_weights = load_matrix(FINAL / "00016.bin")
    expected_final_bias = np.fromfile(FINAL / "00017.bin", dtype="<f4")
    labels = np.zeros((4, 256), dtype="<f4")
    labels[np.arange(4), symbols] = 1.0

    with tempfile.TemporaryDirectory(prefix="nncp-ggml-head-") as tmp_name:
        tmp = Path(tmp_name)
        fixture = tmp / "fixture"
        fixture.mkdir()
        hidden.astype("<f4").tofile(fixture / "hidden.bin")
        initial_weights.astype("<f4").tofile(fixture / "weights.bin")
        initial_bias.astype("<f4").tofile(fixture / "bias.bin")
        labels.tofile(fixture / "labels.bin")
        expected_gradient_weights.astype("<f4").tofile(
            fixture / "expected_gradient_weights.bin"
        )
        expected_gradient_bias.astype("<f4").tofile(
            fixture / "expected_gradient_bias.bin"
        )
        expected_final_weights.astype("<f4").tofile(
            fixture / "expected_final_weights.bin"
        )
        expected_final_bias.astype("<f4").tofile(
            fixture / "expected_final_bias.bin"
        )

        fixture_package = RESULT / "bound_head_fixture.tar.xz"
        common.run(
            [
                "tar", "--sort=name", "--mtime=@0", "--owner=0", "--group=0",
                "--numeric-owner", "-cJf", str(fixture_package), "-C", str(fixture), ".",
            ]
        )

        source = tmp / "source"
        source.mkdir()
        source_tar = tmp / "source.tar"
        source_tar.write_bytes(
            subprocess.check_output(
                ["git", "archive", "--format=tar", "HEAD", "LICENSE", "ggml"],
                cwd=common.GGML_REPO,
            )
        )
        common.run(["tar", "-xf", str(source_tar), "-C", str(source)])
        shutil.copy2(PROGRAM / "CMakeLists.txt", source / "CMakeLists.txt")
        shutil.copy2(PROGRAM / "probe.cpp", source / "probe.cpp")
        source_package = RESULT / "ggml_head_source_closure.tar.xz"
        common.run(
            [
                "tar", "--sort=name", "--mtime=@0", "--owner=0", "--group=0",
                "--numeric-owner", "-cJf", str(source_package), "-C", str(source), ".",
            ]
        )

        build = tmp / "build"
        common.run(
            [
                "cmake", "-S", str(source), "-B", str(build),
                "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                "-DGGML_NATIVE=OFF", "-DGGML_OPENMP=OFF", "-DGGML_BLAS=OFF",
                "-DGGML_LLAMAFILE=OFF", "-DGGML_CCACHE=OFF",
            ]
        )
        common.run(
            ["cmake", "--build", str(build), "--target", "nncp_ggml_head_probe", "-j4"]
        )
        binaries = [path for path in build.rglob("nncp_ggml_head_probe") if path.is_file()]
        if len(binaries) != 1:
            raise RuntimeError("head probe binary not uniquely located")
        binary = binaries[0]
        run_a = tmp / "run_a"
        run_b = tmp / "run_b"
        clean_env = {"HOME": str(tmp / "home"), "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"}
        Path(clean_env["HOME"]).mkdir()
        common.run([str(binary), str(fixture), str(run_a)], cwd=tmp, env=clean_env)
        common.run([str(binary), str(fixture), str(run_b)], cwd=tmp, env=clean_env)
        repeat_identity = aggregate(run_a) == aggregate(run_b)

        observed_gradient_weights = np.fromfile(
            run_a / "gradient_weights.bin", dtype="<f4"
        ).reshape((256, 32))
        observed_gradient_bias = np.fromfile(run_a / "gradient_bias.bin", dtype="<f4")
        observed_final_weights = np.fromfile(
            run_a / "updated_weights.bin", dtype="<f4"
        ).reshape((256, 32))
        observed_final_bias = np.fromfile(run_a / "updated_bias.bin", dtype="<f4")
        gradient_weights_comparison = comparison(
            expected_gradient_weights, observed_gradient_weights
        )
        gradient_bias_comparison = comparison(expected_gradient_bias, observed_gradient_bias)
        final_weights_comparison = comparison(expected_final_weights, observed_final_weights)
        final_bias_comparison = comparison(expected_final_bias, observed_final_bias)
        ldd = common.run(["ldd", str(binary)]).stdout
        forbidden = [
            line for line in ldd.splitlines()
            if "ggml" in line.lower() or "cuda" in line.lower() or "opencl" in line.lower()
        ]
        source_bytes = source_package.stat().st_size
        gradient_pass = all(
            item["maximum_absolute_error"] <= GRADIENT_TOLERANCE
            and item["sign_mismatches"] == 0
            for item in (gradient_weights_comparison, gradient_bias_comparison)
        )
        update_pass = all(
            item["maximum_absolute_error"] <= UPDATE_TOLERANCE
            for item in (final_weights_comparison, final_bias_comparison)
        )
        decision = {
            "schema": "enwiki9_nncp_ggml_output_head_update_parity_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epistemic_tier": "zero_credit_open_head_parity",
            "score_credit_bytes": 0,
            "ggml_commit": commit,
            "fixture_input_sha256": {str(path): expected for path, expected in EXPECTED.items()},
            "fixture_package_bytes": fixture_package.stat().st_size,
            "fixture_package_sha256": common.sha256(fixture_package),
            "hidden_reconstruction": hidden_reconstruction,
            "bias_fixture_identity": bias_identity,
            "gradient_weights": gradient_weights_comparison,
            "gradient_bias": gradient_bias_comparison,
            "final_weights": final_weights_comparison,
            "final_bias": final_bias_comparison,
            "gradient_pass": gradient_pass,
            "update_pass": update_pass,
            "repeat_output_identical": repeat_identity,
            "run_aggregate_sha256": aggregate(run_a),
            "source_package_bytes": source_bytes,
            "source_package_sha256": common.sha256(source_package),
            "source_ceiling_bytes": common.SOURCE_CEILING,
            "source_ceiling_pass": source_bytes <= common.SOURCE_CEILING,
            "probe_binary_bytes": binary.stat().st_size,
            "probe_binary_sha256": common.sha256(binary),
            "forbidden_dynamic_dependencies": forbidden,
            "dynamic_dependency_pass": not forbidden,
            "loss": (run_a / "loss.txt").read_text().strip(),
        }
        decision["overall_pass"] = all(
            [gradient_pass, update_pass, repeat_identity, decision["source_ceiling_pass"], decision["dynamic_dependency_pass"]]
        )
        (RESULT / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
        (RESULT / "probe.ldd.txt").write_text(ldd)

    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
