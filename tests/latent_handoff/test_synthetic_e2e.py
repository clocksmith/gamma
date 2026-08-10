import hashlib

import torch
from transformers import Qwen3Config, Qwen3ForCausalLM, __version__ as transformers_version

from src.mind_meld.latent_handoff.calibration import (
    apply_directional_mapper,
    capture_prefill,
)
from src.mind_meld.latent_handoff.contract import (
    ExperimentContract,
    ModelIdentity,
    RouteOutcome,
    digest_object,
)
from src.mind_meld.latent_handoff.injection import inject_and_forward
from src.mind_meld.latent_handoff.mapper import fit_directional_mapper
from src.mind_meld.latent_handoff.rope import rope_contract_from_config


def test_fitted_mapper_runs_from_capture_through_target_decode() -> None:
    torch.manual_seed(21)
    torch.use_deterministic_algorithms(True)
    config = Qwen3Config(
        vocab_size=96,
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
    calibration_ids = torch.randint(0, config.vocab_size, (1, 64))
    calibration = capture_prefill(model, calibration_ids)
    identity = ModelIdentity(
        "synthetic/Qwen3-tiny",
        "0123456789abcdef",
        digest_object({name: list(value.shape) for name, value in model.state_dict().items()}),
        digest_object(config.to_dict()),
        "synthetic-tokenizer",
        "completion-mode",
    )
    mapper = fit_directional_mapper(
        [(calibration.content_cache, calibration.content_cache)],
        source_identity=identity,
        target_identity=identity,
        selected_layers=((0,), (1,)),
        calibration_digest="calibration",
        validation_digest="validation",
        fit_code_commit="abcdef123456",
        ridge_lambda=1e-8,
    )

    held_out_ids = torch.randint(0, config.vocab_size, (1, 17))
    query_ids = torch.randint(0, config.vocab_size, (1, 5))
    held_out = capture_prefill(model, held_out_ids)
    mapped = apply_directional_mapper(
        mapper, held_out.content_cache, config, held_out.position_ids
    )
    contract = ExperimentContract(
        source=identity,
        target=identity,
        source_geometry=held_out.rotated_cache.geometry,
        target_geometry=mapped.geometry,
        source_rope=rope_contract_from_config(config),
        target_rope=rope_contract_from_config(config),
        transformers_version=transformers_version,
        attention_implementation="eager",
        deterministic_algorithms=True,
        route=RouteOutcome.MAPPED_CACHE,
        token_ids_digest=hashlib.sha256(held_out_ids.numpy().tobytes()).hexdigest(),
        position_ids_digest=hashlib.sha256(held_out.position_ids.numpy().tobytes()).hexdigest(),
    )
    result = inject_and_forward(
        model, mapped, query_ids, contract, target_identity=identity
    )
    with torch.no_grad():
        native = model(
            torch.cat((held_out_ids, query_ids), dim=1), use_cache=False, return_dict=True
        ).logits[:, -query_ids.shape[1] :, :]
    torch.testing.assert_close(result.logits, native, rtol=2e-4, atol=2e-4)
    assert torch.equal(result.logits.argmax(-1), native.argmax(-1))
