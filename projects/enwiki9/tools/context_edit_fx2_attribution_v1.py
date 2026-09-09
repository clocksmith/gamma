#!/usr/bin/env python3
"""Attribute the sealed prediction stream without changing its model or mixture."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.context_edit_fx2_audit_v1 import Adapter, ARMS, BASE, TRACE, canonical
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

PLAN = 'operations/provenance/context_edit_fx2_attribution_v1_plan.json'
EXPERTS = ('L', 'D', 'S')


def reset_ideal_gain(gain):
    """Ideal equal-prior episode mixture; no Q63 or finite archive guarantee."""
    return max(0.0, gain) + math.log2(1 + 2 ** (-abs(gain))) - 1


def attribute(body, trace, expected=None):
    if not body or len(trace) != len(body) * 8 * 28:
        raise ValueError('coordinate length mismatch')
    state = Adapter()
    witnesses = {a: hashlib.sha256() for a in ARMS}
    first_saturation = {a: None for a in EXPERTS}
    last_change = {a: None for a in EXPERTS}
    changed = {a: 0 for a in ARMS}
    saturation_exits = {a: 0 for a in EXPERTS}
    saturated = {a: False for a in EXPERTS}
    boundaries = []
    episodes = []
    current = None
    for i, record in enumerate(struct.iter_unpack('<7I', trace)):
        parent, truth = record[1], record[6]
        before = state.expert.triggers
        predictions = state.predict(parent)
        if truth != ((body[i // 8] >> (7 - i % 8)) & 1):
            raise ValueError('truth coordinate mismatch')
        if state.expert.triggers != before:
            current = dict(start_byte=i // 8, donor_start_byte=state.expert.source_start,
                           bits=0, pure_saved_bits={a: 0.0 for a in EXPERTS},
                           global_mixture_saved_bits={a: 0.0 for a in EXPERTS})
            episodes.append(current)
        for a, q in predictions.items():
            witnesses[a].update(struct.pack('<H', q))
            changed[a] += q != parent
            if a in EXPERTS and q != parent:
                last_change[a] = i
        if current is not None:
            current['bits'] += 1
            pt = parent if truth else 65536 - parent
            for a, q in state.pending[1].items():
                pure = parent if q is None else q
                qt = pure if truth else 65536 - pure
                mixed = predictions[a] if truth else 65536 - predictions[a]
                current['pure_saved_bits'][a] += math.log2(qt / pt)
                current['global_mixture_saved_bits'][a] += math.log2(mixed / pt)
        state.observe(truth)
        for a, m in state.mixtures.items():
            now = m.parent_weight == (1 << 63) - 1
            if now and first_saturation[a] is None:
                first_saturation[a] = i
            if saturated[a] and not now:
                saturation_exits[a] += 1
            saturated[a] = now
        if state.expert.active is None:
            current = None
        if i % 256 == 255 or i + 1 == len(body) * 8:
            boundaries.append(dict(decoded_bytes=(i + 1) // 8,
                                   sha256=hashlib.sha256(canonical(state.snapshot())).hexdigest()))
    hashes = {a: h.hexdigest() for a, h in witnesses.items()}
    if expected is not None:
        if (hashes != expected['probability_sha256'] or boundaries != expected['state_boundaries']
                or changed != expected['changed_q16_events'] or len(episodes) != expected['triggers']):
            raise ValueError('attribution changed sealed probability or state trajectory')
        for a in EXPERTS:
            actual = math.fsum(e['global_mixture_saved_bits'][a] for e in episodes)
            if abs(actual - expected['ideal_saved_bits'][a]) > 1e-7:
                raise ValueError('episode loss does not sum to original diagnostic')
    summary = {}
    for a in EXPERTS:
        gains = [e['pure_saved_bits'][a] for e in episodes]
        summary[a] = dict(pure_saved_bits=math.fsum(gains),
                          profitable_episodes=sum(g > 0 for g in gains),
                          hindsight_positive_bits=math.fsum(max(0.0, g) for g in gains),
                          hindsight_selection_after_one_bit_per_episode=math.fsum(max(0.0, g) for g in gains)-len(gains),
                          ideal_equal_prior_reset_saved_bits=math.fsum(reset_ideal_gain(g) for g in gains),
                          first_parent_saturation_after_bit=first_saturation[a],
                          saturation_exit_count=saturation_exits[a], last_changed_q16_bit=last_change[a])
    return dict(schema='gamma.enwiki9.context-edit-attribution.v1', modeled_wrt_bytes=len(body),
                episode_count=len(episodes), episodes=episodes, summary=summary,
                original_trajectory_verified=expected is not None,
                probability_sha256=hashes, verified_state_boundaries=len(boundaries),
                coordinate='Zero-based WRT body bit coordinates; saturation sampled after observe.',
                scope='Unmixed and reset quantities are conditional ideal costs only. Hindsight choices are not causal selectors. No finite coder, native parent replay or package saving is claimed.',
                objective_credit_bytes=0)


def main():
    plan = json.loads((ROOT / PLAN).read_text())
    for item in plan['inputs']:
        data = (ROOT / item['path']).read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('changed input: ' + item['path'])
    parsed = parse_store_bytes((ROOT / (BASE + 'fixture.stored')).read_bytes(),
                               read_dictionary_words(ROOT / (BASE + 'dictionary/english.dic')))
    if parsed.decoded != (ROOT / (BASE + 'prof_input/input')).read_bytes():
        raise ValueError('raw inverse mismatch')
    expected = json.loads((ROOT / plan['original_measurement']).read_text())
    return attribute(parsed.stream[5:], (ROOT / TRACE).read_bytes(), expected)


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('no arguments expected')
    print(json.dumps(main(), indent=2))
