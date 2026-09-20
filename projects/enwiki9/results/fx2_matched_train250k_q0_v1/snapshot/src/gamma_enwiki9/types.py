"""Domain distinctions shared by execution, evidence, recipes and delivery."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal


class CandidateKind(str, Enum):
    STANDALONE_CODEC = "standalone_codec"
    EXPERIMENT_RECIPE = "experiment_recipe"
    ANALYSIS_ONLY = "analysis_only"
    EXTERNAL_ADAPTER = "external_adapter"


class ClosureKind(str, Enum):
    BUILD = "build"
    CODEC_RUNTIME = "codec_runtime"
    EXPERIMENT_RUNTIME = "experiment_runtime"
    VERIFICATION = "verification"


@dataclass(frozen=True)
class Population:
    sha256: str
    count: int
    unit: Literal["raw_bytes", "transformed_symbols", "trace_rows", "archive_bytes"]
    coordinate: str
    initialization: str
    prior_exposure: str
    reconstruction_assets: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunOutcome:
    returncode: int | None
    classification: str
    cleanup_complete: bool
    observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceReport:
    verified: bool
    identities: tuple[str, ...] = ()
    comparisons: tuple[str, ...] = ()
    coverage: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScientificDecision:
    hypothesis: str
    outcome: Literal["supported", "rejected", "inconclusive"]
    evidence: EvidenceReport

    def __post_init__(self):
        if self.outcome != "inconclusive" and not self.evidence.verified:
            raise ValueError("a scientific decision requires verified evidence")


@dataclass(frozen=True)
class PackageInventory:
    required_assets: tuple[str, ...]
    counted_bytes: int
    accounting_form: str
    missing: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildProfile:
    command: tuple[str, ...]
    tools: tuple[tuple[str, str], ...]
    required_options: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResourceBudget:
    cpus: tuple[int, ...]
    memory_bytes: int
    scratch_bytes: int
    wall_seconds: int

    def __post_init__(self):
        if not self.cpus or any(type(x) is not int or x < 0 for x in self.cpus):
            raise ValueError("CPU assignment is required")
        if any(type(x) is not int or x <= 0 for x in
               (self.memory_bytes, self.scratch_bytes, self.wall_seconds)):
            raise ValueError("resource limits must be positive integers")


@dataclass(frozen=True)
class ExecutionContext:
    job_id: str
    snapshot_root: Path
    workspace: Path
    budget: ResourceBudget
    build_profile: BuildProfile
    environment: tuple[tuple[str, str], ...] = ()
