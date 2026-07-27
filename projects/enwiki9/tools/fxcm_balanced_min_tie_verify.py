#!/usr/bin/env python3
"""Verify balanced minimum-priority FXCM tie selection."""

from __future__ import annotations

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "fxcm_balanced_min_tie_v1" / "theorem_verifier.json"


def select(priorities: list[int], protected: set[int], checksum: int) -> int:
    eligible = [i for i in range(len(priorities)) if i not in protected]
    best = min(priorities[i] for i in eligible)
    ties = [i for i in eligible if priorities[i] == best]
    return ties[checksum % len(ties)]


def main() -> None:
    modulus = 1 << 16
    modulo_counts: dict[str, list[int]] = {}
    for tie_count in range(1, 15):
        counts = [0] * tie_count
        for checksum in range(modulus):
            counts[checksum % tie_count] += 1
        assert max(counts) - min(counts) <= 1
        assert min(counts) == modulus // tie_count
        assert max(counts) == (modulus + tie_count - 1) // tie_count
        modulo_counts[str(tie_count)] = counts

    rng = random.Random(0xBADA55)
    cases = 0
    for associativity in (10, 14):
        for _ in range(10_000):
            priorities = [rng.randrange(256) for _ in range(associativity)]
            protected = set(rng.sample(range(associativity), rng.randrange(3)))
            checksum = rng.randrange(modulus)
            chosen = select(priorities, protected, checksum)
            eligible = [i for i in range(associativity) if i not in protected]
            assert chosen in eligible
            assert priorities[chosen] == min(priorities[i] for i in eligible)
            assert chosen == select(priorities, protected, checksum)
            cases += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema": "fxcm_balanced_min_tie_theorem_v1",
                "status": "pass",
                "checksum_values": modulus,
                "tie_counts_verified": list(range(1, 15)),
                "maximum_selection_imbalance": 1,
                "random_state_cases_verified": cases,
                "modulo_counts": modulo_counts,
                "score_credit_bytes": 0,
                "boundary": "Native compression and resource evidence remain required.",
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
