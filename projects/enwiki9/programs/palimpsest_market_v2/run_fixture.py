#!/usr/bin/env python3
"""Run deterministic source-only PALIMPSEST market and finite-coder fixtures."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from core import (
    DelimiterSubstitutionKernel,
    MarketRoute,
    NumericAffineKernel,
    PalimpsestMarket,
    PhysicalDonor,
    PrefixSuffixGraftingKernel,
    RouteId,
    TokenAlignmentKernel,
    conditional_p1,
    splitmix64,
)
from finite_coder import (
    CODED_ARMS,
    CounterfactualReplay,
    decode_schedule,
    encode_schedule,
)


EXPECTED_RUN_SHA256 = (
    "a0614457cd000abf604fbe333458fe883d55a44a4f2bb4bd62d2be61147c82fa"
)
EXPECTED_STATE_SHA256 = (
    "0e04ebc63068c29a2a522142f56ae79c0fb8f8de460bab910eefa3f9e2306885"
)
EXPECTED_A_IDENTITY_SHA256 = (
    "6bb3fd3b0d1309d0a6603cc0f5453e7c71ac04a6beffd97a7ac29af7a0706088"
)


def _load_harm_core():
    path = (
        Path(__file__).resolve().parents[1]
        / "harm_route_edit_residual_shadow_q0_v1/core.py"
    )
    spec = importlib.util.spec_from_file_location("_palimpsest_harm_reference", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen HARM reference")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _occurrence(ordinal: int) -> tuple[int, ...]:
    return (1, ordinal, 0, 0, 0, 0)


def _install(
    model: PalimpsestMarket,
    route: MarketRoute,
    value: bytes,
    ordinal: int,
    entry_coordinate: int,
    completion_coordinate: int,
) -> None:
    occurrence = _occurrence(ordinal)
    model.enter(occurrence, route, entry_coordinate)
    if ordinal % 2 and len(value) > 1:
        for truth in value[:-1]:
            model.commit_byte(occurrence, truth)
        model.exit(occurrence, len(value), completion_coordinate)
        model.commit_byte(occurrence, value[-1])
    else:
        for truth in value:
            model.commit_byte(occurrence, truth)
        model.exit(occurrence, len(value), completion_coordinate)


def _harm_a_identity() -> dict[str, object]:
    harm_core = _load_harm_core()
    harm = harm_core.HarmDelta()
    market = PalimpsestMarket()
    harm_route = harm_core.RouteId(0x10, 0x20, 0x30, 0x40)
    market_route = MarketRoute(RouteId(0x10, 0x20, 0x30, 0x40), 0x50)
    first = (1, 0x10, 0x20, 0x30, 0x40, 0)
    harm.enter(first, harm_route, occurrence_seed=7)
    market.enter(first, market_route, coordinate=10)
    for truth in b"alpha-beta":
        harm.commit_byte(first, truth)
        market.commit_byte(first, truth)
    harm.exit(first, expected_commits=10)
    market.exit(first, expected_commits=10, completion_coordinate=30)

    second = (1, 0x10, 0x20, 0x30, 0x40, 1)
    harm.enter(second, harm_route, occurrence_seed=8)
    market.enter(second, market_route, coordinate=100)
    digest = hashlib.sha256()
    identity = True
    for ordinal, truth in enumerate(b"alphaX-beta"):
        parent = tuple(28000 + ((ordinal * 977 + bit * 313) % 9000) for bit in range(8))
        harm_rows = harm.score_byte(second, parent, truth)
        market_rows = market.score_byte(second, parent, truth)
        identity &= harm_rows["candidate_E"] == market_rows["candidate_A"]
        identity &= harm_rows["mixture_E"] == market_rows["mixture_A"]
        identity &= market_rows["P"] == market_rows["K"] == parent
        for probability in market_rows["mixture_A"]:
            digest.update(probability.to_bytes(2, "little"))
        harm.commit_byte(second, truth)
        market.commit_byte(second, truth)
    harm.exit(second, expected_commits=11)
    market.exit(second, expected_commits=11, completion_coordinate=130)
    return {
        "pass": identity,
        "probability_sha256": digest.hexdigest(),
    }


def _physical_value(value: bytes, ordinal: int) -> bytes:
    if value.isdigit():
        modulus = 10 ** len(value)
        return str((int(value) + 37 * (ordinal + 1)) % modulus).zfill(
            len(value)
        ).encode("ascii")
    return bytes((byte ^ ((ordinal % 7) + 1)) for byte in value)


def _typed_kernel_fixture() -> dict[str, object]:
    cases = (
        (NumericAffineKernel(b"2025"), b"2026"),
        (DelimiterSubstitutionKernel(b"aa::bb"), b"cc::dd"),
        (TokenAlignmentKernel(b"alpha beta"), b"alpha gamma"),
        (PrefixSuffixGraftingKernel(b"prefix-suffix"), b"suffix"),
    )
    digest = hashlib.sha256()
    awake = {}
    for kernel, truth_value in cases:
        observed = 0
        for truth in truth_value:
            histogram = kernel.histogram()
            if histogram is None:
                break
            prefix = 0
            for bit_index in range(8):
                probability = conditional_p1(histogram, prefix, bit_index)
                digest.update(probability.to_bytes(2, "little"))
                prefix = (prefix << 1) | ((truth >> (7 - bit_index)) & 1)
            kernel.observe(truth)
            observed += 1
        awake[kernel.kernel_name] = observed
        digest.update(kernel.digest_bytes())
    return {"observed_bytes": awake, "sha256": digest.hexdigest()}


def _finite_coder_stress_fixture() -> dict[str, object]:
    probabilities = []
    truths = []
    state = 0x123456789ABCDEF0
    for _ in range(4096):
        state = splitmix64(state)
        probabilities.append(1 + state % 65535)
        state = splitmix64(state)
        truths.append((state >> 63) & 1)
    archive = encode_schedule(probabilities, truths)
    decoded = decode_schedule(archive, probabilities)
    return {
        "bit_count": len(truths),
        "archive_bytes": len(archive),
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "roundtrip_pass": decoded == tuple(truths),
    }


def _build_market() -> tuple[PalimpsestMarket, MarketRoute, int, int]:
    model = PalimpsestMarket()
    target = MarketRoute(RouteId(1, 2, 3, 4), 0xABC)
    ordinal = 100
    coordinate = 1000

    for index in range(8):
        _install(
            model,
            target,
            f"20260{index:03d}".encode("ascii"),
            ordinal,
            coordinate,
            coordinate + 40,
        )
        ordinal += 1
        companion = MarketRoute(
            RouteId(500 + index, 31, 41, 51), 0xC00 + index
        )
        _install(
            model,
            companion,
            f"20640{index:03d}".encode("ascii"),
            ordinal,
            coordinate + 100,
            coordinate + 140,
        )
        ordinal += 1
        coordinate += 1000

    for index in range(8):
        route = MarketRoute(RouteId(20 + index, 30, 40, 50), target.shape_id)
        _install(
            model,
            route,
            f"20310{index:03d}".encode("ascii"),
            ordinal,
            coordinate,
            coordinate + 40,
        )
        ordinal += 1
        coordinate += 1000

    for index in range(8):
        route = MarketRoute(RouteId(60 + index, 70, 80, 90), 0xD00 + index)
        _install(
            model,
            route,
            f"20420{index:03d}".encode("ascii"),
            ordinal,
            coordinate,
            coordinate + 40,
        )
        ordinal += 1
        coordinate += 1000

    for index in range(48):
        route = MarketRoute(RouteId(1000 + index, 71, 81, 91), 0xE00 + index)
        _install(
            model,
            route,
            f"20530{index % 1000:03d}".encode("ascii"),
            ordinal,
            coordinate,
            coordinate + 40,
        )
        ordinal += 1
        coordinate += 250
    return model, target, ordinal, coordinate + 100000


def run_once() -> dict[str, object]:
    identity = _harm_a_identity()
    model, target, ordinal, coordinate = _build_market()
    replay = CounterfactualReplay()
    admissible = {"X": True, "G": True}

    for field in range(1):
        choices = model.preview_h_choices(target, coordinate)
        physical = tuple(
            PhysicalDonor(_physical_value(choice.record.value, index), choice.age)
            for index, choice in enumerate(choices)
        )
        occurrence = _occurrence(ordinal)
        model.enter(occurrence, target, coordinate, physical)
        current = model.occurrences[occurrence]
        for control in admissible:
            admissible[control] &= current.controls_admissible[control]
        truth_value = f"2026{9000 + field:04d}".encode("ascii")
        for byte_index, truth in enumerate(truth_value):
            parent = tuple(
                24576 + ((field * 811 + byte_index * 353 + bit * 101) % 16384)
                for bit in range(8)
            )
            rows = model.score_byte(occurrence, parent, truth)
            if rows["P"] != rows["K"]:
                raise AssertionError("P/K probability identity failure")
            replay.observe_byte(rows, truth)
            model.commit_byte(occurrence, truth)
        model.exit(
            occurrence,
            expected_commits=len(truth_value),
            completion_coordinate=coordinate + 64,
        )
        ordinal += 1
        coordinate += 1000

    finite = replay.finish()
    if not all(finite["roundtrip"].values()):
        raise AssertionError("finite arithmetic roundtrip failure")
    if finite["archive_sha256"]["P"] != finite["archive_sha256"]["K"]:
        raise AssertionError("P/K finite payload identity failure")
    if finite["interval_sha256"]["P"] != finite["interval_sha256"]["K"]:
        raise AssertionError("P/K finite interval identity failure")
    kernel_fixture = _typed_kernel_fixture()
    coder_stress = _finite_coder_stress_fixture()
    if not coder_stress["roundtrip_pass"]:
        raise AssertionError("finite arithmetic stress roundtrip failure")
    result = {
        "a_harm_identity": identity,
        "controls_admissible": admissible,
        "bit_count": finite["bit_count"],
        "archive_bytes": finite["archive_bytes"],
        "archive_sha256": finite["archive_sha256"],
        "interval_sha256": finite["interval_sha256"],
        "roundtrip": finite["roundtrip"],
        "p_k_payload_identity": (
            finite["archive_sha256"]["P"] == finite["archive_sha256"]["K"]
        ),
        "p_k_interval_identity": (
            finite["interval_sha256"]["P"] == finite["interval_sha256"]["K"]
        ),
        "all_arms_exercised": all(
            finite["interval_sha256"][arm] != finite["interval_sha256"]["P"]
            for arm in CODED_ARMS
            if arm not in ("P", "K")
        ),
        "state_sha256": model.state_digest(),
        "typed_kernel_fixture": kernel_fixture,
        "finite_coder_stress_fixture": coder_stress,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["run_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


def main() -> int:
    first = run_once()
    second = run_once()
    repeat = first == second
    known = (
        first["run_sha256"] == EXPECTED_RUN_SHA256
        and first["state_sha256"] == EXPECTED_STATE_SHA256
        and first["a_harm_identity"]["probability_sha256"]
        == EXPECTED_A_IDENTITY_SHA256
    )
    result = {
        "schema": "gamma.enwiki9.palimpsest-market-source-fixture.v2",
        "candidate_id": "palimpsest_market_v2",
        "repeat_identity_pass": repeat,
        "known_answer_pass": known,
        "run": first,
        "archive_authority": False,
        "objective_credit_bytes": 0,
        "corpus_access": False,
        "native_authorized": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if repeat and known else 2


if __name__ == "__main__":
    raise SystemExit(main())
