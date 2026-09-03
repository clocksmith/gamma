#!/usr/bin/env python3
"""Run deterministic source-only HARM-Delta fixtures; no corpus is opened."""

from __future__ import annotations

import hashlib
import json

from core import HarmDelta, RouteId

EXPECTED_PROBABILITY_SHA256 = (
    "8ba2a030e57ad0399b98a33cfe9a691517d4e975bb82638da79b5fb46824689d"
)
EXPECTED_STATE_SHA256 = (
    "2bfa5c120b9293d22c0b7ee76af125da055e362116433cc4ca4d8b4b7813c334"
)


def run_once() -> dict[str, object]:
    model = HarmDelta()
    route = RouteId(0x10, 0x20, 0x30, 0x40)
    first = (1, 0x10, 0x20, 0x30, 0x40, 0)
    model.enter(first, route, occurrence_seed=100)
    for byte in b"alpha-beta":
        model.commit_byte(first, byte)
    model.exit(first, expected_commits=10)

    second = (1, 0x10, 0x20, 0x30, 0x40, 1)
    model.enter(second, route, occurrence_seed=101)
    probability_bytes = bytearray()
    for byte in b"alphaX-beta":
        rows = model.score_byte(second, [32768] * 8, byte)
        if rows["P"] != rows["K"]:
            raise AssertionError("P/K probability identity failure")
        for arm in ("L", "E", "G", "S", "R", "N"):
            for count in rows[f"mixture_{arm}"]:
                probability_bytes.extend(int(count).to_bytes(2, "little"))
        model.commit_byte(second, byte)
    model.exit(second, expected_commits=11)
    return {
        "probability_sha256": hashlib.sha256(probability_bytes).hexdigest(),
        "state_sha256": model.state_digest(),
        "probability_bytes": len(probability_bytes),
        "p_k_identity": True,
        "route_value": model.route_bank.get(route).decode("ascii"),
    }


def main() -> int:
    first = run_once()
    second = run_once()
    repeat = first == second
    known_answer = (
        first["probability_sha256"] == EXPECTED_PROBABILITY_SHA256
        and first["state_sha256"] == EXPECTED_STATE_SHA256
    )
    result = {
        "schema": "gamma.enwiki9.harm-delta-source-fixture.v1",
        "candidate_id": "harm_route_edit_residual_shadow_q0_v1",
        "repeat_identity_pass": repeat,
        "known_answer_pass": known_answer,
        "run": first,
        "archive_authority": False,
        "objective_credit_bytes": 0,
        "corpus_access": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if repeat and known_answer else 2


if __name__ == "__main__":
    raise SystemExit(main())
