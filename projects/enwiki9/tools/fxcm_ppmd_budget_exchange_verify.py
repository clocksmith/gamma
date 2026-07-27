#!/usr/bin/env python3
import json


CELL_COUNT = 27_955_200
OLD_CELL_BYTES = 96
NEW_CELL_BYTES = 92
OLD_PPMD_KIB = 20_352
BYTES_PER_KIB = 1_024


def main() -> None:
    released = (OLD_CELL_BYTES - NEW_CELL_BYTES) * CELL_COUNT
    added_kib, residue = divmod(released, BYTES_PER_KIB)
    new_ppmd_kib = OLD_PPMD_KIB + added_kib
    old_payload = OLD_CELL_BYTES * CELL_COUNT + OLD_PPMD_KIB * BYTES_PER_KIB
    new_payload = NEW_CELL_BYTES * CELL_COUNT + new_ppmd_kib * BYTES_PER_KIB
    assert new_payload <= old_payload
    assert (
        NEW_CELL_BYTES * CELL_COUNT
        + (new_ppmd_kib + 1) * BYTES_PER_KIB
        > old_payload
    )
    result = {
        "schema": "fxcm_ppmd_budget_exchange_verifier_v1",
        "cell_count": CELL_COUNT,
        "old_cell_bytes": OLD_CELL_BYTES,
        "new_cell_bytes": NEW_CELL_BYTES,
        "released_bytes": released,
        "old_ppmd_kib": OLD_PPMD_KIB,
        "added_ppmd_kib": added_kib,
        "new_ppmd_kib": new_ppmd_kib,
        "residual_budget_bytes": residue,
        "old_combined_payload_bytes": old_payload,
        "new_combined_payload_bytes": new_payload,
        "maximality_verified": True,
        "score_credit_bytes": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
