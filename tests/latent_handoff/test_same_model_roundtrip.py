import hashlib
from dataclasses import replace

import pytest
import torch
from transformers import Qwen3Config, Qwen3ForCausalLM, __version__ as transformers_version

from src.mind_meld.latent_handoff.calibration import capture_prefill
from src.mind_meld.latent_handoff.contract import (
    ContractError,
    ExperimentContract,
    ModelIdentity,
    RouteOutcome,
    digest_object,
)
from src.mind_meld.latent_handoff.injection import inject_and_forward
from src.mind_meld.latent_handoff.rope import rope_contract_from_config


def _identity(model: Qwen3ForCausalLM) -> ModelIdentity:
    state_shapes = {name: list(value.shape) for name, value in model.state_dict().items()}
    return ModelIdentity(
        repository="synthetic/Qwen3-tiny",
        revision="0123456789abcdef",
        weights_digest=digest_object(state_shapes),
        config_digest=digest_object(model.config.to_dict()),
        tokenizer_bundle_digest="synthetic-token-ids-v1",
        chat_template_digest="completion-mode-no-template",
    )


def test_same_model_capture_injection_teacher_forcing_parity_128_positions() -> None:
    torch.manual_seed(7)
    torch.use_deterministic_algorithms(True)
    config = Qwen3Config(
        vocab_size=64,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=8,
        max_position_embeddings=256,
        rope_theta=1_000_000.0,
        attention_dropout=0.0,
    )
    config._attn_implementation = "eager"
    model = Qwen3ForCausalLM(config).eval()
    prefix = torch.randint(0, config.vocab_size, (1, 11))
    continuation = torch.randint(0, config.vocab_size, (1, 128))
    capture = capture_prefill(model, prefix)
    identity = _identity(model)
    contract = ExperimentContract(
        source=identity,
        target=identity,
        source_geometry=capture.rotated_cache.geometry,
        target_geometry=capture.rotated_cache.geometry,
        source_rope=rope_contract_from_config(config),
        target_rope=rope_contract_from_config(config),
        transformers_version=transformers_version,
        attention_implementation="eager",
        deterministic_algorithms=True,
        route=RouteOutcome.NATIVE_TARGET_CACHE,
        token_ids_digest=hashlib.sha256(prefix.numpy().tobytes()).hexdigest(),
        position_ids_digest=hashlib.sha256(capture.position_ids.numpy().tobytes()).hexdigest(),
    )
    with pytest.raises(ContractError, match="loaded target model identity"):
        inject_and_forward(
            model,
            capture.rotated_cache,
            continuation,
            contract,
            target_identity=replace(identity, revision="fedcba9876543210"),
        )
    injected = inject_and_forward(
        model,
        capture.rotated_cache,
        continuation,
        contract,
        target_identity=identity,
    )
    with torch.no_grad():
        native = model(torch.cat((prefix, continuation), dim=1), use_cache=False, return_dict=True)
    native_continuation = native.logits[:, prefix.shape[1] :, :]
    torch.testing.assert_close(injected.logits, native_continuation, rtol=1e-5, atol=1e-6)
    assert torch.equal(injected.logits.argmax(-1), native_continuation.argmax(-1))
    assert injected.cache_position.tolist() == list(range(11, 139))
