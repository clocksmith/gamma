#!/usr/bin/env python3
"""Freeze the layer-19 pre-softmax score-adjoint source oracle."""

from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import nncp_libnc_top_attention_product_oracle_64_q0_v1_materializer as parent
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = (
    "nncp_libnc_top_attention_softmax_input_adjoint_oracle_64_q0_v1"
)
PARENT_EXPERIMENT = ROOT / (
    "operations/adaptive/experiments/"
    "nncp_libnc_top_attention_product_oracle_64_q0_v1.json"
)
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = ROOT / (
    "tools/nncp_libnc_top_attention_softmax_input_adjoint_oracle_64_q0_v1.py"
)
MATERIALIZER = Path(__file__).resolve()
PROBE = (
    ROOT / "tools/nncp_libnc_top_attention_softmax_input_adjoint_probe_q0.c"
)
DESCRIPTOR = PROGRAM / "program.py"
OUTPUT = ROOT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(
    identifier: str, measurement_id: str, operator: str, threshold: object
) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": measurement_id,
        "operator": operator,
        "threshold": threshold,
    }


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    experiment = copy.deepcopy(json.loads(PARENT_EXPERIMENT.read_text()))
    experiment["experimentId"] = CANDIDATE_ID
    experiment["proposalId"] = CANDIDATE_ID
    experiment["registrationTiming"] = "prospective"
    experiment["evidenceClass"] = "oracle"
    experiment["objectiveCreditBytes"] = 0
    experiment["hypothesis"] = {
        "claim": (
            "A marked-zero probe immediately before the layer-19 attention "
            "softmax yields complete, live, deterministic BF16 score input "
            "and score-adjoint populations while preserving the proven "
            "attention-product captures and every non-probe fixture payload."
        ),
        "falsification": (
            "Any incomplete, dead, nondeterministic, fixture-changing, "
            "product-capture-changing, source-failing, resource-failing, or "
            "cleanup-failing population rejects the oracle."
        ),
    }
    experiment["changedMechanism"] = (
        "Retain the proven layer-19 attended and probability marked-zero "
        "probes and add one independent marked-zero score probe to t0 "
        "immediately before nc_soft_max. Capture input and callback adjoint "
        "twice across the same 64-state production population."
    )
    experiment["invariants"] = [
        "The production model, block, parameters, optimizer, update, probabilities, and every non-probe fixture payload remain unchanged.",
        "The score probe is algebraically zero-valued and is attached immediately before the ordinary softmax.",
        "The original attended and probability input/adjoint populations remain complete and deterministic.",
        "Score input and adjoint cover every state, head, stream, and key coordinate twice.",
        "Captured source tensors are zero-credit teacher evidence and cannot ship in a Gamma codec.",
        "A later open softmax backward must compute dS independently; this oracle does not implement it.",
    ]
    experiment["controls"] = [
        {
            "id": "marked-score-adjoint",
            "role": "treatment",
            "definition": "Attach one marked zero at the pre-softmax score boundary and capture its complete callback adjoint.",
        },
        {
            "id": "product-probe-preservation",
            "role": "comparator",
            "definition": "Retain and revalidate complete attended and probability input/adjoint populations.",
        },
        {
            "id": "unchanged-fixture",
            "role": "shifted",
            "definition": "Require every non-probe production fixture payload to retain its bound digest.",
        },
        {
            "id": "independent-replay",
            "role": "replay",
            "definition": "Repeat all six tensor populations and compare complete captures byte-for-byte.",
        },
        {
            "id": "live-score-tensors",
            "role": "negative",
            "definition": "Reject an all-zero score input or score adjoint.",
        },
    ]
    experiment["population"] = {
        "unit": "BF16 top-attention score forward and adjoint words",
        "scopeBytes": 20971520,
        "scopeSymbols": 10485760,
        "selection": (
            "Every pre-softmax score and score-adjoint word across 64 states, "
            "eight heads, 32 streams, and 320 key coordinates."
        ),
        "coordinate": (
            "state-major, stream-major, head-major, key-major serialization; "
            "observed LibNC metadata 320,1,8,32."
        ),
    }
    experiment["causalBoundary"] = {
        "availableInformation": [
            "The bound production graph/update callback and proven attention-product oracle antecedents.",
            "Only the frozen pre-softmax boundary, namespace, population, and controls are evaluated.",
        ],
        "forbiddenInformation": [
            "Using captured score adjoints in a shipping implementation, fitting to mismatch coordinates, or editing source comparators.",
            "Claiming open softmax backward, complete open attention, archive gain, or objective credit from this source oracle.",
        ],
    }
    existing_measurements = {row["id"] for row in experiment["measurements"]}
    additions = [
        measurement(
            "scoreInputElementCount",
            "BF16 elements",
            "Words in the combined pre-softmax score input.",
        ),
        measurement(
            "scoreAdjointElementCount",
            "BF16 elements",
            "Words in the combined pre-softmax score adjoint.",
        ),
        measurement(
            "scoreInputLive",
            "boolean",
            "The complete score input population is not all zero.",
        ),
        measurement(
            "scoreAdjointLive",
            "boolean",
            "The complete score-adjoint population is not all zero.",
        ),
        measurement(
            "scoreCaptureDeterministic",
            "boolean",
            "Both complete score input/adjoint captures reproduce byte-for-byte.",
        ),
    ]
    experiment["measurements"].extend(
        row for row in additions if row["id"] not in existing_measurements
    )
    for row in experiment["promotionPredicates"]:
        if row["measurement"] == "declaredProbeFileCount":
            row["threshold"] = 1536
    experiment["promotionPredicates"].extend(
        [
            predicate(
                "p-score-input-elements",
                "scoreInputElementCount",
                "eq",
                5242880,
            ),
            predicate(
                "p-score-adjoint-elements",
                "scoreAdjointElementCount",
                "eq",
                5242880,
            ),
            predicate("p-score-input-live", "scoreInputLive", "eq", True),
            predicate(
                "p-score-adjoint-live", "scoreAdjointLive", "eq", True
            ),
            predicate(
                "p-score-repeat", "scoreCaptureDeterministic", "eq", True
            ),
        ]
    )
    replaced = {"probe-source", "runner", "materializer", "program-descriptor"}
    experiment["inputs"] = [
        row for row in experiment["inputs"] if row["id"] not in replaced
    ]
    experiment["inputs"].extend(
        [
            parent.base.reference(PROBE, "probe-source"),
            parent.base.reference(RUNNER, "runner"),
            parent.base.reference(MATERIALIZER, "materializer"),
            parent.base.reference(DESCRIPTOR, "program-descriptor"),
        ]
    )
    present = {row["path"] for row in experiment["inputs"]}
    for path in local_source_closure((RUNNER, MATERIALIZER)):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            experiment["inputs"].append(
                parent.base.reference(path, parent.source_identifier(path))
            )
            present.add(relative)
    experiment["outputs"] = [
        f"results/{CANDIDATE_ID}/decision.json",
        f"results/{CANDIDATE_ID}/execution.json",
        f"results/{CANDIDATE_ID}/source-attended-heads-input.bf16",
        f"results/{CANDIDATE_ID}/source-attended-heads-adjoint.bf16",
        f"results/{CANDIDATE_ID}/source-attention-probability-input.bf16",
        f"results/{CANDIDATE_ID}/source-attention-probability-adjoint.bf16",
        f"results/{CANDIDATE_ID}/source-attention-score-input.bf16",
        f"results/{CANDIDATE_ID}/source-attention-score-adjoint.bf16",
        f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
    ]
    experiment["generatedUtc"] = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    )
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
