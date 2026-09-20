"""Explicit synthetic CPU/native diagnostic; no corpus, fitting or installations.

Run with the existing CPU torch runtime and PYTHONPATH=projects/enwiki9/src.
The output directory must be new. This measures differences rather than imposing
an invented tolerance on two implementations with different FP32 arithmetic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from gamma_enwiki9.adapters.fx2_title_native import adapt
from gamma_enwiki9.adapters.fx2_training_reference import materialize, load_package, load_model


ROOT = Path(__file__).resolve().parents[1]


def identity(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def run(output: Path):
    import numpy as np
    import torch

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    source_zip = ROOT / "results/fx2_expert_release250k_v3/P-source.zip"
    fixture = ROOT / "tests/fx2_title_model_fixture.cpp"
    members, adaptation = adapt(source_zip, ROOT / "lib")
    upstream = ROOT / "external/fx2-cmix-transformer-v1"
    pairs = {
        "P": (upstream / "models/6m-q4-fp32.tch", upstream / "models/6m-q4-fp32.tfwc2"),
        "E": (ROOT / "results/fx2_entropy_train250k_q0_v2/native/E/checkpoint.tch",
              ROOT / "results/fx2_entropy_train250k_q0_v2/native/E/weights.tfwc2"),
    }
    zero = ROOT / "results/fx2_title_train250k_q0_v1/native/K/weights.tfwc2"
    report = {
        "schema": "gamma.enwiki9.fx2-synthetic-reference-diagnostic.v1",
        "scope": "eight synthetic tokens; no corpus, training, archive or score",
        "inputs": [identity(source_zip), identity(fixture), identity(Path(__file__)),
                   identity(zero), *[identity(p) for pair in pairs.values() for p in pair]],
        "tokens": list(range(8)), "prior_binary16_bits": "0x1cff",
        "prior_geometry": [8, 205], "reset": "begin_article before token zero",
        "native_adaptation": adaptation,
        "adapted_sources": {name: hashlib.sha256(data).hexdigest() for name, data in members.items()},
        "torch": torch.__version__, "device": "cpu", "torch_threads": 1,
        "arms": {}, "objective_credit_bytes": 0,
        "limitations": ["No tolerance or prediction parity is assumed.",
                        "Block differences localize the first observed drift; they do not establish its cause.",
                        "Native finite archives remain required for every trained checkpoint."],
    }
    with tempfile.TemporaryDirectory(prefix="gamma-fx2-synthetic-") as temporary:
        workspace = Path(temporary)
        native = workspace / "native"
        for name, data in members.items():
            path = native / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        infer = native / "cpp_infer/src"
        model_path = infer / "opt/model_opt.cpp"
        original = model_path.read_text()
        anchor = "      mlp_block(l);\n      if (l < 6) {"
        if original.count(anchor) != 1:
            raise ValueError("ambiguous synthetic block capture anchor")
        block_path = workspace / "blocks.f32"
        replacement = """      mlp_block(l);
      static FILE* gamma_debug = std::fopen(%s, "wb");
      if (!gamma_debug || std::fwrite(x, sizeof(float), D, gamma_debug) != D) std::abort();
      std::fflush(gamma_debug);
      if (l < 6) {""" % json.dumps(str(block_path))
        instrumented = original.replace(anchor, replacement)
        model_path.write_text(instrumented)
        report["block_capture"] = {
            "path": "cpp_infer/src/opt/model_opt.cpp", "anchor": anchor,
            "replacement_template": replacement.replace(str(block_path), "${WORKSPACE}/blocks.f32"),
            "preimage_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "postimage_sha256": hashlib.sha256(instrumented.encode()).hexdigest(),
        }
        sources = [infer / "weights_io.cpp", infer / "weights_io_compressed.cpp",
                   *[infer / "opt" / (name + ".cpp") for name in
                     ("qmat_dense", "qmat_sparse", "attn", "kda", "glue", "arena_build", "model_opt")]]
        binary = workspace / "fixture"
        command = ["/usr/bin/g++", "-std=c++17", "-O3", "-march=x86-64-v3",
                   "-mrecip=none", "-fno-math-errno", "-I", str(native),
                   str(fixture), *map(str, sources), "-o", str(binary)]
        report["compiler_version"] = subprocess.check_output([command[0], "--version"], text=True).splitlines()[0]
        report["compile_command_template"] = [s.replace(str(workspace), "${WORKSPACE}") for s in command]
        subprocess.run(command, check=True, timeout=120)
        report["native_binary_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        for arm, (checkpoint, packed) in pairs.items():
            # One base model per process keeps block capture geometry unambiguous.
            raw = subprocess.check_output([str(binary), str(packed)], timeout=30)
            native_logits = np.frombuffer(raw, dtype="<f4").copy().reshape(8, 205)
            native_blocks = np.fromfile(block_path, dtype="<f4").reshape(8, 12, 192)
            reference = workspace / (arm + "-reference")
            report.setdefault("reference_adaptation", {})[arm] = materialize(upstream, reference)
            model = load_model(load_package(reference), checkpoint)
            recorded = {}
            for number, block in enumerate(model.blocks):
                block.register_forward_hook(
                    lambda module, args, result, number=number:
                    recorded.__setitem__(number, result.detach().numpy().copy()[0]))
            prior = np.array([0x1cff], dtype=np.uint16).view(np.float16).astype(np.float32).item()
            with torch.no_grad():
                cpu_logits = model.compute_logits(torch.arange(8).reshape(1, 8),
                    torch.full((1, 8, 205), prior), torch.tensor([[0, 8]], dtype=torch.int32))[0]
            cpu_blocks = np.stack([recorded[i] for i in range(12)], axis=1)
            other = torch.from_numpy(native_logits)
            difference = (other - cpu_logits).abs()
            report["arms"][arm] = {
                "max_absolute_logit_difference": float(difference.max()),
                "mean_absolute_logit_difference": float(difference.mean()),
                "max_absolute_probability_difference": float((other.softmax(-1) - cpu_logits.softmax(-1)).abs().max()),
                "per_token_logit_max": difference.max(-1).values.tolist(),
                "per_token_block_max": np.abs(native_blocks - cpu_blocks).max(-1).tolist(),
            }
            for name, array in (("native-logits", native_logits), ("cpu-logits", cpu_logits.numpy()),
                                ("native-blocks", native_blocks), ("cpu-blocks", cpu_blocks)):
                array.astype("<f4").tofile(output / (arm + "-" + name + ".f32"))
        # Instrumented capture has two models here; only the bitwise equality exit
        # check is used, not this run's interleaved block capture.
        subprocess.run([str(binary), str(pairs["E"][1]), str(zero)],
                       check=True, stdout=subprocess.DEVNULL, timeout=30)
        report["native_E_zero_K_bitwise_equal"] = True
    report["outputs"] = {p.name: {"bytes": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(output.iterdir())}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({arm: row["max_absolute_logit_difference"] for arm, row in report["arms"].items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
