#!/usr/bin/env python3
import json


BASE_CELLS = 27_955_200
OLD_CELL_BYTES = 96
NEW_CELL_BYTES = 92
RESTORED_CELLS = 2_097_152


def main() -> None:
    released = (OLD_CELL_BYTES - NEW_CELL_BYTES) * BASE_CELLS
    restoration = NEW_CELL_BYTES * RESTORED_CELLS
    delta = restoration - released
    old_payload = OLD_CELL_BYTES * BASE_CELLS
    new_cells = BASE_CELLS + RESTORED_CELLS
    new_payload = NEW_CELL_BYTES * new_cells
    assert new_payload - old_payload == delta
    result = {
        "schema": "fxcm_slack_funded_restoration_verifier_v1",
        "base_cells": BASE_CELLS,
        "restored_cells": RESTORED_CELLS,
        "new_total_cells": new_cells,
        "old_cell_bytes": OLD_CELL_BYTES,
        "new_cell_bytes": NEW_CELL_BYTES,
        "released_bytes": released,
        "restoration_bytes": restoration,
        "net_payload_increase_bytes": delta,
        "old_payload_bytes": old_payload,
        "new_payload_bytes": new_payload,
        "payload_identity_verified": True,
        "rss_credit_bytes": 0,
        "score_credit_bytes": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
