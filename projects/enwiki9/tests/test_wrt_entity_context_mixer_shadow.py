from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "wrt_entity_context_mixer_shadow.py"
)
TOOLS = TOOL.parent
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "wrt_entity_context_mixer_shadow", TOOL
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_signed_blend_interpolates_and_extrapolates_symmetrically() -> None:
    assert MODULE.signed_blend_probability(30_000, 40_000, 50_000) == 30_500
    assert MODULE.signed_blend_probability(30_000, 40_000, -50_000) == 29_500
    assert MODULE.signed_blend_probability(30_000, 30_001, 500_000) == 30_001
    assert MODULE.signed_blend_probability(30_000, 29_999, 500_000) == 29_999
    assert MODULE.signed_blend_probability(1, 65_535, -1_000_000) == 1


def test_mixer_decides_before_current_gain_is_learned() -> None:
    mixer = MODULE.ContextMixer(
        blends_ppm=(-50_000, 0, 50_000),
        minimum_observations=1,
        margin_qbits=0,
        decay_shift=0,
    )
    keys = ((0,),)

    first = mixer.decide_then_learn(keys, (-100, 0, 500))
    assert first.expert_index == 1
    assert first.gain_qbits == 0

    second = mixer.decide_then_learn(keys, (-100, 0, -500))
    assert second.expert_index == 2
    assert second.gain_qbits == -500


def test_hierarchical_mixer_backs_off_when_detail_has_no_history() -> None:
    mixer = MODULE.ContextMixer(
        blends_ppm=(-25_000, 0, 25_000),
        minimum_observations=1,
        margin_qbits=0,
        decay_shift=0,
    )
    coarse = (0,)
    first_detail = (1, 1)
    second_detail = (1, 2)
    mixer.update((coarse, first_detail), (200, 0, -200))

    expert, level = mixer.choose((coarse, second_detail))
    assert mixer.blends_ppm[expert] == -25_000
    assert level == 0


def test_decay_moves_positive_and_negative_scores_toward_zero() -> None:
    assert MODULE.decay_toward_zero(1024, 2) == 768
    assert MODULE.decay_toward_zero(-1024, 2) == -768
    assert MODULE.decay_toward_zero(3, 2) == 3
    assert MODULE.decay_toward_zero(-3, 2) == -3


def test_feature_keys_ignore_future_suffix_and_truth() -> None:
    endpoint = MODULE.EndpointStats(
        p1=45_000,
        support=17,
        branches=3,
        zeros=4,
        ones=13,
    )
    # Both full events have the same first four decoded bits (1010).  Only those
    # prior bits enter the feature key at relative_bit=4.
    prefix_a = MODULE.event_prefix(b"\xA1", 4)
    prefix_b = MODULE.event_prefix(b"\xAF", 4)
    assert prefix_a == prefix_b
    keys_a = MODULE.causal_feature_keys(
        "disagreement",
        path_depth=2,
        relative_bit=4,
        prefix=prefix_a,
        base_p1=30_000,
        endpoint=endpoint,
    )
    keys_b = MODULE.causal_feature_keys(
        "disagreement",
        path_depth=2,
        relative_bit=4,
        prefix=prefix_b,
        base_p1=30_000,
        endpoint=endpoint,
    )
    assert keys_a == keys_b


def test_endpoint_stats_filters_by_already_decoded_prefix() -> None:
    trie = MODULE.EntityTrie(cap_nodes=16)
    for _ in range(3):
        trie.insert((b"A",))
    trie.insert((b"C",))

    stats = MODULE.endpoint_stats(
        trie,
        node=0,
        bit_index=6,
        prefix=0b010000,
        min_support=1,
        alpha2=1,
    )
    assert stats is not None
    assert stats.support == 4
    assert stats.branches == 2
    assert stats.zeros == 3
    assert stats.ones == 1
