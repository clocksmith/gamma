#!/usr/bin/env python3
"""Exact NNCP gate for a CP8 high/low-byte output readout."""

from __future__ import annotations

import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ROCM_PYTHON = Path("/home/x/deco/gamma/.venv_rocm/bin/python")
os.environ.setdefault("AMD_SERIALIZE_KERNEL", "3")
os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", "11.0.0")
if Path(sys.executable) != ROCM_PYTHON:
    if not ROCM_PYTHON.is_file():
        raise SystemExit(f"missing receipt-bound ROCm interpreter: {ROCM_PYTHON}")
    os.execve(
        str(ROCM_PYTHON),
        [str(ROCM_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        os.environ.copy(),
    )

import torch
import torch.nn.functional as F

import nncp_tied_bf16_embedding_qm0 as parent_driver


CANDIDATE_ID = "nncp_cp8_symbol_readout_qm0_v1"
VOCABULARY = 16_392
WIDTH = 1_024
HIGH_CLASSES = 65
LOW_CLASSES = 256
CP_RANK = 8
SOURCE_LIMIT_BYTES = 65_536
FAITHFUL_OUTPUT_ELEMENTS = VOCABULARY * WIDTH
FACTORIZED_OUTPUT_ELEMENTS = (
    HIGH_CLASSES * WIDTH
    + LOW_CLASSES * WIDTH
    + CP_RANK * WIDTH
    + HIGH_CLASSES * CP_RANK
    + LOW_CLASSES * CP_RANK
)
FAITHFUL_OUTPUT_BYTES = 2 * FAITHFUL_OUTPUT_ELEMENTS
FACTORIZED_OUTPUT_BYTES = 2 * FACTORIZED_OUTPUT_ELEMENTS
PARAMETER_BYTES_REMOVED = FAITHFUL_OUTPUT_BYTES - FACTORIZED_OUTPUT_BYTES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def install_cp8_readout() -> None:
    core = parent_driver.child_harness.harness.parent.core
    faithful_type = core.FaithfulModel

    class CP8OutputModel(faithful_type):
        def __init__(self, config: object) -> None:
            super().__init__(config)
            if config.vocabulary != VOCABULARY or config.width != WIDTH:
                raise ValueError("CP8 readout received a different NNCP profile")
            del self.output_embedding
            self.output_high = torch.nn.Parameter(
                torch.empty(HIGH_CLASSES, WIDTH, dtype=torch.bfloat16)
            )
            self.output_low = torch.nn.Parameter(
                torch.empty(LOW_CLASSES, WIDTH, dtype=torch.bfloat16)
            )
            self.output_cp_basis = torch.nn.Parameter(
                torch.zeros(CP_RANK, WIDTH, dtype=torch.bfloat16)
            )
            self.output_cp_high = torch.nn.Parameter(
                torch.empty(HIGH_CLASSES, CP_RANK, dtype=torch.bfloat16)
            )
            self.output_cp_low = torch.nn.Parameter(
                torch.empty(LOW_CLASSES, CP_RANK, dtype=torch.bfloat16)
            )
            bound = config.init_range / math.sqrt(config.width)
            torch.nn.init.uniform_(self.output_high, -bound / math.sqrt(2), bound / math.sqrt(2))
            torch.nn.init.uniform_(self.output_low, -bound / math.sqrt(2), bound / math.sqrt(2))
            coefficient = 1.0 / math.sqrt(CP_RANK)
            torch.nn.init.uniform_(self.output_cp_high, -coefficient, coefficient)
            torch.nn.init.uniform_(self.output_cp_low, -coefficient, coefficient)

        def factorized_logits(self, value):
            high = F.linear(value, self.output_high)
            low = F.linear(value, self.output_low)
            basis = F.linear(value, self.output_cp_basis)
            interaction = torch.einsum(
                "...r,hr,lr->...hl",
                basis,
                self.output_cp_high,
                self.output_cp_low,
            )
            logits = high.unsqueeze(-1) + low.unsqueeze(-2) + interaction
            logits = logits.flatten(-2)[..., : self.config.vocabulary]
            return (logits + self.output_bias).float()

        def forward(self, symbols, memories):
            config = self.config
            value = F.embedding(symbols, self.embedding).to(torch.bfloat16)
            value = value * math.sqrt(config.width)
            next_memories = []
            for block, memory in zip(self.blocks, memories, strict=True):
                value, next_memory = block(value, memory, self.shared_relative_bias)
                next_memories.append(next_memory)
            value = self.final_norm(value)
            return self.factorized_logits(value), next_memories

    def make_model(config: object, device: torch.device) -> torch.nn.Module:
        torch.manual_seed(config.seed)
        torch.cuda.manual_seed_all(config.seed)
        return CP8OutputModel(config).to(device)

    core.make_model = make_model

    incremental_parent = parent_driver.child_harness.harness.parent
    cache_q0 = incremental_parent.cache_q0

    def incremental_logits(model, input_symbols, caches, state):
        config = model.config
        value = F.embedding(input_symbols[:, None], model.embedding).to(torch.bfloat16)
        value = value * math.sqrt(config.width)
        cache_position = config.memory_length + state
        active_length = cache_position + 1
        relative_offset = config.segment_length - 1 - state

        for block, (key_cache, value_cache) in zip(model.blocks, caches, strict=True):
            normalized = block.attention_norm(value)
            query = F.linear(normalized, block.query)
            current_key_value = F.linear(normalized, block.key_value)
            current_key, current_value = torch.split(
                current_key_value,
                (config.heads * config.key_width, config.heads * config.value_width),
                dim=-1,
            )
            query = query.view(config.streams, 1, config.heads, config.key_width).transpose(1, 2)
            current_key = current_key.view(config.streams, 1, config.heads, config.key_width).transpose(1, 2)
            current_value = current_value.view(config.streams, 1, config.heads, config.value_width).transpose(1, 2)
            key_cache[:, :, cache_position : cache_position + 1].copy_(current_key)
            value_cache[:, :, cache_position : cache_position + 1].copy_(current_value)
            keys = key_cache[:, :, :active_length]
            values = value_cache[:, :, :active_length]
            content = torch.einsum("bhtd,bhkd->bhtk", query, keys)
            relative_key = block.relative.transpose(1, 2)[
                :, relative_offset : relative_offset + active_length
            ]
            relative = torch.einsum("bhtd,hkd->bhtk", query, relative_key)
            relative_bias = model.shared_relative_bias[
                relative_offset : relative_offset + active_length
            ].T[None, :, None, :]
            relative = relative + relative_bias * math.sqrt(config.key_width * config.width)
            score = (content + relative) / math.sqrt(config.key_width)
            attention = torch.softmax(score.float(), dim=-1).to(value.dtype)
            attended = torch.einsum("bhtk,bhkd->bhtd", attention, values)
            attended = attended.transpose(1, 2).reshape(
                config.streams, 1, config.heads * config.value_width
            )
            value = value + F.linear(attended, block.output)
            feedforward = block.feedforward_norm(value)
            gate, content_ff = F.linear(
                feedforward, block.feedforward_in, block.feedforward_in_bias
            ).chunk(2, dim=-1)
            hidden = core.libnc_gelu(gate) * content_ff
            value = value + F.linear(
                hidden, block.feedforward_out, block.feedforward_out_bias
            )

        value = model.final_norm(value)
        return model.factorized_logits(value)[:, 0]

    cache_q0.incremental_logits = incremental_logits


def main() -> int:
    parent_driver.CANDIDATE_ID = CANDIDATE_ID
    parent_driver.install_tied_embedding = install_cp8_readout
    status = parent_driver.main()

    output_dir = ROOT / "results" / CANDIDATE_ID
    if "--output-dir" in sys.argv:
        output_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
    decision_path = output_dir / "decision.json"
    decision = json.loads(decision_path.read_text())
    comparison = decision.pop("tied_comparison")
    decision.pop("tied_embedding")

    source_paths = (
        Path(__file__),
        ROOT / "tools/nncp_tied_bf16_embedding_qm0.py",
        ROOT / "tools/nncp_zipf_output_bias_qm0.py",
        ROOT / "tools/nncp_evicted_ema_memory_qm0.py",
        ROOT / "docs/nncp_cp8_symbol_readout_qm0_plan.md",
        ROOT / f"programs/{CANDIDATE_ID}/meta.json",
    )
    source_blob = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in source_paths
    )
    source_package = lzma.compress(source_blob, preset=9 | lzma.PRESET_EXTREME)
    source_path = output_dir / "incremental_source_package.lzma"
    source_path.write_bytes(source_package)
    comparison["incremental_source_package_bytes"] = len(source_package)

    failed = [
        condition
        for condition in decision["failed_conditions"]
        if condition != "incremental_source_exceeds_65536"
    ]
    if len(source_package) > SOURCE_LIMIT_BYTES:
        failed.append("incremental_source_exceeds_65536")
    promotion = not failed
    decision.update(
        {
            "schema": "enwiki9_nncp_cp8_symbol_readout_qm0_v1",
            "candidate_id": CANDIDATE_ID,
            "status": "AUTHORIZED_MATURE_CP8_READOUT" if promotion else "REJECT",
            "verdict": "authorize_mature_cp8_readout" if promotion else "retire_cp8_symbol_readout",
            "cp8_readout": {
                "symbol_high": "id >> 8",
                "symbol_low": "id & 255",
                "high_classes": HIGH_CLASSES,
                "low_classes": LOW_CLASSES,
                "cp_rank": CP_RANK,
                "input_embedding_unchanged_and_independent": True,
                "symbol_specific_bias_unchanged": True,
                "faithful_output_parameter_bytes": FAITHFUL_OUTPUT_BYTES,
                "factorized_output_parameter_bytes": FACTORIZED_OUTPUT_BYTES,
                "parameter_bytes_removed": PARAMETER_BYTES_REMOVED,
                "transmitted_table_bytes": 0,
            },
            "cp8_comparison": comparison,
            "failed_conditions": failed,
            "claim_boundary": (
                "Exact fixed high/low CP-rank-8 NNCP output representation at "
                "65,536 symbols. No rank, partition, dtype, bias, initialization, "
                "interaction-form, published-score, or full-corpus inheritance."
            ),
        }
    )
    decision["decision"]["promotion_authorized"] = promotion
    decision["inputs"]["cp8_driver_script_sha256"] = sha256_file(Path(__file__))
    decision["artifacts"] = {
        "incremental_source_package": {
            "path": str(source_path.relative_to(ROOT)),
            "bytes": len(source_package),
            "sha256": sha256_file(source_path),
        }
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "actual_gain_bytes": comparison["actual_gain_bytes"],
                "candidate_archive_bytes": comparison["candidate_archive_bytes"],
                "failed_conditions": failed,
                "ideal_third_gain_bytes": comparison["aligned_ideal"]["chronological_third_gain_bytes"],
                "parameter_bytes_removed": PARAMETER_BYTES_REMOVED,
                "verdict": decision["verdict"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return status


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nncp-cp8-symbol-readout-qm0: {error}", file=sys.stderr)
        raise
