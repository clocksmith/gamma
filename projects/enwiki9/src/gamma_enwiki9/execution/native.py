"""Reusable native operations with explicit execution and evidence capabilities."""
from __future__ import annotations
from pathlib import Path

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.resolver import ArtifactResolver
from gamma_enwiki9.evidence.trace import TraceGeometry, compare_trace
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.types import ExecutionContext


class NativeGate:
    def __init__(self, context: ExecutionContext, *, resolver: ArtifactResolver,
                 executor: CommandExecutor, evidence_writer=publish_immutable_artifact):
        self.context, self.resolver, self.executor = context, resolver, executor
        self.evidence_writer = evidence_writer
        if executor.context != context:
            raise ValueError("executor belongs to another execution context")
        self.verify_build_profile()

    def verify_build_profile(self):
        for name, digest in self.context.build_profile.tools:
            path = Path(name)
            if fingerprint(path, path.parent)["sha256"] != digest.removeprefix("sha256:"):
                raise ValueError("build profile tool identity changed")

    def copy(self, name: str, destination: Path):
        if not destination.resolve().is_relative_to(self.context.workspace.resolve()):
            raise ValueError("materialized input escapes owned workspace")
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.resolver.copy(name, destination)

    def run(self, phase: str, argv: list[str], limits: PhaseLimits):
        self.verify_build_profile()
        outcome, record = self.executor.run(phase, argv, limits)
        self.verify_build_profile()
        return outcome, record

    def compare_trace(self, left: Path, right: Path, geometry: TraceGeometry):
        result = compare_trace(left, right, geometry)
        if not result["equal"]:
            self.evidence_writer(self.context.workspace / "first-divergence.json", canonical_bytes(result) + b"\n")
        return result
