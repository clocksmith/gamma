#!/usr/bin/env python3
"""Freeze the 12 independently selected unseen boundary corpora (B01..B12) with exact bytes and SHA-256 pins.

Selected by an isolated read-only subagent that never inspected capacity-diagnostic-v1/ or
projects/algorithm_solver/. Only reads raw UTF-8 source bytes and records alphabet size and hashes;
runs zero capacity, rank, or solver calculations.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAMMA_ROOT = HERE.parents[3]
DECO_ROOT = Path(os.environ.get("DECO_ROOT", str(GAMMA_ROOT.parent.parent)))

REPO_ROOTS = {
    "gamma": GAMMA_ROOT,
    "fawn": Path(os.environ.get("FAWN_REPO", str(DECO_ROOT / "fawn"))),
    "doppler": Path(os.environ.get("DOPPLER_REPO", str(DECO_ROOT / "doppler"))),
    "reploid": Path(os.environ.get("REPLOID_REPO", str(DECO_ROOT / "reploid"))),
}

SELECTIONS = [
    {
        "id": "B01",
        "name": "enwiki9-endpoint428-seal-tests",
        "language": "Python",
        "repo": "gamma",
        "commit": "fbe798f63",
        "files": [
            "projects/enwiki9/tests/test_seal_endpoint428_pair_layer0_10m.py",
            "projects/enwiki9/tests/test_seal_endpoint428_pair_layer0_lzma_package.py",
            "projects/enwiki9/tests/test_seal_endpoint428_pair_layer0_native.py",
        ],
        "description": "Unit tests verifying archive byte-budget economics and packaging guards for enwiki9 endpoint-428 layer-0 sealing tools.",
    },
    {
        "id": "B02",
        "name": "zig-runtime-app-orchestration",
        "language": "Zig",
        "repo": "fawn",
        "commit": "a281360ff0",
        "files": [
            "runtime/zig/src/app/mod.zig",
            "runtime/zig/src/app/prepare.zig",
            "runtime/zig/src/app/request.zig",
            "runtime/zig/src/app/runner.zig",
        ],
        "description": "Hexagonal Zig runtime application layer defining request contracts, preparation, and synchronous execution orchestration.",
    },
    {
        "id": "B03",
        "name": "wgsl-dot-product-variants",
        "language": "WGSL",
        "repo": "fawn",
        "commit": "a281360ff0",
        "files": [
            "bench/inference-pipeline/kernels/dot_product_forward_f32.wgsl",
            "bench/inference-pipeline/kernels/dot_product_pairwise_f32.wgsl",
            "bench/inference-pipeline/kernels/dot_product_reverse_f32.wgsl",
        ],
        "description": "Compute shader variants implementing forward, pairwise, and reverse-order f32 dot-product reductions.",
    },
    {
        "id": "B04",
        "name": "wgsl-linear-attention-kernels",
        "language": "WGSL",
        "repo": "doppler",
        "commit": "bfee8cd43",
        "files": [
            "src/gpu/kernels/linear_attention_apply.wgsl",
            "src/gpu/kernels/linear_attention_apply_f16.wgsl",
            "src/gpu/kernels/linear_attention_summary.wgsl",
            "src/gpu/kernels/linear_attention_summary_f16.wgsl",
        ],
        "description": "WebGPU WGSL kernels for linear-attention state summary and application across f32 and f16 precision lanes.",
    },
    {
        "id": "B05",
        "name": "js-json-format-helpers",
        "language": "JavaScript",
        "repo": "doppler",
        "commit": "bfee8cd43",
        "files": [
            "src/formats/clone-json.js",
            "src/formats/load-json.js",
            "src/formats/sorted-json.js",
        ],
        "description": "Shared JSON serialization utilities for deep cloning, cross-runtime loading, and deterministic key-sorted hashing.",
    },
    {
        "id": "B06",
        "name": "py-gamma-core-engine",
        "language": "Python",
        "repo": "gamma",
        "commit": "fbe798f63",
        "files": [
            "gamma-core/src/engine/__init__.py",
            "gamma-core/src/engine/base.py",
            "gamma-core/src/engine/factory.py",
        ],
        "description": "Abstract inference-engine base interface, configuration dataclass, and backend registration factory for gamma-core.",
    },
    {
        "id": "B07",
        "name": "c-dxil-source-native-headers",
        "language": "C",
        "repo": "fawn",
        "commit": "a281360ff0",
        "files": [
            "runtime/c/compiler/src/dxil/dxil_source_native_bounds.h",
            "runtime/c/compiler/src/dxil/dxil_source_native_internal.h",
            "runtime/c/compiler/src/dxil/dxil_source_native_opt.h",
            "runtime/c/compiler/src/dxil/dxil_source_native_packed.h",
        ],
        "description": "Internal C headers for Doe DXIL native source projection covering function state, bounds clamping, opt, and packed ops.",
    },
    {
        "id": "B08",
        "name": "py-privacy-concrete-prepare",
        "language": "Python",
        "repo": "doppler",
        "commit": "bfee8cd43",
        "files": [
            "tools/privacy-concrete/prepare.py",
            "tools/privacy-concrete/prepare_flash_embedding.py",
            "tools/privacy-concrete/prepare_flash_tokenizer.py",
        ],
        "description": "CLI preparation scripts provisioning pinned public tokenizer files, embedding shards, and fixtures.",
    },
    {
        "id": "B09",
        "name": "js-poolday-work-providers",
        "language": "JavaScript",
        "repo": "reploid",
        "commit": "7c335e2cf",
        "files": [
            "apps/poolday/providers/work-adapter.js",
            "apps/poolday/providers/work-device.js",
            "apps/poolday/providers/work-generation-completion.js",
            "apps/poolday/providers/work-network-provider.js",
            "apps/poolday/providers/work-provider.js",
            "apps/poolday/providers/work-resident-provider.js",
        ],
        "description": "Poolday work-provider module wiring device lifetimes, resident execution, placement, and completion adapters.",
    },
    {
        "id": "B10",
        "name": "c-tsir-internal-headers",
        "language": "C",
        "repo": "fawn",
        "commit": "a281360ff0",
        "files": [
            "runtime/c/compiler/src/tsir/tsir_extended_internal.h",
            "runtime/c/compiler/src/tsir/tsir_frontend_internal.h",
            "runtime/c/compiler/src/tsir/tsir_reference_internal.h",
            "runtime/c/compiler/src/tsir/tsir_source_internal.h",
        ],
        "description": "Internal C compiler headers defining frontend lowering, semantic IR, reference helpers, and extended matching for TSIR.",
    },
    {
        "id": "B11",
        "name": "wgsl-qwen-gqa-backward",
        "language": "WGSL",
        "repo": "doppler",
        "commit": "bfee8cd43",
        "files": [
            "src/gpu/kernels/backward/qwen_gqa_attention_backward.wgsl",
            "src/gpu/kernels/backward/qwen_gqa_softmax_backward_scores.wgsl",
            "src/gpu/kernels/backward/qwen_gqa_softmax_recompute.wgsl",
        ],
        "description": "Backward-pass WGSL compute shaders implementing grouped-query attention gradient propagation and softmax recomputation.",
    },
    {
        "id": "B12",
        "name": "js-reploid-core-primitives",
        "language": "JavaScript",
        "repo": "reploid",
        "commit": "7c335e2cf",
        "files": [
            "packages/reploid/src/cancellation.js",
            "packages/reploid/src/hashing.js",
            "packages/reploid/src/index.js",
            "packages/reploid/src/observation.js",
        ],
        "description": "Core Reploid package primitives for abort-signal cancellation racing, SHA-256 hashing, observation, and exports.",
    },
]


def main() -> None:
    corpora = {}
    queries = []
    for spec in SELECTIONS:
        root = REPO_ROOTS[spec["repo"]]
        programs = []
        file_meta = []
        for rel in spec["files"]:
            path = root / rel
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            programs.append(text)
            file_meta.append({
                "path": rel,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            })
        alpha_size = len(set("".join(programs)))
        total_bytes = sum(f["bytes"] for f in file_meta)
        corpora[spec["id"]] = {
            "id": spec["id"],
            "name": spec["name"],
            "language": spec["language"],
            "repo": spec["repo"],
            "commit": spec["commit"],
            "description": spec["description"],
            "alphabetSize": alpha_size,
            "totalBytes": total_bytes,
            "files": file_meta,
            "programs": programs,
        }
        # Two symmetric queries per corpus: (1) primary 64-slot cliff, (2) below-alphabet stress test
        below_k = alpha_size - 1 if alpha_size < 64 else alpha_size - 2
        queries.append({"corpusId": spec["id"], "rule": "W2", "budget": 64, "kind": "64-slot-cliff"})
        queries.append({"corpusId": spec["id"], "rule": "W2", "budget": below_k, "kind": "below-alphabet"})

    payload = {
        "schema": "bits-boundary-race-instances/v1",
        "selectorSubagentId": "a7d22714-d5ae-4c23-8949-8780036cd6e6",
        "rule": "W2",
        "maxBytes": 160,
        "wholeProgramExcluded": True,
        "corpora": corpora,
        "queries": queries,
    }
    out_path = HERE / "boundary-instances.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(corpora)} corpora, {len(queries)} queries)")
    for cid, obj in corpora.items():
        print(f"  {cid} ({obj['language']:10s}) |Sigma|={obj['alphabetSize']:2d} bytes={obj['totalBytes']:5d}  {obj['name']}")


if __name__ == "__main__":
    main()
