#!/usr/bin/env python3
import json


OLD_BYTES = 96
NEW_BYTES = 92
OLD_COUNTS = [
    2097152, 4194304, 2097152, 2097152, 2097152, 2097152,
    4096, 524288, 1048576, 2097152, 2097152, 2097152,
    2097152, 2097152, 524288, 32768, 131072, 524288,
]


def main() -> None:
    new_counts = [(OLD_BYTES * n) // NEW_BYTES for n in OLD_COUNTS]
    residues = [
        OLD_BYTES * n - NEW_BYTES * m
        for n, m in zip(OLD_COUNTS, new_counts)
    ]
    assert all(m >= n for n, m in zip(OLD_COUNTS, new_counts))
    assert all(
        NEW_BYTES * m <= OLD_BYTES * n
        for n, m in zip(OLD_COUNTS, new_counts)
    )
    assert all(
        NEW_BYTES * (m + 1) > OLD_BYTES * n
        for n, m in zip(OLD_COUNTS, new_counts)
    )
    assert all(0 <= residue < NEW_BYTES for residue in residues)
    added = sum(new_counts) - sum(OLD_COUNTS)
    assert added == sum(n // 23 for n in OLD_COUNTS)
    result = {
        "schema": "fxcm_budget_preserving_capacity_verifier_v1",
        "old_cell_bytes": OLD_BYTES,
        "new_cell_bytes": NEW_BYTES,
        "old_counts": OLD_COUNTS,
        "new_counts": new_counts,
        "old_total_cells": sum(OLD_COUNTS),
        "new_total_cells": sum(new_counts),
        "added_cells": added,
        "old_payload_bytes": OLD_BYTES * sum(OLD_COUNTS),
        "new_payload_bytes": NEW_BYTES * sum(new_counts),
        "residual_slack_bytes": sum(residues),
        "maximality_verified": True,
        "score_credit_bytes": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
