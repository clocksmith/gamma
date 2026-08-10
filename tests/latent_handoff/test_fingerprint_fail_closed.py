from dataclasses import replace

import pytest

from src.mind_meld.latent_handoff.contract import (
    CacheGeometry,
    CacheLayout,
    ContractError,
    ExperimentContract,
    ModelIdentity,
    RopeContract,
    RouteOutcome,
)


def identity(name: str) -> ModelIdentity:
    return ModelIdentity(name, "0123456789abcdef", "w", "c", "t", "h")


def contract() -> ExperimentContract:
    geometry = CacheGeometry(CacheLayout.LBSHD, 2, 1, 2, 7, 8, "float32")
    rope = RopeContract("default", 1_000_000.0, "none", 8)
    return ExperimentContract(
        source=identity("source"),
        target=identity("target"),
        source_geometry=geometry,
        target_geometry=geometry,
        source_rope=rope,
        target_rope=rope,
        transformers_version="4.57.6",
        attention_implementation="eager",
        deterministic_algorithms=True,
        route=RouteOutcome.MAPPED_CACHE,
        token_ids_digest="tokens",
        position_ids_digest="positions",
    )


def test_contract_digest_is_stable() -> None:
    value = contract()
    assert value.digest == value.digest


def test_contract_rejects_unpinned_revision() -> None:
    value = contract()
    bad_source = replace(value.source, revision="main")
    with pytest.raises(ContractError, match="immutable commit"):
        replace(value, source=bad_source).validate()


def test_contract_rejects_sequence_mismatch() -> None:
    value = contract()
    target = replace(value.target_geometry, sequence=8)
    with pytest.raises(ContractError, match="sequence lengths differ"):
        replace(value, target_geometry=target).validate()


def test_route_enum_cannot_represent_replay_or_reset() -> None:
    with pytest.raises(ValueError):
        RouteOutcome("TEXTUAL_REPLAY")
    with pytest.raises(ValueError):
        RouteOutcome("CACHE_RESET")
