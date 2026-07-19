#!/usr/bin/env python3
"""Emit Gamma's append-only TranslateGemma exposure ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from exposure_ledger import EXPOSURE_LEDGER_SCHEMA, EXPOSURE_LEDGER_SCHEMA_SHA256, seal_events


REPO_ROOT = Path(__file__).resolve().parents[4]
PROMOTION_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "promotion"
OUTPUT_PATH = PROMOTION_ROOT / "exposure-ledger.v1.json"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_ledger() -> dict[str, object]:
    contract_path = PROMOTION_ROOT / "promotion-contract.v1.json"
    data_path = REPO_ROOT / "projects" / "distillation" / "translation" / "training_data" / "translate_distill_pairs.eval2_wmt13_enes_128.jsonl"
    contract_hash = f"sha256:{file_hash(contract_path)}"
    data_hash = f"sha256:{file_hash(data_path)}"
    actor = {"type": "repository", "id": "clocksmith/gamma"}
    base = {
        "repository": "gamma",
        "experimentId": "gamma.translation.enes.single-student.promotion.v1",
        "actor": actor,
    }
    events = [
        {
            **base,
            "eventId": "gamma-translation-draft",
            "occurredAt": "2026-03-10T01:49:45.000Z",
            "type": "campaign_transition",
            "receipt": {"id": "promotion-contract", "sha256": contract_hash, "path": str(contract_path.relative_to(REPO_ROOT))},
            "details": {"from": None, "to": "draft"},
        },
        {
            **base,
            "eventId": "gamma-wmt13-registered",
            "occurredAt": "2026-03-10T01:49:46.000Z",
            "type": "artifact_registered",
            "artifact": {"id": "wmt13-enes-128-legacy", "sha256": data_hash, "path": str(data_path.relative_to(REPO_ROOT))},
            "role": "development",
            "details": {
                "acquisitionPath": "legacy WMT13 evaluation material",
                "labelingPath": "public references",
                "componentId": "wmt13-enes",
                "familyId": "legacy-wmt",
                "firstExposureTimeBasis": "earliest checked-in TranslateGemma run timestamp",
            },
        },
        {
            **base,
            "eventId": "gamma-wmt13-exposed-development",
            "occurredAt": "2026-03-10T01:49:47.000Z",
            "type": "artifact_exposed",
            "artifact": {"id": "wmt13-enes-128-legacy", "sha256": data_hash, "path": str(data_path.relative_to(REPO_ROOT))},
            "role": "development",
            "details": {
                "experimentIds": ["translategemma-nativekd2", "savant-nativekd2"],
                "personIds": [],
                "decisionIds": ["data_selection", "checkpoint_selection", "decode_selection", "router_evaluation"],
                "promotionUseAllowed": False,
            },
        },
        {
            **base,
            "eventId": "gamma-translation-contract-frozen",
            "occurredAt": "2026-07-14T00:00:00.000Z",
            "type": "campaign_transition",
            "receipt": {"id": "promotion-contract", "sha256": contract_hash, "path": str(contract_path.relative_to(REPO_ROOT))},
            "details": {"from": "draft", "to": "frozen"},
        },
    ]
    return {
        "schema": EXPOSURE_LEDGER_SCHEMA,
        "schemaSha256": EXPOSURE_LEDGER_SCHEMA_SHA256,
        "ledgerId": "gamma.translation.enes.exposure.v1",
        "repository": "gamma",
        "events": seal_events(events),
    }


def main() -> int:
    OUTPUT_PATH.write_text(json.dumps(build_ledger(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT_PATH.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
