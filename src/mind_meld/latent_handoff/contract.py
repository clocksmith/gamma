"""Immutable identities and invariants for Latent Handoff v0."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gamma.latent-handoff-contract/v1"


class ContractError(ValueError):
    """Raised before decoding when an experiment identity is incompatible."""


class CacheLayout(str, Enum):
    LBSHD = "LBSHD"


class RouteOutcome(str, Enum):
    """The only state origins admitted by the scientific harness."""

    NATIVE_TARGET_CACHE = "NATIVE_TARGET_CACHE"
    MAPPED_CACHE = "MAPPED_CACHE"


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def digest_object(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def digest_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ModelIdentity:
    repository: str
    revision: str
    weights_digest: str
    config_digest: str
    tokenizer_bundle_digest: str
    chat_template_digest: str

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"model identity field {name!r} is empty")
        if len(self.revision) < 7:
            raise ContractError("model revision must be an immutable commit identifier")


@dataclass(frozen=True)
class CacheGeometry:
    layout: CacheLayout
    layers: int
    batch: int
    kv_heads: int
    sequence: int
    head_dim: int
    dtype: str

    def validate(self) -> None:
        if self.layout is not CacheLayout.LBSHD:
            raise ContractError(f"unsupported cache layout: {self.layout}")
        if min(self.layers, self.batch, self.kv_heads, self.sequence, self.head_dim) <= 0:
            raise ContractError("cache geometry dimensions must all be positive")
        if not self.dtype:
            raise ContractError("cache dtype is required")


@dataclass(frozen=True)
class RopeContract:
    rope_type: str
    theta: float
    scaling_digest: str
    rotary_dim: int
    position_base: int = 0

    def validate(self) -> None:
        if self.rope_type != "default":
            raise ContractError(
                f"Latent Handoff v0 only admits default RoPE, got {self.rope_type!r}"
            )
        if self.theta <= 0 or self.rotary_dim <= 0 or self.position_base < 0:
            raise ContractError("invalid RoPE contract")


@dataclass(frozen=True)
class ExperimentContract:
    source: ModelIdentity
    target: ModelIdentity
    source_geometry: CacheGeometry
    target_geometry: CacheGeometry
    source_rope: RopeContract
    target_rope: RopeContract
    transformers_version: str
    attention_implementation: str
    deterministic_algorithms: bool
    route: RouteOutcome
    token_ids_digest: str
    position_ids_digest: str
    schema: str = SCHEMA

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ContractError(f"unsupported contract schema: {self.schema}")
        self.source.validate()
        self.target.validate()
        self.source_geometry.validate()
        self.target_geometry.validate()
        self.source_rope.validate()
        self.target_rope.validate()
        if self.source_geometry.sequence != self.target_geometry.sequence:
            raise ContractError("source and target cache sequence lengths differ")
        if not self.transformers_version or not self.attention_implementation:
            raise ContractError("runtime identity is incomplete")
        if not self.deterministic_algorithms:
            raise ContractError("deterministic algorithms must be enabled")
        if not self.token_ids_digest or not self.position_ids_digest:
            raise ContractError("serialized token and position identities are required")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["route"] = self.route.value
        value["source_geometry"]["layout"] = self.source_geometry.layout.value
        value["target_geometry"]["layout"] = self.target_geometry.layout.value
        return value

    @property
    def digest(self) -> str:
        self.validate()
        return digest_object(self.to_dict())


def bundle_digest(files: Mapping[str, Path]) -> str:
    """Digest an explicitly named bundle without relying on directory order."""

    members = {name: digest_file(path) for name, path in sorted(files.items())}
    return digest_object(members)
