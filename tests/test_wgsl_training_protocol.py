import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "wgsl"
    / "training"
    / "train_wgsl.py"
)
SPEC = importlib.util.spec_from_file_location("gamma_wgsl_training", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FixtureTokenizer:
    eos_token_id = 99

    def encode(self, value, add_special_tokens):
        prefix = [1] if add_special_tokens else []
        return prefix + [ord(character) for character in value]


def test_encode_pair_masks_prompt_and_preserves_completion():
    encoded = MODULE._encode_pair(FixtureTokenizer(), "abc", "xy", 32)
    assert encoded["inputIds"] == [1, 97, 98, 99, 120, 121, 99]
    assert encoded["labels"] == [-100, -100, -100, -100, 120, 121, 99]
    assert encoded["completionMask"] == [0, 0, 0, 0, 1, 1, 1]
    assert encoded["completionTokenCount"] == 3


def test_encode_pair_truncates_prompt_before_completion():
    encoded = MODULE._encode_pair(FixtureTokenizer(), "abcdef", "xy", 5)
    assert encoded["inputIds"] == [101, 102, 120, 121, 99]
    assert encoded["labels"] == [-100, -100, 120, 121, 99]


def test_jsonl_loader_is_fail_closed(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text(json.dumps({"prompt": "p", "completion": "c"}) + "\n", encoding="utf-8")
    assert MODULE._read_jsonl(path) == [{"prompt": "p", "completion": "c"}]
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="contains no rows"):
        MODULE._read_jsonl(empty)


def test_dpo_completion_text_preserves_whitespace_and_empty_negatives():
    assert MODULE._require_text("  replacement  ", "chosen", allow_empty=True) == "  replacement  "
    assert MODULE._require_text("  ", "rejected", allow_empty=True) == "  "
    assert MODULE._require_text("", "rejected", allow_empty=True) == ""
    with pytest.raises(RuntimeError, match="must be a string"):
        MODULE._require_text(None, "rejected", allow_empty=True)


def test_protocol_rejects_unversioned_request_before_runtime_imports():
    with pytest.raises(RuntimeError, match="request.protocol"):
        MODULE.execute({})


def test_tree_hash_changes_with_adapter_bytes(tmp_path):
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    weights = adapter / "adapter_model.safetensors"
    weights.write_bytes(b"one")
    first = MODULE._hash_tree(adapter)
    weights.write_bytes(b"two")
    second = MODULE._hash_tree(adapter)
    assert len(first) == 64
    assert first != second


def test_base_policy_load_skips_lora_attachment(monkeypatch, tmp_path):
    class Model:
        class Config:
            use_cache = False
        config = Config()

    model = Model()
    tokenizer = object()
    monkeypatch.setattr(MODULE, "_resolve_model_path", lambda _model, _runtime: tmp_path)
    monkeypatch.setattr(MODULE, "_load_tokenizer", lambda _path, _runtime: tokenizer)
    monkeypatch.setattr(
        MODULE,
        "_load_base_model",
        lambda _path, _runtime, _dtype, _checkpointing: model,
    )
    monkeypatch.setattr(
        MODULE,
        "_attach_lora",
        lambda *_args: pytest.fail("base rollout must not attach LoRA"),
    )
    loaded_model, loaded_tokenizer, model_path = MODULE._load_policy(
        {
            "model": {"modelId": "fixture"},
            "training": {"dtype": "bfloat16", "gradientCheckpointing": False},
            "policyMode": "base",
        },
        {},
    )
    assert loaded_model is model
    assert loaded_tokenizer is tokenizer
    assert model_path == tmp_path


def test_generation_policy_enables_cache_and_disables_checkpointing(monkeypatch, tmp_path):
    class Model:
        class Config:
            use_cache = False
        config = Config()

    observed = {}
    model = Model()
    monkeypatch.setattr(MODULE, "_resolve_model_path", lambda _model, _runtime: tmp_path)
    monkeypatch.setattr(MODULE, "_load_tokenizer", lambda _path, _runtime: object())

    def load(_path, _runtime, _dtype, checkpointing):
        observed["checkpointing"] = checkpointing
        return model

    monkeypatch.setattr(MODULE, "_load_base_model", load)
    MODULE._load_policy(
        {
            "model": {"modelId": "fixture"},
            "training": {"dtype": "bfloat16", "gradientCheckpointing": True},
            "policyMode": "base",
        },
        {},
        for_generation=True,
    )
    assert observed["checkpointing"] is False
    assert model.config.use_cache is True


def test_base_rollout_uses_declared_policy_hash():
    policy_hash = "a" * 64
    adapter_path, observed_hash = MODULE._rollout_policy_identity(
        {"policyMode": "base", "policyHash": policy_hash}
    )
    assert adapter_path is None
    assert observed_hash == policy_hash


def test_base_rollout_rejects_adapter_path():
    with pytest.raises(RuntimeError, match="cannot be combined"):
        MODULE._load_policy(
            {
                "model": {"modelId": "fixture"},
                "training": {"dtype": "bfloat16", "gradientCheckpointing": False},
                "policyMode": "base",
                "adapterPath": "/tmp/adapter",
            },
            {},
        )


def test_rollout_output_resumes_only_matching_prefix(tmp_path):
    task = {"taskId": "task-1"}
    sampling = {"seed": 11, "groupSize": 2, "temperature": 0.8}
    state = {
        "schemaVersion": 1,
        "policyHash": "a" * 64,
        "sampling": sampling,
    }
    rollout_path, groups = MODULE._prepare_rollout_output(
        tmp_path,
        state,
        [task],
        sampling,
        2,
    )
    assert groups == []
    rollout_path.write_text(
        json.dumps({
            "taskId": "task-1",
            "sampling": {**sampling, "seed": 11},
            "samples": [{"completionMask": [0, 1]}, {"completionMask": [0, 1]}],
        }) + "\n",
        encoding="utf-8",
    )
    resumed_path, resumed = MODULE._prepare_rollout_output(
        tmp_path,
        state,
        [task],
        sampling,
        2,
    )
    assert resumed_path == rollout_path
    assert len(resumed) == 1


def test_rollout_output_rejects_stale_state(tmp_path):
    sampling = {"seed": 11, "groupSize": 2}
    MODULE._prepare_rollout_output(
        tmp_path,
        {"schemaVersion": 1, "policyHash": "a" * 64},
        [{"taskId": "task-1"}],
        sampling,
        2,
    )
    with pytest.raises(RuntimeError, match="stale_rollout"):
        MODULE._prepare_rollout_output(
            tmp_path,
            {"schemaVersion": 1, "policyHash": "b" * 64},
            [{"taskId": "task-1"}],
            sampling,
            2,
        )


def test_per_row_seeded_sampler_is_deterministic():
    import torch

    scores = torch.tensor([
        [0.1, 0.2, 0.3, 0.4],
        [0.4, 0.3, 0.2, 0.1],
    ])
    first = MODULE._PerRowSeededTopPSampler(
        torch,
        [11, 29],
        0.8,
        0.95,
        scores.device,
    )(None, scores)
    second = MODULE._PerRowSeededTopPSampler(
        torch,
        [11, 29],
        0.8,
        0.95,
        scores.device,
    )(None, scores)
    assert torch.equal(first, second)
    assert torch.isfinite(first).sum(dim=1).tolist() == [1, 1]


def test_grpo_samples_are_seed_shuffled_before_step_budget_is_applied():
    groups = [
        {
            "samples": [
                {"sampleId": f"sample-{index}", "advantage": 1 if index % 2 else 0}
                for index in range(10)
            ]
        },
        {
            "samples": [
                {"sampleId": f"sample-{index}", "advantage": -1 if index % 2 else 0}
                for index in range(10, 20)
            ]
        },
    ]
    first = MODULE._seed_shuffled_grpo_samples(groups, 11)
    second = MODULE._seed_shuffled_grpo_samples(groups, 11)
    different_seed = MODULE._seed_shuffled_grpo_samples(groups, 29)
    input_ids = [f"sample-{index}" for index in range(1, 20, 2)]
    first_ids = [sample["sampleId"] for sample in first]

    assert first_ids == [sample["sampleId"] for sample in second]
    assert first_ids != input_ids
    assert first_ids != [sample["sampleId"] for sample in different_seed]
    assert set(first_ids) == set(input_ids)


def test_grpo_update_contract_rejects_stale_or_reused_rollouts():
    assert MODULE._grpo_update_contract({
        "updatesPerRolloutBatch": 1,
        "maximumStalePolicyUpdates": 0,
    }) == (1, 0)
    with pytest.raises(RuntimeError, match="exactly one update"):
        MODULE._grpo_update_contract({
            "updatesPerRolloutBatch": 2,
            "maximumStalePolicyUpdates": 0,
        })
    with pytest.raises(RuntimeError, match="zero stale-policy"):
        MODULE._grpo_update_contract({
            "updatesPerRolloutBatch": 1,
            "maximumStalePolicyUpdates": 1,
        })
