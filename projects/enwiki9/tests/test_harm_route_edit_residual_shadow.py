from __future__ import annotations

import importlib.util
import hashlib
import math
from pathlib import Path
import struct
import sys
import tempfile


CORE = (
    Path(__file__).resolve().parents[1]
    / "programs/harm_route_edit_residual_shadow_q0_v1/core.py"
)
ADAPTER = (
    Path(__file__).resolve().parents[1]
    / "programs/harm_route_edit_residual_shadow_q0_v1/callback_adapter.py"
)


def load_core():
    spec = importlib.util.spec_from_file_location("_harm_delta_core_test", CORE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_adapter():
    core = load_core()
    sys.modules["core"] = core
    spec = importlib.util.spec_from_file_location("_harm_delta_adapter_test", ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_edit_transducer_tracks_one_insertion_beyond_lockstep() -> None:
    core = load_core()
    donor = b"abcdefghi"
    truth = b"abcXdefghi"
    edit = core.EditTransducer(donor)
    lock = core.LockstepTransducer(donor)
    edit_bits = 0.0
    lock_bits = 0.0
    for value in truth:
        edit_hist = edit.histogram()
        lock_hist = lock.histogram()
        if edit_hist is not None:
            edit_bits -= math.log2(edit_hist[value] / sum(edit_hist))
        if lock_hist is not None:
            lock_bits -= math.log2(lock_hist[value] / sum(lock_hist))
        edit.observe(value)
        lock.observe(value)
    assert edit.last_mode_mass["I"] > 0
    assert edit_bits < lock_bits


def test_edit_transducer_tracks_one_silent_donor_deletion() -> None:
    core = load_core()
    donor = b"abcXdefghi"
    truth = b"abcdefghi"
    edit = core.EditTransducer(donor)
    lock = core.LockstepTransducer(donor)
    edit_bits = 0.0
    lock_bits = 0.0
    for value in truth:
        edit_hist = edit.histogram()
        lock_hist = lock.histogram()
        assert edit_hist is not None
        edit_bits -= math.log2(edit_hist[value] / sum(edit_hist))
        if lock_hist is not None:
            lock_bits -= math.log2(lock_hist[value] / sum(lock_hist))
        edit.observe(value)
        lock.observe(value)
    assert any(offset > 0 for offset, _ in edit.weights)
    assert edit_bits < lock_bits


def test_edit_rows_are_exact_probability_rows() -> None:
    core = load_core()
    assert all(sum(row.values()) == 256 for row in core.TRANSITIONS.values())
    assert all(
        donor + 255 * other == core.PROBABILITY_SCALE
        for donor, other in core.EMISSIONS.values()
    )


def test_candidate_probabilities_are_pretruth_and_normalized() -> None:
    core = load_core()
    edit = core.EditTransducer(b"same value")
    histogram = edit.histogram()
    assert histogram is not None
    assert len(histogram) == 256
    assert min(histogram) > 0
    prefix = 0
    truth = ord("s")
    probabilities = []
    for bit_index in range(8):
        probabilities.append(core.conditional_p1(histogram, prefix, bit_index))
        prefix = (prefix << 1) | ((truth >> (7 - bit_index)) & 1)
    assert all(0 < probability < core.PROBABILITY_SCALE for probability in probabilities)


def test_negated_arm_is_exact_distribution_reflection() -> None:
    core = load_core()
    edit = core.EditTransducer(b"A")
    histogram = edit.histogram()
    assert histogram is not None
    negated = core.complement_histogram(histogram)
    for value in range(256):
        assert negated[value] == histogram[value ^ 0xFF]
    assert sum(negated) == sum(histogram)


def test_sleeping_mixture_is_exactly_parent_neutral() -> None:
    core = load_core()
    mixture = core.SleepingMixture()
    before = mixture.parent_weight
    assert mixture.predict(12345, None) == 12345
    mixture.observe(12345, None, 1)
    assert mixture.parent_weight == before
    assert mixture.awake_updates == 0
    for invalid in (0, core.PROBABILITY_SCALE):
        try:
            mixture.predict(invalid, None)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid sleeping parent probability accepted")


def test_route_value_is_not_installed_until_field_exit_and_commits() -> None:
    core = load_core()
    harm = core.HarmDelta()
    route = core.RouteId(1, 2, 3, 4)
    occurrence = (1, 1, 2, 3, 4, 0)
    harm.enter(occurrence, route, occurrence_seed=11)
    harm.commit_byte(occurrence, ord("a"))
    assert harm.route_bank.get(route) is None
    harm.exit(occurrence, expected_commits=2)
    assert harm.route_bank.get(route) is None
    harm.commit_byte(occurrence, ord("b"))
    assert harm.route_bank.get(route) == b"ab"


def test_overflowing_value_is_retired_after_exact_commit_count() -> None:
    core = load_core()
    harm = core.HarmDelta()
    route = core.RouteId(4, 3, 2, 1)
    occurrence = (1, 4, 3, 2, 1, 0)
    harm.enter(occurrence, route, occurrence_seed=17)
    expected = core.MAX_VALUE_BYTES + 3
    for _ in range(expected - 1):
        harm.commit_byte(occurrence, ord("z"))
    harm.exit(occurrence, expected_commits=expected)
    assert occurrence in harm.occurrences
    harm.commit_byte(occurrence, ord("z"))
    assert occurrence not in harm.occurrences
    assert harm.route_bank.get(route) is None


def test_expert_sleeps_before_byte_513_and_active_fields_are_bounded() -> None:
    core = load_core()
    harm = core.HarmDelta()
    route = core.RouteId(14, 13, 12, 11)
    harm.route_bank.put(route, b"z" * core.MAX_VALUE_BYTES)
    occurrence = (1, 14, 13, 12, 11, 0)
    harm.enter(occurrence, route, occurrence_seed=1)
    for _ in range(core.MAX_VALUE_BYTES):
        harm.commit_byte(occurrence, ord("z"))
    assert harm.candidate_histograms(occurrence)["E"] is None

    bounded = core.HarmDelta()
    for ordinal in range(core.MAX_ACTIVE_OCCURRENCES):
        bounded.enter(
            (1, ordinal, 0, 0, 0, 0),
            core.RouteId(ordinal, 0, 0, 0),
            occurrence_seed=ordinal,
        )
    try:
        bounded.enter((9, 9, 9, 9, 9, 9), core.RouteId(99, 0, 0, 0), 99)
    except MemoryError:
        pass
    else:
        raise AssertionError("active occurrence ceiling was not enforced")


def test_l_e_n_and_bookkeeping_have_frozen_roles() -> None:
    core = load_core()
    harm = core.HarmDelta()
    route = core.RouteId(9, 8, 7, 6)
    first = (1, 9, 8, 7, 6, 0)
    harm.enter(first, route, occurrence_seed=1)
    for value in b"abcd":
        harm.commit_byte(first, value)
    harm.exit(first, expected_commits=4)

    second = (1, 9, 8, 7, 6, 1)
    harm.enter(second, route, occurrence_seed=2)
    histograms = harm.candidate_histograms(second)
    assert histograms["L"] is not None
    assert histograms["E"] is not None
    assert histograms["N"] == core.complement_histogram(histograms["E"])
    rows = harm.score_byte(second, [32768] * 8, ord("a"))
    assert rows["P"] == rows["K"] == tuple([32768] * 8)
    assert rows["candidate_L"] != tuple([32768] * 8)
    assert rows["mixture_E"] != tuple([32768] * 8)
    assert "N" not in harm.mixtures


def test_negated_arm_uses_es_live_pretruth_weight_without_state() -> None:
    core = load_core()
    harm = core.HarmDelta()
    route = core.RouteId(19, 18, 17, 16)
    harm.route_bank.put(route, b"A")
    occurrence = (1, 19, 18, 17, 16, 0)
    harm.enter(occurrence, route, occurrence_seed=1)
    histogram = harm.candidate_histograms(occurrence)["N"]
    assert histogram is not None
    candidate = core.conditional_p1(histogram, 0, 0)
    expected = core.mixture_p1(
        harm.mixtures["E"].parent_weight, 32768, candidate
    )
    rows = harm.score_byte(occurrence, [32768] * 8, ord("A"))
    assert rows["mixture_N"][0] == expected
    assert set(harm.mixtures) == set(harm.MIXTURE_ARMS)


def test_integer_mixture_matches_direct_ratio() -> None:
    core = load_core()
    weight = core.POSTERIOR_SCALE // 3
    observed = core.mixture_p1(weight, 50000, 10000)
    numerator = weight * 50000 + (core.POSTERIOR_SCALE - weight) * 10000
    quotient, remainder = divmod(numerator, core.POSTERIOR_SCALE)
    expected = quotient + (1 if remainder * 2 >= core.POSTERIOR_SCALE else 0)
    assert observed == expected


def test_q63_boundaries_and_posterior_match_unbounded_reference() -> None:
    core = load_core()
    for weight in (1, core.POSTERIOR_SCALE // 2, core.POSTERIOR_SCALE - 1):
        for parent in (1, 32768, core.PROBABILITY_SCALE - 1):
            for candidate in (1, 12345, core.PROBABILITY_SCALE - 1):
                mixed = core.mixture_p1(weight, parent, candidate)
                numerator = (
                    weight * parent
                    + (core.POSTERIOR_SCALE - weight) * candidate
                )
                quotient, remainder = divmod(numerator, core.POSTERIOR_SCALE)
                expected = quotient + (
                    1 if remainder * 2 >= core.POSTERIOR_SCALE else 0
                )
                expected = max(1, min(core.PROBABILITY_SCALE - 1, expected))
                assert mixed == expected
                for truth in (0, 1):
                    parent_truth = (
                        parent if truth else core.PROBABILITY_SCALE - parent
                    )
                    candidate_truth = (
                        candidate if truth
                        else core.PROBABILITY_SCALE - candidate
                    )
                    parent_mass = weight * parent_truth
                    total_mass = parent_mass + (
                        core.POSTERIOR_SCALE - weight
                    ) * candidate_truth
                    quotient, remainder = divmod(
                        parent_mass * core.POSTERIOR_SCALE, total_mass
                    )
                    expected_weight = quotient + (
                        1 if remainder * 2 >= total_mass else 0
                    )
                    expected_weight = max(
                        1, min(core.POSTERIOR_SCALE - 1, expected_weight)
                    )
                    assert core.posterior_parent_weight(
                        weight, parent, candidate, truth
                    ) == expected_weight


def test_twin_futures_match_until_first_different_truth() -> None:
    core = load_core()

    def prepared():
        harm = core.HarmDelta()
        route = core.RouteId(11, 22, 33, 44)
        first = (1, 11, 22, 33, 44, 0)
        harm.enter(first, route, occurrence_seed=1)
        for value in b"route-value":
            harm.commit_byte(first, value)
        harm.exit(first, expected_commits=11)
        active = (1, 11, 22, 33, 44, 1)
        harm.enter(active, route, occurrence_seed=2)
        return harm, active

    left, left_id = prepared()
    right, right_id = prepared()
    assert left.state_digest() == right.state_digest()
    for value in b"route-":
        assert (
            left.candidate_histograms(left_id)
            == right.candidate_histograms(right_id)
        )
        left.score_byte(left_id, [30000] * 8, value)
        right.score_byte(right_id, [30000] * 8, value)
        left.commit_byte(left_id, value)
        right.commit_byte(right_id, value)
    assert left.state_digest() == right.state_digest()
    assert left.candidate_histograms(left_id) == right.candidate_histograms(right_id)
    left.score_byte(left_id, [30000] * 8, ord("A"))
    right.score_byte(right_id, [30000] * 8, ord("B"))
    left.commit_byte(left_id, ord("A"))
    right.commit_byte(right_id, ord("B"))
    assert left.state_digest() != right.state_digest()


def test_state_digest_closes_donor_and_shifted_route_state() -> None:
    core = load_core()
    route = core.RouteId(51, 52, 53, 54)
    occurrence = (1, 51, 52, 53, 54, 0)
    left = core.HarmDelta()
    right = core.HarmDelta()
    left.enter(occurrence, route, 1, physical_donor=b"AAAA")
    right.enter(occurrence, route, 1, physical_donor=b"BBBB")
    assert left.state_digest() != right.state_digest()

    preceding = core.RouteId(61, 62, 63, 64)
    shifted = core.HarmDelta()
    first = (1, 61, 62, 63, 64, 0)
    shifted.enter(first, preceding, 1)
    shifted.commit_byte(first, ord("q"))
    shifted.exit(first, 1)
    second = (1, 71, 72, 73, 74, 0)
    shifted.enter(second, core.RouteId(71, 72, 73, 74), 2)
    assert shifted.occurrences[second].transducers["S"].donor == b"q"


def test_restricted_callback_replay_ignores_posttruth_raw_after() -> None:
    adapter = load_adapter()
    route = (101, 202, 303, 404)

    def row(source, availability, virtual, event, raw_after):
        return adapter.TapeRow(
            source=source,
            availability=availability,
            first_bit=availability * 8,
            raw_before=0,
            raw_after=raw_after,
            route_lo=route[0],
            route_hi=route[1],
            witness_lo=route[2],
            witness_hi=route[3],
            virtual_ordinal=virtual,
            field_ordinal=0,
            event_type=event,
            flags=adapter.EXPECTED_FLAGS[event],
            depth=1,
            key_identity=adapter.EXPECTED_KEY_IDENTITY[event],
        )

    stream = b"MabQMabQ"
    base_rows = [
        row(0, 1, 0, adapter.EVENT_EXPLICIT_FIELD_ENTRY, 1),
        row(1, 1, 0, adapter.EVENT_FIELD_VALUE_BYTE, 2),
        row(2, 2, 1, adapter.EVENT_FIELD_VALUE_BYTE, 3),
        row(3, 3, 2, adapter.EVENT_FIELD_VALUE_BYTE, 4),
        row(3, 4, 2, adapter.EVENT_FIELD_EXIT, 4),
        row(4, 5, 2, adapter.EVENT_EXPLICIT_FIELD_ENTRY, 5),
        row(5, 5, 2, adapter.EVENT_FIELD_VALUE_BYTE, 6),
        row(6, 6, 3, adapter.EVENT_FIELD_VALUE_BYTE, 7),
        row(7, 7, 4, adapter.EVENT_FIELD_VALUE_BYTE, 8),
        row(7, 8, 4, adapter.EVENT_FIELD_EXIT, 8),
    ]
    altered_rows = [
        adapter.TapeRow(
            **{**record.__dict__, "raw_after": record.raw_after + 9999}
        )
        for record in base_rows
    ]
    parent = lambda coordinate: tuple([32768] * 8)
    first = adapter.replay(stream, base_rows, parent)
    second = adapter.replay(stream, altered_rows, parent)
    assert first == second
    assert first["active_bytes"] == 6
    assert first["arm_awake_bytes"]["E"] == 3


def test_opening_population_cannot_fake_physical_control() -> None:
    adapter = load_adapter()
    # The absence of a separately frozen source-coordinate provider keeps G
    # asleep; opening-only evidence therefore cannot satisfy E > G.
    route = (7, 8, 9, 10)
    rows = [
        adapter.TapeRow(0, 1, 8, 0, 1, *route, 0, 0, 2, 137, 1, 1),
        adapter.TapeRow(1, 1, 8, 1, 2, *route, 0, 0, 3, 11, 1, 1),
        adapter.TapeRow(2, 2, 16, 2, 3, *route, 1, 0, 3, 11, 1, 1),
        adapter.TapeRow(2, 3, 24, 2, 3, *route, 1, 0, 5, 137, 1, 1),
    ]
    result = adapter.replay(b"MZQ", rows, lambda coordinate: tuple([32768] * 8))
    assert result["arm_awake_bytes"]["G"] == 0


def test_measurement_scope_preserves_warm_route_and_mixture_state() -> None:
    adapter = load_adapter()
    route = (41, 42, 43, 44)

    def row(source, availability, virtual, event):
        return adapter.TapeRow(
            source, availability, availability * 8, 0, 0, *route,
            virtual, 0, event,
            adapter.EXPECTED_FLAGS[event],
            1, adapter.EXPECTED_KEY_IDENTITY[event],
        )

    stream = b"MaaQMaaQ"
    rows = [
        row(0, 1, 0, adapter.EVENT_EXPLICIT_FIELD_ENTRY),
        row(1, 1, 0, adapter.EVENT_FIELD_VALUE_BYTE),
        row(2, 2, 1, adapter.EVENT_FIELD_VALUE_BYTE),
        row(3, 3, 2, adapter.EVENT_FIELD_VALUE_BYTE),
        row(3, 4, 2, adapter.EVENT_FIELD_EXIT),
        row(4, 5, 2, adapter.EVENT_EXPLICIT_FIELD_ENTRY),
        row(5, 5, 2, adapter.EVENT_FIELD_VALUE_BYTE),
        row(6, 6, 3, adapter.EVENT_FIELD_VALUE_BYTE),
        row(7, 7, 4, adapter.EVENT_FIELD_VALUE_BYTE),
        row(7, 8, 4, adapter.EVENT_FIELD_EXIT),
    ]
    result = adapter.replay(
        stream,
        rows,
        lambda coordinate: tuple([32768] * 8),
        measure_start=5,
        measure_end=8,
    )
    assert result["measure_start_wrt"] == 5
    assert result["measure_end_wrt"] == 8
    assert result["active_bytes"] == 3
    assert result["arm_awake_bytes"]["E"] == 3


def test_missing_deferred_literal_is_rejected() -> None:
    adapter = load_adapter()
    route = (81, 82, 83, 84)

    def row(source, availability, virtual, event):
        return adapter.TapeRow(
            source, availability, availability * 8, 0, 0, *route,
            virtual, 0, event, adapter.EXPECTED_FLAGS[event], 1,
            adapter.EXPECTED_KEY_IDENTITY[event],
        )

    rows = [
        row(0, 1, 0, adapter.EVENT_EXPLICIT_FIELD_ENTRY),
        row(1, 1, 0, adapter.EVENT_FIELD_VALUE_BYTE),
        row(2, 2, 0, adapter.EVENT_FIELD_VALUE_BYTE),
    ]
    try:
        adapter.replay(b"MPA", rows, lambda coordinate: tuple([32768] * 8))
    except ValueError as error:
        assert "missing deferred" in str(error)
    else:
        raise AssertionError("missing deferred literal callback accepted")


def test_duplicate_deferred_literal_is_rejected_before_second_commit() -> None:
    adapter = load_adapter()
    route = (85, 86, 87, 88)

    def row(source, availability, virtual, event):
        return adapter.TapeRow(
            source, availability, availability * 8, 0, 0, *route,
            virtual, 0, event, adapter.EXPECTED_FLAGS[event], 1,
            adapter.EXPECTED_KEY_IDENTITY[event],
        )

    deferred = row(1, 3, 0, adapter.EVENT_DEFERRED_VALUE_UPDATE)
    rows = [
        row(0, 1, 0, adapter.EVENT_EXPLICIT_FIELD_ENTRY),
        row(1, 1, 0, adapter.EVENT_FIELD_VALUE_BYTE),
        row(2, 2, 0, adapter.EVENT_FIELD_VALUE_BYTE),
        deferred,
        deferred,
    ]
    try:
        adapter.replay(b"MPA", rows, lambda coordinate: tuple([32768] * 8))
    except ValueError as error:
        assert "duplicate deferred" in str(error)
    else:
        raise AssertionError("duplicate deferred literal callback accepted")


def test_malformed_gsrt_flags_delta_and_priority_are_rejected() -> None:
    adapter = load_adapter()
    base = adapter.TapeRow(
        1, 1, 8, 0, 0, 1, 2, 3, 4, 0, 0,
        adapter.EVENT_FIELD_VALUE_BYTE,
        adapter.EXPECTED_FLAGS[adapter.EVENT_FIELD_VALUE_BYTE], 1, 1,
    )
    for changed in (
        {"flags": 0},
        {"key_identity": 2},
        {"availability": 2, "first_bit": 16},
    ):
        row = adapter.TapeRow(**{**base.__dict__, **changed})
        try:
            adapter.validate_tape_row(row, 4)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed GSRT callback accepted")

    deferred = adapter.TapeRow(
        0, 2, 16, 0, 0, 1, 2, 3, 4, 0, 0,
        adapter.EVENT_DEFERRED_VALUE_UPDATE,
        adapter.EXPECTED_FLAGS[adapter.EVENT_DEFERRED_VALUE_UPDATE], 1, 1,
    )
    structural = adapter.TapeRow(
        1, 2, 16, 0, 0, 1, 2, 3, 4, 0, 0,
        adapter.EVENT_FIELD_EXIT,
        adapter.EXPECTED_FLAGS[adapter.EVENT_FIELD_EXIT], 1, 1,
    )
    try:
        adapter.replay(
            b"ab", [structural, deferred],
            lambda coordinate: tuple([32768] * 8),
        )
    except ValueError as error:
        assert "priority" in str(error)
    else:
        raise AssertionError("GSRT equal-availability priority drift accepted")


def test_physical_seed_is_source_bound_and_context_verified() -> None:
    adapter = load_adapter()
    target = 100_000_700
    source = 100
    context = b"0123456789abcdef"
    donor = bytes(range(256)) * 2
    seed = adapter.PhysicalSeed(
        target, source, adapter.horizon_context_hash(context), 1234
    )
    payload = struct.pack(
        "<4Q", seed.target_coordinate, seed.source_coordinate,
        seed.context_hash, seed.anchor_transition_hash,
    )
    payload_sha = hashlib.sha256(payload).hexdigest()
    observer_sha = "a" * 64
    tape = adapter.PhysicalSeedTape(
        observer_sha, observer_sha, payload_sha, payload_sha,
        seed.anchor_transition_hash, seed.anchor_transition_hash,
        {target: seed},
    )
    mutable_source = {target: seed}
    immutable_tape = adapter.PhysicalSeedTape(
        observer_sha, observer_sha, payload_sha, payload_sha,
        seed.anchor_transition_hash, seed.anchor_transition_hash,
        mutable_source,
    )
    mutable_source.clear()
    assert immutable_tape.get(target) == seed
    try:
        immutable_tape.seeds[target] = seed
    except TypeError:
        pass
    else:
        raise AssertionError("physical seed tape remained caller-mutable")

    class SparseHistory:
        def __getitem__(self, key):
            spans = {
                (target - 16, target): context,
                (source - 16, source): context,
                (source, source + 512): donor,
            }
            return spans[(key.start, key.stop)]

    assert adapter._physical_donor(SparseHistory(), target, tape) == donor
    forged = adapter.PhysicalSeed(
        target, source, adapter.horizon_context_hash(context) ^ 1, 1234
    )
    forged_payload = struct.pack(
        "<4Q", forged.target_coordinate, forged.source_coordinate,
        forged.context_hash, forged.anchor_transition_hash,
    )
    forged_sha = hashlib.sha256(forged_payload).hexdigest()
    forged_tape = adapter.PhysicalSeedTape(
        observer_sha, observer_sha, forged_sha, forged_sha, 1234, 1234,
        {target: forged},
    )
    try:
        adapter._physical_donor(SparseHistory(), target, forged_tape)
    except ValueError as error:
        assert "context hash" in str(error)
    else:
        raise AssertionError("forged physical context hash accepted")


def test_physical_seed_requires_prospectively_bound_observer() -> None:
    adapter = load_adapter()
    empty_sha = hashlib.sha256(b"").hexdigest()
    tape = adapter.PhysicalSeedTape(
        "b" * 64, "b" * 64, empty_sha, empty_sha, 0, 0, {}
    )
    try:
        adapter.replay(
            b"x", [], lambda coordinate: tuple([32768] * 8),
            physical_seed_tape=tape,
            expected_physical_observer_sha256="c" * 64,
        )
    except ValueError as error:
        assert "observer identity" in str(error)
    else:
        raise AssertionError("unbound physical observer accepted")


def test_empty_physical_seed_tape_is_not_an_admissible_g_comparator() -> None:
    adapter = load_adapter()
    empty_sha = hashlib.sha256(b"").hexdigest()
    observer_sha = "b" * 64
    tape = adapter.PhysicalSeedTape(
        observer_sha, observer_sha, empty_sha, empty_sha, 0, 0, {}
    )
    result = adapter.replay(
        b"x", [], lambda coordinate: tuple([32768] * 8),
        physical_seed_tape=tape,
        expected_physical_observer_sha256=observer_sha,
    )
    assert result["physical_g_comparator_admissible"] is False

    unused = adapter.PhysicalSeed(100_000_700, 100, 1, 2)
    unused_payload = struct.pack("<4Q", 100_000_700, 100, 1, 2)
    unused_sha = hashlib.sha256(unused_payload).hexdigest()
    unused_tape = adapter.PhysicalSeedTape(
        observer_sha, observer_sha, unused_sha, unused_sha, 2, 2,
        {100_000_700: unused},
    )
    unused_result = adapter.replay(
        b"x", [], lambda coordinate: tuple([32768] * 8),
        physical_seed_tape=unused_tape,
        expected_physical_observer_sha256=observer_sha,
    )
    assert unused_result["physical_g_comparator_admissible"] is False


def test_raw_coordinate_thirds_do_not_use_wrt_distance() -> None:
    adapter = load_adapter()
    metrics = adapter.ReplayMetrics(0, 100, 500_000_000, 510_000_000)
    parent = tuple([32768] * 8)
    rows = {"P": parent}
    awake = {}
    for arm in adapter.HarmDelta.ARMS:
        rows[f"candidate_{arm}"] = parent
        rows[f"mixture_{arm}"] = tuple([40000] * 8)
        awake[arm] = True
    for coordinate, raw in ((1, 500_000_001), (2, 504_000_000), (3, 509_000_000)):
        metrics.observe(coordinate, raw, 255, rows, awake, None)
    result = metrics.result("0" * 64)
    assert result["chronological_third_coordinate_system"] == "canonical_raw"
    assert all(value > 0 for value in result["mixture_gain_bits_by_third"]["E"])


def test_iter_tape_requires_exact_full_header_and_repeat_binding() -> None:
    adapter = load_adapter()
    header = bytearray(adapter.TAPE_HEADER_BYTES)
    header[:8] = b"GSRT2\0\0\0"
    struct.pack_into("<III", header, 8, 2, adapter.TAPE_HEADER_BYTES,
                     adapter.TAPE_RECORD_BYTES)
    struct.pack_into("<I", header, 20, 0)
    values = {
        24: 9,
        32: 4,
        40: 10,
        48: 1,
        56: 1,
        64: 1,
        72 + 8 * (adapter.EVENT_FIELD_VALUE_BYTE - 1): 1,
        168: 11,
        176: 12,
        184: 13,
    }
    for offset, value in values.items():
        struct.pack_into("<Q", header, offset, value)
    row = adapter.TapeRow(
        1, 1, 8, 2, 3, 1, 2, 3, 4, 0, 0,
        adapter.EVENT_FIELD_VALUE_BYTE,
        adapter.EXPECTED_FLAGS[adapter.EVENT_FIELD_VALUE_BYTE], 1, 1,
    )
    payload = bytes(header) + adapter.TAPE_RECORD.pack(*row.__dict__.values())
    digest = hashlib.sha256(payload).hexdigest()
    binding = adapter.TapeBinding(
        digest, digest, 0, 9, 4, 10, 1, 1, 1,
        (0, 0, 1, 0, 0, 0, 0, 0, 0), 0, 0, 11, 12, 13,
    )
    with tempfile.NamedTemporaryFile() as stream:
        stream.write(payload)
        stream.flush()
        assert list(adapter.iter_tape(Path(stream.name), binding)) == [row]
        drifted = adapter.TapeBinding(
            digest, "f" * 64, 0, 9, 4, 10, 1, 1, 1,
            (0, 0, 1, 0, 0, 0, 0, 0, 0), 0, 0, 11, 12, 13,
        )
        try:
            list(adapter.iter_tape(Path(stream.name), drifted))
        except ValueError as error:
            assert "repeat identity" in str(error)
        else:
            raise AssertionError("nonrepeating GSRT2 binding accepted")

    mismatched_header = bytearray(header)
    struct.pack_into("<Q", mismatched_header, 72 + 8 * 2, 0)
    struct.pack_into("<Q", mismatched_header, 72 + 8 * 1, 1)
    mismatched_payload = bytes(mismatched_header) + payload[len(header):]
    mismatched_sha = hashlib.sha256(mismatched_payload).hexdigest()
    mismatched_binding = adapter.TapeBinding(
        mismatched_sha, mismatched_sha, 0, 9, 4, 10, 1, 1, 1,
        (0, 1, 0, 0, 0, 0, 0, 0, 0), 0, 0, 11, 12, 13,
    )
    with tempfile.NamedTemporaryFile() as stream:
        stream.write(mismatched_payload)
        stream.flush()
        try:
            list(adapter.iter_tape(Path(stream.name), mismatched_binding))
        except ValueError as error:
            assert "body/header" in str(error)
        else:
            raise AssertionError("GSRT2 body/header event drift accepted")

    positional_binding = adapter.TapeBinding(
        digest, digest, 0, 9, 4, 10, 1, 1, 1,
        (0, 0, 1, 0, 0, 0, 0, 0, 0), 0, 1, 11, 12, 13,
    )
    with tempfile.NamedTemporaryFile() as stream:
        stream.write(payload)
        stream.flush()
        try:
            list(adapter.iter_tape(Path(stream.name), positional_binding))
        except ValueError as error:
            assert "positional" in str(error)
        else:
            raise AssertionError("positional predictive population accepted")

    deferred_header = bytearray(header)
    struct.pack_into("<Q", deferred_header, 72 + 8 * 2, 0)
    struct.pack_into("<Q", deferred_header, 72 + 8 * 3, 1)
    deferred_row = adapter.TapeRow(
        0, 2, 16, 0, 1, 1, 2, 3, 4, 0, 0,
        adapter.EVENT_DEFERRED_VALUE_UPDATE,
        adapter.EXPECTED_FLAGS[adapter.EVENT_DEFERRED_VALUE_UPDATE], 1, 1,
    )
    deferred_payload = (
        bytes(deferred_header)
        + adapter.TAPE_RECORD.pack(*deferred_row.__dict__.values())
    )
    deferred_sha = hashlib.sha256(deferred_payload).hexdigest()
    inconsistent_binding = adapter.TapeBinding(
        deferred_sha, deferred_sha, 0, 9, 4, 10, 1, 1, 1,
        (0, 0, 0, 1, 0, 0, 0, 0, 0), 0, 0, 11, 12, 13,
    )
    with tempfile.NamedTemporaryFile() as stream:
        stream.write(deferred_payload)
        stream.flush()
        try:
            list(adapter.iter_tape(Path(stream.name), inconsistent_binding))
        except ValueError as error:
            assert "event accounting" in str(error)
        else:
            raise AssertionError("deferred header/accounting drift accepted")
