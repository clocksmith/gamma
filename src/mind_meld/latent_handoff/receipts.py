"""Canonical, append-only experiment receipt construction."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .contract import canonical_json, digest_object


RECEIPT_SCHEMA = "gamma.latent-handoff-receipt/v1"


@dataclass
class ExperimentReceipt:
    contract_digest: str
    phase: str
    status: str
    artifacts: dict[str, str]
    measurements: dict[str, Any]
    gates: dict[str, bool]
    prohibited_route_counts: dict[str, int] = field(
        default_factory=lambda: {"textualReplay": 0, "cacheReset": 0, "heuristicFallback": 0}
    )
    notes: list[str] = field(default_factory=list)
    schema: str = RECEIPT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        value = {
            "schema": self.schema,
            "contractDigest": self.contract_digest,
            "phase": self.phase,
            "status": self.status,
            "artifacts": self.artifacts,
            "measurements": self.measurements,
            "gates": self.gates,
            "prohibitedRouteCounts": self.prohibited_route_counts,
            "notes": self.notes,
        }
        value["receiptDigest"] = digest_object(value)
        return value

    def write(self, path: Path) -> str:
        value = self.to_dict()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json(value) + b"\n")
        return value["receiptDigest"]


def read_receipt(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = value.pop("receiptDigest")
    actual = digest_object(value)
    if expected != actual:
        raise ValueError("receipt digest mismatch")
    value["receiptDigest"] = expected
    return value
