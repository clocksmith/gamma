#!/usr/bin/env python3
"""Verify the exact FXCM/PPMD joint static-allocation certificate."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "fxcm_joint_budget_composition_v1" / "theorem_verifier.json"


def main() -> None:
    saving = 111_820_800
    restore = 192_937_984
    quantum = 1_048_576
    quanta = 24
    baseline_ppmd_kib = 20_352

    restoration_net = restore - saving
    ppmd_growth = quantum * quanta
    total_delta = restoration_net + ppmd_growth
    total_delta_kib, remainder = divmod(total_delta, 1024)
    final_ppmd_kib = baseline_ppmd_kib + (ppmd_growth // 1024)

    assert restoration_net == 81_117_184
    assert ppmd_growth == 25_165_824
    assert total_delta == 106_283_008
    assert remainder == 0
    assert total_delta_kib == 103_792
    assert final_ppmd_kib == 44_928

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema": "fxcm_joint_budget_composition_theorem_v1",
                "status": "pass",
                "saving_bytes": saving,
                "idx13_restoration_bytes": restore,
                "ppmd_quantum_bytes": quantum,
                "ppmd_quanta": quanta,
                "restoration_net_bytes": restoration_net,
                "ppmd_growth_bytes": ppmd_growth,
                "total_static_delta_bytes": total_delta,
                "total_static_delta_kib": total_delta_kib,
                "baseline_ppmd_kib": baseline_ppmd_kib,
                "candidate_ppmd_kib": final_ppmd_kib,
                "score_credit_bytes": 0,
                "boundary": (
                    "Static allocation arithmetic only; native RSS, archive, "
                    "determinism, roundtrip, package, and runtime remain required."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
