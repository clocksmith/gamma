"""Config-driven local-only Latent Handoff v0 experiment operations."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer, __version__ as transformers_version

from .calibration import (
    apply_directional_mapper,
    apply_directional_mapper_timed,
    capture_prefill,
)
from .conditions import permuted_cache, random_orthogonal_cache, zero_cache
from .contract import (
    ContractError,
    ExperimentContract,
    ModelIdentity,
    RouteOutcome,
    bundle_digest,
    digest_file,
    digest_object,
)
from .injection import greedy_continue, inject_and_forward
from .layer_selection import select_source_layers
from .mapper import DirectionalMapper, fit_directional_mapper
from .metrics import (
    cosine_similarity,
    floor_normalized_retention,
    logit_fidelity,
    teacher_forced_perplexity,
    tensor_fidelity,
)
from .receipts import ExperimentReceipt
from .receipts import read_receipt
from .rope import rope_contract_from_config
from .rope import apply_rope, qwen3_cos_sin


TOKENIZER_FILES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "chat_template.jinja",
)
WEIGHT_PATTERNS = ("*.safetensors", "*.bin")


@dataclass(frozen=True)
class LoadedSide:
    identity: ModelIdentity
    model: Any
    tokenizer: Any


def load_config(path: Path, *, require_materialized: bool = True) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != "gamma.latent-handoff-experiment/v1":
        raise ContractError("unsupported or missing experiment config schema")
    for side in ("source", "target"):
        section = value.get(side)
        if not isinstance(section, dict):
            raise ContractError(f"missing {side} model config")
        if not section.get("repository") or not re.fullmatch(
            r"[0-9a-f]{40}", section.get("revision", "")
        ):
            raise ContractError(f"{side} repository and immutable revision are required")
        if require_materialized and not section.get("localPath"):
            raise ContractError(
                f"{side}.localPath is unset; provision pinned weights locally before execution"
            )
    if value.get("mode") != "completion":
        raise ContractError("v0 requires completion mode")
    if value.get("thinking") is not False:
        raise ContractError("v0 requires thinking=false")
    if value.get("runtime", {}).get("deterministicAlgorithms") is not True:
        raise ContractError("v0 requires deterministicAlgorithms=true")
    if value.get("runtime", {}).get("attentionImplementation") != "eager":
        raise ContractError("v0 requires the pinned eager attention implementation")
    device = value.get("runtime", {}).get("device")
    if device not in {"cpu", "cuda", "mps"}:
        raise ContractError(f"unsupported runtime device: {device!r}")
    if value.get("mapper", {}).get("featurePolicy") not in (
        "all-source-kv-heads",
        "same-source-head",
    ):
        raise ContractError("unsupported mapper feature policy")
    return value


def _required_path(value: Any, label: str) -> Path:
    if not value:
        raise ContractError(f"{label} is unset")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise ContractError(f"{label} does not exist: {path}")
    return path


def fingerprint_from_config(config_path: Path, side_name: str, output: Path) -> Path:
    config = load_config(config_path, require_materialized=False)
    if side_name not in ("source", "target"):
        raise ContractError("fingerprint side must be source or target")
    section = config[side_name]
    local_path = _required_path(section.get("localPath"), f"{side_name}.localPath")
    identity = _identity(section, local_path)
    value = {
        "repository": identity.repository,
        "revision": identity.revision,
        "expectedIdentity": {
            "weightsDigest": identity.weights_digest,
            "configDigest": identity.config_digest,
            "tokenizerBundleDigest": identity.tokenizer_bundle_digest,
            "chatTemplateDigest": identity.chat_template_digest,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return output


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _weight_digest(path: Path) -> str:
    members: dict[str, str] = {}
    for pattern in WEIGHT_PATTERNS:
        for member in sorted(path.glob(pattern)):
            members[member.name] = digest_file(member)
    if not members:
        raise ContractError(f"no model weight files found under {path}")
    return digest_object(members)


def _identity(section: dict[str, Any], local_path: Path) -> ModelIdentity:
    config_path = local_path / "config.json"
    if not config_path.is_file():
        raise ContractError(f"missing model config: {config_path}")
    tokenizer_files = {
        name: local_path / name for name in TOKENIZER_FILES if (local_path / name).is_file()
    }
    if "tokenizer.json" not in tokenizer_files or "tokenizer_config.json" not in tokenizer_files:
        raise ContractError("tokenizer bundle lacks tokenizer.json or tokenizer_config.json")
    tokenizer_config = json.loads((local_path / "tokenizer_config.json").read_text(encoding="utf-8"))
    chat_template = tokenizer_config.get("chat_template", "")
    chat_template_file = local_path / "chat_template.jinja"
    if chat_template_file.is_file():
        chat_template = chat_template_file.read_text(encoding="utf-8")
    identity = ModelIdentity(
        repository=section["repository"],
        revision=section["revision"],
        weights_digest=_weight_digest(local_path),
        config_digest=digest_file(config_path),
        tokenizer_bundle_digest=bundle_digest(tokenizer_files),
        chat_template_digest=hashlib.sha256(chat_template.encode("utf-8")).hexdigest(),
    )
    identity.validate()
    expected = section.get("expectedIdentity", {})
    comparisons = {
        "weightsDigest": identity.weights_digest,
        "configDigest": identity.config_digest,
        "tokenizerBundleDigest": identity.tokenizer_bundle_digest,
        "chatTemplateDigest": identity.chat_template_digest,
    }
    for name, actual in comparisons.items():
        if expected.get(name) and expected[name] != actual:
            raise ContractError(f"{section['repository']} {name} mismatch")
    return identity


def _validated_phase1_receipts(
    config: dict[str, Any], source: ModelIdentity, target: ModelIdentity
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name, expected_identity in (("source", source), ("target", target)):
        receipt_path = _required_path(
            config.get("phase1Receipts", {}).get(name), f"phase1Receipts.{name}"
        )
        receipt = read_receipt(receipt_path)
        if receipt.get("phase") != "same-model-cache-exactness" or not receipt.get(
            "gates", {}
        ).get("cacheCorrectness"):
            raise ContractError(f"{name} same-model cache receipt has not passed")
        if receipt.get("artifacts", {}).get("modelIdentityDigest") != digest_object(
            expected_identity.__dict__
        ):
            raise ContractError(f"{name} same-model receipt identity mismatch")
        receipts[name] = receipt
    return receipts


def load_side(section: dict[str, Any], *, device: str, dtype: str) -> LoadedSide:
    if device == "cuda" and not torch.cuda.is_available():
        raise ContractError("runtime device cuda is unavailable on this machine")
    if device == "mps":
        if not torch.backends.mps.is_built() or not torch.backends.mps.is_available():
            raise ContractError("runtime device mps is unavailable on this machine")
    local_path = Path(section["localPath"]).expanduser().resolve()
    if not local_path.is_dir():
        raise ContractError(f"local model path does not exist: {local_path}")
    identity = _identity(section, local_path)
    tokenizer = AutoTokenizer.from_pretrained(local_path, local_files_only=True)
    dtype_value = getattr(torch, dtype)
    model = AutoModelForCausalLM.from_pretrained(
        local_path,
        local_files_only=True,
        torch_dtype=dtype_value,
        attn_implementation="eager",
    ).to(device).eval()
    if getattr(model.config, "model_type", None) != "qwen3":
        raise ContractError("Latent Handoff v0 only admits Qwen3 models")
    return LoadedSide(identity, model, tokenizer)


def read_jsonl_texts(path: Path) -> list[str]:
    texts: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            text = value.get("text")
            if not isinstance(text, str) or not text:
                raise ContractError(f"{path}:{line_number} lacks non-empty text")
            texts.append(text)
    if not texts:
        raise ContractError(f"corpus is empty: {path}")
    return texts


def _identical_tokens(source: LoadedSide, target: LoadedSide, text: str, device: str) -> torch.Tensor:
    source_ids = source.tokenizer(text, add_special_tokens=False, return_tensors="pt").input_ids
    target_ids = target.tokenizer(text, add_special_tokens=False, return_tensors="pt").input_ids
    if not torch.equal(source_ids, target_ids):
        raise ContractError("source and target token IDs differ for calibration text")
    return source_ids.to(device)


def fit_from_config(config_path: Path, output: Path) -> Path:
    config = load_config(config_path)
    runtime = config["runtime"]
    device, dtype = runtime["device"], runtime["dtype"]
    torch.use_deterministic_algorithms(True)
    source = load_side(config["source"], device=device, dtype=dtype)
    target = load_side(config["target"], device=device, dtype=dtype)
    _validated_phase1_receipts(config, source.identity, target.identity)
    if source.identity.tokenizer_bundle_digest != target.identity.tokenizer_bundle_digest:
        raise ContractError("source and target tokenizer bundle digests differ")
    calibration_path = _required_path(config["corpora"]["calibration"], "corpora.calibration")
    validation_path = _required_path(config["corpora"]["validation"], "corpora.validation")
    texts = read_jsonl_texts(calibration_path)

    def pairs():
        for text in texts:
            token_ids = _identical_tokens(source, target, text, device)
            source_cache = capture_prefill(source.model, token_ids).content_cache
            target_cache = capture_prefill(target.model, token_ids).content_cache
            yield source_cache, target_cache
    top_k = int(config["mapper"]["topK"])
    ridge_lambda = float(config["mapper"]["ridgeLambda"])
    selected = select_source_layers(pairs, top_k=top_k, ridge_lambda=ridge_lambda)
    mapper = fit_directional_mapper(
        pairs,
        source_identity=source.identity,
        target_identity=target.identity,
        selected_layers=selected,
        calibration_digest=digest_file(calibration_path),
        validation_digest=digest_file(validation_path),
        fit_code_commit=_git_commit(),
        ridge_lambda=ridge_lambda,
        feature_policy=config["mapper"]["featurePolicy"],
    )
    artifact_digest = mapper.save(output)
    key_scores = []
    value_scores = []
    executable_mapper = mapper.to(device, getattr(torch, dtype))
    for text in read_jsonl_texts(validation_path):
        token_ids = _identical_tokens(source, target, text, device)
        source_cache = capture_prefill(source.model, token_ids).content_cache
        target_cache = capture_prefill(target.model, token_ids).content_cache
        mapped = executable_mapper.map_content(source_cache)
        key_scores.append(tensor_fidelity(target_cache.key, mapped.key))
        value_scores.append(tensor_fidelity(target_cache.value, mapped.value))
    fit_receipt = ExperimentReceipt(
        contract_digest=digest_object(
            {"source": source.identity.__dict__, "target": target.identity.__dict__}
        ),
        phase="mapper-fit-validation",
        status="measured",
        artifacts={
            "mapperDigest": artifact_digest,
            "calibrationCorpus": str(calibration_path),
            "validationCorpus": str(validation_path),
        },
        measurements={
            "selectedSourceLayers": [list(value) for value in selected],
            "keyFidelity": key_scores,
            "valueFidelity": value_scores,
        },
        gates={"mapperSerialized": True, "heldOutSignal": False},
        notes=["Held-out signal is measured here; promotion remains an evaluation decision."],
    )
    fit_receipt.write(output / "fit-receipt.json")
    return output


def _identity_mapper(identity: ModelIdentity, cache: Any) -> DirectionalMapper:
    geometry = cache.geometry
    feature_dim = geometry.kv_heads * geometry.head_dim
    weights = torch.zeros(
        (geometry.layers, geometry.kv_heads, feature_dim, geometry.head_dim),
        dtype=cache.key.dtype,
        device=cache.key.device,
    )
    for layer in range(geometry.layers):
        for head in range(geometry.kv_heads):
            start = head * geometry.head_dim
            weights[layer, head, start : start + geometry.head_dim] = torch.eye(
                geometry.head_dim, device=cache.key.device, dtype=cache.key.dtype
            )
    biases = torch.zeros(
        (geometry.layers, geometry.kv_heads, geometry.head_dim),
        dtype=cache.key.dtype,
        device=cache.key.device,
    )
    return DirectionalMapper(
        source=identity,
        target=identity,
        selected_layers=tuple((layer,) for layer in range(geometry.layers)),
        ridge_lambda=0.0,
        calibration_digest="identity-gate",
        validation_digest="identity-gate",
        fit_code_commit=_git_commit(),
        key_weight=weights,
        key_bias=biases,
        value_weight=weights.clone(),
        value_bias=biases.clone(),
        source_kv_heads=geometry.kv_heads,
        source_head_dim=geometry.head_dim,
        target_kv_heads=geometry.kv_heads,
        target_head_dim=geometry.head_dim,
        feature_policy="all-source-kv-heads",
    )


def phase1_from_config(config_path: Path, side_name: str, output: Path) -> Path:
    config = load_config(config_path)
    if side_name not in ("source", "target"):
        raise ContractError("phase1 side must be source or target")
    runtime = config["runtime"]
    device, dtype = runtime["device"], runtime["dtype"]
    torch.use_deterministic_algorithms(True)
    side = load_side(config[side_name], device=device, dtype=dtype)
    calibration_path = _required_path(config["corpora"]["calibration"], "corpora.calibration")
    text = read_jsonl_texts(calibration_path)[0]
    ids = side.tokenizer(text, add_special_tokens=False, return_tensors="pt").input_ids
    if ids.shape[1] == 0:
        raise ContractError("phase1 text tokenized to an empty sequence")
    repeats = (139 + ids.shape[1] - 1) // ids.shape[1]
    ids = ids.repeat(1, repeats)[:, :139].to(device)
    prefix, continuation = ids[:, :11], ids[:, 11:139]
    capture = capture_prefill(side.model, prefix)
    rope = rope_contract_from_config(side.model.config)
    contract = ExperimentContract(
        source=side.identity,
        target=side.identity,
        source_geometry=capture.rotated_cache.geometry,
        target_geometry=capture.rotated_cache.geometry,
        source_rope=rope,
        target_rope=rope,
        transformers_version=transformers_version,
        attention_implementation="eager",
        deterministic_algorithms=True,
        route=RouteOutcome.NATIVE_TARGET_CACHE,
        token_ids_digest=hashlib.sha256(prefix.cpu().numpy().tobytes()).hexdigest(),
        position_ids_digest=hashlib.sha256(capture.position_ids.cpu().numpy().tobytes()).hexdigest(),
    )
    injected = inject_and_forward(
        side.model,
        capture.rotated_cache,
        continuation,
        contract,
        target_identity=side.identity,
    )
    with torch.no_grad():
        native = side.model(
            ids,
            attention_mask=torch.ones_like(ids),
            use_cache=False,
            return_dict=True,
        ).logits[:, 11:, :]
    identity_mapped = _identity_mapper(side.identity, capture.content_cache).map_content(
        capture.content_cache
    )
    cos, sin = qwen3_cos_sin(
        side.model.config,
        capture.position_ids,
        dtype=identity_mapped.key.dtype,
        device=identity_mapped.key.device,
    )
    identity_rotated_key = apply_rope(identity_mapped.key, cos, sin)
    logits_close = torch.allclose(injected.logits, native, rtol=1e-4, atol=1e-5)
    greedy_equal = torch.equal(injected.logits.argmax(-1), native.argmax(-1))
    identity_close = torch.allclose(
        identity_rotated_key, capture.rotated_cache.key, rtol=1e-5, atol=1e-6
    ) and torch.allclose(
        identity_mapped.value, capture.rotated_cache.value, rtol=1e-5, atol=1e-6
    )
    gate = logits_close and greedy_equal and identity_close
    receipt = ExperimentReceipt(
        contract_digest=contract.digest,
        phase="same-model-cache-exactness",
        status="passed" if gate else "failed",
        artifacts={
            "calibrationCorpus": str(calibration_path),
            "modelIdentityDigest": digest_object(side.identity.__dict__),
        },
        measurements={
            "teacherForcedPositions": 128,
            "logits": logit_fidelity(native, injected.logits),
            "greedyTokensEqual": greedy_equal,
            "identityMapperRoundTrip": identity_close,
            "ropeRoundTrip": tensor_fidelity(
                capture.rotated_cache.key, identity_rotated_key
            ),
            "cachePositionStart": int(injected.cache_position[0].item()),
        },
        gates={"cacheCorrectness": gate},
    )
    receipt.write(output)
    if not gate:
        raise ContractError("same-model cache correctness gate failed")
    return output


def evaluate_from_config(config_path: Path, mapper_path: Path, output: Path) -> Path:
    config = load_config(config_path)
    runtime = config["runtime"]
    device, dtype = runtime["device"], runtime["dtype"]
    torch.use_deterministic_algorithms(True)
    source = load_side(config["source"], device=device, dtype=dtype)
    target = load_side(config["target"], device=device, dtype=dtype)
    _validated_phase1_receipts(config, source.identity, target.identity)
    mapper = DirectionalMapper.load(mapper_path).to(device, getattr(torch, dtype))
    if mapper.source != source.identity or mapper.target != target.identity:
        raise ContractError("mapper direction or model identity does not match loaded models")
    mapper_metadata = json.loads((mapper_path / "mapper.json").read_text(encoding="utf-8"))
    fit_receipt = read_receipt(mapper_path / "fit-receipt.json")
    if fit_receipt.get("artifacts", {}).get("mapperDigest") != mapper_metadata.get(
        "artifactDigest"
    ):
        raise ContractError("mapper fit receipt does not match the mapper artifact")
    evaluation_path = _required_path(config["corpora"]["evaluation"], "corpora.evaluation")
    rows = [json.loads(line) for line in evaluation_path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) < 2:
        raise ContractError("evaluation requires at least two counterfactual trials")
    if len({row.get("query") for row in rows}) != 1:
        raise ContractError("evaluation trials must use one fixed visible query")
    if len({row.get("expected") for row in rows}) != len(rows):
        raise ContractError("evaluation operational facts must be unique per trial")
    prefix_lengths = set()
    for index, row in enumerate(rows):
        for field in (
            "prefix",
            "query",
            "expected",
            "teacherForcedContinuation",
            "summary750Words",
            "summaryTokenMatched",
        ):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ContractError(f"evaluation trial {index} lacks {field}")
        if len(row["summary750Words"].split()) != 750:
            raise ContractError(f"evaluation trial {index} summary750Words is not 750 words")
        prefix_ids = _identical_tokens(source, target, row["prefix"], device)
        prefix_lengths.add(prefix_ids.shape[1])
        continuation_ids = _identical_tokens(
            source, target, row["teacherForcedContinuation"], device
        )
        if not 32 <= continuation_ids.shape[1] <= 128:
            raise ContractError(
                f"evaluation trial {index} teacher continuation must contain 32..128 tokens"
            )
        summary_words_ids = _identical_tokens(source, target, row["summary750Words"], device)
        summary_matched_ids = _identical_tokens(
            source, target, row["summaryTokenMatched"], device
        )
        if summary_words_ids.shape[1] != summary_matched_ids.shape[1]:
            raise ContractError(
                f"evaluation trial {index} token-matched summary has the wrong token count"
            )
    if len(prefix_lengths) != 1:
        raise ContractError("evaluation prefixes must have the same token length")
    results: list[dict[str, Any]] = []

    def decode_condition(cache: Any, query_ids: torch.Tensor, condition_contract: ExperimentContract) -> tuple[Any, str]:
        started = time.perf_counter()
        initial = inject_and_forward(
            target.model,
            cache,
            query_ids,
            condition_contract,
            target_identity=target.identity,
        )
        generated, _ = greedy_continue(
            target.model,
            initial,
            condition_contract,
            target_identity=target.identity,
            max_new_tokens=int(config["evaluation"]["maxNewTokens"]),
        )
        return initial, target.tokenizer.decode(generated[0], skip_special_tokens=True), time.perf_counter() - started

    def visible_only(text: str) -> tuple[str, float]:
        ids = target.tokenizer(text, add_special_tokens=False, return_tensors="pt").input_ids.to(device)
        started = time.perf_counter()
        capture = capture_prefill(target.model, ids)
        identity_contract = ExperimentContract(
            source=target.identity,
            target=target.identity,
            source_geometry=capture.rotated_cache.geometry,
            target_geometry=capture.rotated_cache.geometry,
            source_rope=rope_contract_from_config(target.model.config),
            target_rope=rope_contract_from_config(target.model.config),
            transformers_version=transformers_version,
            attention_implementation="eager",
            deterministic_algorithms=True,
            route=RouteOutcome.NATIVE_TARGET_CACHE,
            token_ids_digest=hashlib.sha256(ids.cpu().numpy().tobytes()).hexdigest(),
            position_ids_digest=hashlib.sha256(capture.position_ids.cpu().numpy().tobytes()).hexdigest(),
        )
        first_token = capture.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        first = inject_and_forward(
            target.model,
            capture.rotated_cache,
            first_token,
            identity_contract,
            target_identity=target.identity,
        )
        rest, _ = greedy_continue(
            target.model,
            first,
            identity_contract,
            target_identity=target.identity,
            max_new_tokens=max(1, int(config["evaluation"]["maxNewTokens"]) - 1),
        )
        generated = torch.cat((first_token, rest), dim=1)
        return target.tokenizer.decode(generated[0], skip_special_tokens=True), time.perf_counter() - started

    for trial, row in enumerate(rows):
        prefix, query = row["prefix"], row["query"]
        expected = row["expected"]
        prefix_ids = _identical_tokens(source, target, prefix, device)
        query_ids = _identical_tokens(source, target, query, device)
        source_capture = capture_prefill(source.model, prefix_ids)
        target_capture = capture_prefill(target.model, prefix_ids)
        mapped, mapping_timings, mapped_content = apply_directional_mapper_timed(
            mapper, source_capture.content_cache, target.model.config, source_capture.position_ids
        )
        contract = ExperimentContract(
            source=source.identity,
            target=target.identity,
            source_geometry=source_capture.rotated_cache.geometry,
            target_geometry=mapped.geometry,
            source_rope=rope_contract_from_config(source.model.config),
            target_rope=rope_contract_from_config(target.model.config),
            transformers_version=transformers_version,
            attention_implementation="eager",
            deterministic_algorithms=True,
            route=RouteOutcome.MAPPED_CACHE,
            token_ids_digest=hashlib.sha256(prefix_ids.cpu().numpy().tobytes()).hexdigest(),
            position_ids_digest=hashlib.sha256(source_capture.position_ids.cpu().numpy().tobytes()).hexdigest(),
        )
        mapped_result, text, mapped_elapsed = decode_condition(mapped, query_ids, contract)
        native_contract = ExperimentContract(
            **{**contract.__dict__, "route": RouteOutcome.NATIVE_TARGET_CACHE,
               "source_geometry": target_capture.rotated_cache.geometry,
               "target_geometry": target_capture.rotated_cache.geometry}
        )
        native_result, native_text, native_elapsed = decode_condition(
            target_capture.rotated_cache, query_ids, native_contract
        )
        continuation_ids = _identical_tokens(
            source, target, row["teacherForcedContinuation"], device
        )
        mapped_teacher = inject_and_forward(
            target.model,
            mapped,
            continuation_ids,
            contract,
            target_identity=target.identity,
            capture_attention_outputs=False,
        )
        native_teacher = inject_and_forward(
            target.model,
            target_capture.rotated_cache,
            continuation_ids,
            native_contract,
            target_identity=target.identity,
            capture_attention_outputs=False,
        )
        controls: dict[str, Any] = {}
        for name, cache in (
            ("zero", zero_cache(mapped)),
            (
                "randomOrthogonal",
                random_orthogonal_cache(source_capture.rotated_cache, seed=trial),
            ),
            ("permutedMap", permuted_cache(mapped, seed=trial)),
        ):
            control_result, control_text, elapsed = decode_condition(cache, query_ids, contract)
            controls[name] = {
                "generated": control_text,
                "exactOperationalRecall": float(control_text.strip() == expected.strip()),
                "containsOperationalFact": float(expected in control_text),
                "logits": logit_fidelity(native_result.logits, control_result.logits),
                "elapsedSeconds": elapsed,
            }
        no_history_text, no_history_elapsed = visible_only(query)
        controls["noHistory"] = {
            "generated": no_history_text,
            "exactOperationalRecall": float(no_history_text.strip() == expected.strip()),
            "containsOperationalFact": float(expected in no_history_text),
            "elapsedSeconds": no_history_elapsed,
        }
        if source_capture.rotated_cache.geometry == mapped.geometry:
            direct_result, direct_text, elapsed = decode_condition(
                source_capture.rotated_cache, query_ids, contract
            )
            controls["directCopy"] = {
                "generated": direct_text,
                "exactOperationalRecall": float(direct_text.strip() == expected.strip()),
                "containsOperationalFact": float(expected in direct_text),
                "logits": logit_fidelity(native_result.logits, direct_result.logits),
                "elapsedSeconds": elapsed,
            }
        if len(rows) > 1:
            wrong_row = rows[(trial + 1) % len(rows)]
            wrong_prefix_ids = _identical_tokens(
                source, target, wrong_row["prefix"], device
            )
            wrong_capture = capture_prefill(source.model, wrong_prefix_ids)
            wrong_mapped = apply_directional_mapper(
                mapper,
                wrong_capture.content_cache,
                target.model.config,
                wrong_capture.position_ids,
            )
        else:
            wrong_row = None
            wrong_mapped = None
        if wrong_mapped is not None and wrong_mapped.geometry == mapped.geometry:
            wrong_result, wrong_text, elapsed = decode_condition(wrong_mapped, query_ids, contract)
            controls["wrongCacheSameLength"] = {
                "generated": wrong_text,
                "exactOperationalRecall": float(wrong_text.strip() == expected.strip()),
                "containsOperationalFact": float(expected in wrong_text),
                "followsWrongOperationalFact": float(wrong_row["expected"] in wrong_text),
                "logits": logit_fidelity(native_result.logits, wrong_result.logits),
                "elapsedSeconds": elapsed,
            }
        for field, name in (
            ("summary750Words", "summary750Words"),
            ("summaryTokenMatched", "summaryTokenMatched"),
        ):
            if row.get(field):
                summary_text, elapsed = visible_only(row[field] + query)
                controls[name] = {
                    "generated": summary_text,
                    "exactOperationalRecall": float(summary_text.strip() == expected.strip()),
                    "containsOperationalFact": float(expected in summary_text),
                    "elapsedSeconds": elapsed,
                }
        results.append(
            {
                "trial": trial,
                "expected": expected,
                "generated": text,
                "exactOperationalRecall": float(text.strip() == expected.strip()),
                "containsOperationalFact": float(expected in text),
                "nativeGenerated": native_text,
                "nativeExactOperationalRecall": float(native_text.strip() == expected.strip()),
                "nativeContainsOperationalFact": float(expected in native_text),
                "mappedLogits": logit_fidelity(native_result.logits, mapped_result.logits),
                "teacherForced": {
                    "positions": continuation_ids.shape[1],
                    "logits": logit_fidelity(native_teacher.logits, mapped_teacher.logits),
                    "nativePerplexity": teacher_forced_perplexity(
                        native_teacher.logits, continuation_ids
                    ),
                    "mappedPerplexity": teacher_forced_perplexity(
                        mapped_teacher.logits, continuation_ids
                    ),
                },
                "attentionOutputCosineByLayer": [
                    cosine_similarity(native_output, mapped_output)
                    for native_output, mapped_output in zip(
                        native_result.attention_outputs,
                        mapped_result.attention_outputs,
                    )
                ],
                "mappedKey": tensor_fidelity(
                    target_capture.content_cache.key, mapped_content.key
                ),
                "mappedValue": tensor_fidelity(
                    target_capture.content_cache.value, mapped_content.value
                ),
                "controls": controls,
                "timing": {
                    "sourcePrefillSeconds": source_capture.elapsed_seconds,
                    "sourceCacheSynchronizationSeconds": source_capture.synchronization_seconds,
                    "sourceCacheCaptureSeconds": source_capture.cache_capture_seconds,
                    "gpuCpuReadbackSeconds": 0.0,
                    "sourceRopeRemovalSeconds": source_capture.rope_removal_seconds,
                    "targetReprefillSeconds": target_capture.elapsed_seconds,
                    "featureGatherAndKVMappingSeconds": mapping_timings.feature_gather_and_kv_mapping_seconds,
                    "targetRopeApplicationSeconds": mapping_timings.target_rope_application_seconds,
                    "hostDeviceTransferSeconds": 0.0,
                    "targetCacheCreationSeconds": mapped_result.cache_creation_seconds,
                    "firstReceiverForwardSeconds": mapped_result.forward_seconds,
                    "totalHandoffSeconds": mapping_timings.total_seconds
                    + mapped_result.cache_creation_seconds
                    + mapped_result.forward_seconds,
                    "mappedDecodeSeconds": mapped_elapsed,
                    "nativeDecodeSeconds": native_elapsed,
                },
            }
        )
    mapped_recall = sum(row["exactOperationalRecall"] for row in results) / len(results)
    native_recall = sum(row["nativeExactOperationalRecall"] for row in results) / len(results)
    per_trial_advantages = []
    required_controls = {
        "zero",
        "randomOrthogonal",
        "permutedMap",
        "noHistory",
        "directCopy",
        "wrongCacheSameLength",
        "summary750Words",
        "summaryTokenMatched",
    }
    controls_complete = True
    for row in results:
        available = row["controls"]
        if not required_controls.issubset(available):
            controls_complete = False
            continue
        strongest = max(available[name]["exactOperationalRecall"] for name in required_controls)
        per_trial_advantages.append(row["exactOperationalRecall"] - strongest)
    lower_bound = -1.0
    if per_trial_advantages:
        generator = torch.Generator().manual_seed(0)
        values = torch.tensor(per_trial_advantages, dtype=torch.float64)
        samples = int(config["gates"]["bootstrapSamples"])
        indices = torch.randint(0, len(values), (samples, len(values)), generator=generator)
        means = values[indices].mean(dim=1).sort().values
        alpha = 1.0 - float(config["gates"]["bootstrapConfidence"])
        lower_bound = float(means[max(0, int(alpha / 2 * samples))].item())
    native_ratio = mapped_recall / native_recall if native_recall > 0 else 0.0
    average_advantage = (
        sum(per_trial_advantages) / len(per_trial_advantages)
        if per_trial_advantages
        else -1.0
    )
    wrong_follow_values = [
        row["controls"]["wrongCacheSameLength"]["followsWrongOperationalFact"]
        for row in results
        if "wrongCacheSameLength" in row["controls"]
    ]
    wrong_follows_rate = (
        sum(wrong_follow_values) / len(wrong_follow_values) if wrong_follow_values else 0.0
    )
    causal_gate = (
        controls_complete
        and native_ratio >= float(config["gates"]["mappedNativeRecallRatio"])
        and average_advantage >= float(config["gates"]["controlAdvantage"])
        and lower_bound > 0
        and wrong_follows_rate
        >= float(config["gates"]["wrongCacheFollowsWrongRate"])
    )
    benchmark_path = _required_path(config["corpora"]["benchmarks"], "corpora.benchmarks")
    benchmark_rows = [
        json.loads(line)
        for line in benchmark_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if not benchmark_rows:
        raise ContractError("held-out benchmark corpus is empty")
    benchmark_results: list[dict[str, Any]] = []
    for index, row in enumerate(benchmark_rows):
        for field in ("task", "prefix", "query", "expectedToken"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ContractError(f"benchmark row {index} lacks {field}")
        floor = row.get("chanceFloor")
        if not isinstance(floor, (float, int)) or not 0 <= floor < 1:
            raise ContractError(f"benchmark row {index} has invalid chanceFloor")
        expected_ids = _identical_tokens(source, target, row["expectedToken"], device)
        if expected_ids.shape != (1, 1):
            raise ContractError(f"benchmark row {index} expectedToken is not one token")
        expected_id = int(expected_ids.item())
        prefix_ids = _identical_tokens(source, target, row["prefix"], device)
        query_ids = _identical_tokens(source, target, row["query"], device)
        source_capture = capture_prefill(source.model, prefix_ids)
        target_capture = capture_prefill(target.model, prefix_ids)
        mapped = apply_directional_mapper(
            mapper,
            source_capture.content_cache,
            target.model.config,
            source_capture.position_ids,
        )
        benchmark_contract = ExperimentContract(
            source=source.identity,
            target=target.identity,
            source_geometry=source_capture.rotated_cache.geometry,
            target_geometry=mapped.geometry,
            source_rope=rope_contract_from_config(source.model.config),
            target_rope=rope_contract_from_config(target.model.config),
            transformers_version=transformers_version,
            attention_implementation="eager",
            deterministic_algorithms=True,
            route=RouteOutcome.MAPPED_CACHE,
            token_ids_digest=hashlib.sha256(prefix_ids.cpu().numpy().tobytes()).hexdigest(),
            position_ids_digest=hashlib.sha256(
                source_capture.position_ids.cpu().numpy().tobytes()
            ).hexdigest(),
        )
        native_benchmark_contract = ExperimentContract(
            **{
                **benchmark_contract.__dict__,
                "route": RouteOutcome.NATIVE_TARGET_CACHE,
                "source_geometry": target_capture.rotated_cache.geometry,
                "target_geometry": target_capture.rotated_cache.geometry,
            }
        )
        mapped_result = inject_and_forward(
            target.model,
            mapped,
            query_ids,
            benchmark_contract,
            target_identity=target.identity,
            capture_attention_outputs=False,
        )
        native_result = inject_and_forward(
            target.model,
            target_capture.rotated_cache,
            query_ids,
            native_benchmark_contract,
            target_identity=target.identity,
            capture_attention_outputs=False,
        )
        condition_caches = {
            "zero": zero_cache(mapped),
            "randomOrthogonal": random_orthogonal_cache(
                source_capture.rotated_cache, seed=index
            ),
            "permutedMap": permuted_cache(mapped, seed=index),
            "directCopy": source_capture.rotated_cache,
        }
        control_rows: dict[str, Any] = {}
        for name, cache in condition_caches.items():
            result = inject_and_forward(
                target.model,
                cache,
                query_ids,
                benchmark_contract,
                target_identity=target.identity,
                capture_attention_outputs=False,
            )
            control_rows[name] = {
                "correct": float(int(result.logits[:, -1].argmax().item()) == expected_id),
                "logits": logit_fidelity(native_result.logits[:, -1], result.logits[:, -1]),
            }
        no_history = capture_prefill(target.model, query_ids).logits[:, -1]
        control_rows["noHistory"] = {
            "correct": float(int(no_history.argmax().item()) == expected_id),
            "logits": logit_fidelity(native_result.logits[:, -1], no_history),
        }
        benchmark_results.append(
            {
                "task": row["task"],
                "chanceFloor": float(floor),
                "mappedCorrect": float(
                    int(mapped_result.logits[:, -1].argmax().item()) == expected_id
                ),
                "nativeCorrect": float(
                    int(native_result.logits[:, -1].argmax().item()) == expected_id
                ),
                "mappedLogits": logit_fidelity(
                    native_result.logits[:, -1], mapped_result.logits[:, -1]
                ),
                "controls": control_rows,
            }
        )
    task_metrics: dict[str, Any] = {}
    for task in sorted({row["task"] for row in benchmark_results}):
        task_rows = [row for row in benchmark_results if row["task"] == task]
        floors = {row["chanceFloor"] for row in task_rows}
        if len(floors) != 1:
            raise ContractError(f"benchmark task {task} has inconsistent chance floors")
        floor = next(iter(floors))
        mapped_accuracy = sum(row["mappedCorrect"] for row in task_rows) / len(task_rows)
        native_accuracy = sum(row["nativeCorrect"] for row in task_rows) / len(task_rows)
        retention = (
            floor_normalized_retention(mapped_accuracy, native_accuracy, floor)
            if native_accuracy > floor
            else -1.0
        )
        task_metrics[task] = {
            "chanceFloor": floor,
            "mappedAccuracy": mapped_accuracy,
            "nativeAccuracy": native_accuracy,
            "floorNormalizedRetention": retention,
        }
    average_floor_retention = sum(
        value["floorNormalizedRetention"] for value in task_metrics.values()
    ) / len(task_metrics)
    mapped_closer_than_controls = all(
        row["mappedLogits"]["klDivergence"]
        < min(control["logits"]["klDivergence"] for control in row["controls"].values())
        for row in benchmark_results
    )
    held_out_gate = (
        average_floor_retention
        >= float(config["gates"]["floorNormalizedRetention"])
        and all(
            value["mappedAccuracy"] >= value["chanceFloor"]
            for value in task_metrics.values()
        )
        and mapped_closer_than_controls
    )
    receipt = ExperimentReceipt(
        contract_digest=contract.digest,
        phase="held-out-evaluation",
        status=(
            "claimable"
            if causal_gate and held_out_gate
            else "comparable"
            if causal_gate or held_out_gate
            else "diagnostic"
        ),
        artifacts={"mapper": str(mapper_path.resolve()), "evaluationCorpus": str(evaluation_path)},
        measurements={
            "operationalTrials": results,
            "benchmarkTrials": benchmark_results,
            "benchmarkTasks": task_metrics,
            "aggregate": {
                "mappedExactRecall": mapped_recall,
                "nativeExactRecall": native_recall,
                "mappedNativeRecallRatio": native_ratio,
                "averageControlAdvantage": average_advantage,
                "pairedBootstrapLowerBound": lower_bound,
                "controlsComplete": controls_complete,
                "wrongCacheFollowsWrongRate": wrong_follows_rate,
                "averageFloorNormalizedRetention": average_floor_retention,
                "mappedLogitsCloserThanControls": mapped_closer_than_controls,
            },
        },
        gates={
            "cacheCorrectness": True,
            "causalTransfer": causal_gate,
            "heldOutGeneralization": held_out_gate,
        },
        notes=[
            "Claimable means the pre-registered causal and held-out gates passed; it is not a latency or repeated-switch claim."
        ],
    )
    receipt.write(output)
    return output
