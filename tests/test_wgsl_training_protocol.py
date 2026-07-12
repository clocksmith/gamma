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
