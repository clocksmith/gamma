#!/usr/bin/env python3
"""Attribute closed GRD2 delivery losses using exact cached rows and native replay."""
import argparse
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))
sys.path.insert(0, str(ROOT / 'tests'))
from fx2_ratio_loss_attribution_v1 import coder_comparison
from fx2_ratio_coder_opening250k_q0_v1 import delivery_records
from test_fx2_residual_ratio_native_v1 import Native, load_library, bits, value
from fx2_weight_width_carry_model_v1 import verify

UNIT = 1 << 45


def replay(parent, treatment, state_path, vocabulary, library, rows, arm):
    if arm not in ('D', 'S') or len(vocabulary) != 205 or vocabulary != sorted(set(vocabulary)):
        raise ValueError('arm or vocabulary differs')
    raw, final_gain, changed = coder_comparison(parent, treatment, rows)
    mapping = {b: i for i, b in enumerate(vocabulary)}
    if any(b not in mapping for b in raw):
        raise ValueError('truth outside authenticated vocabulary')
    # The old comparison returns decoded truths; additionally preserve original
    # parent floating predictions before treating this as an isolated delivery.
    with Path(parent).open('rb') as p, Path(treatment).open('rb') as q:
        for i in range(rows * 8):
            a, b = p.read(28), q.read(28)
            if a[:4] != b[:4]:
                raise ValueError('original prediction differs at bit ' + str(i))
    states = iter(delivery_records(Path(state_path), arm, rows))
    ratio = Native(load_library(library), 205, arm)
    expert_gain = []
    base_loss, corrected_loss = [], []
    thirds = [dict(scored_symbols=0, expert_bits_saved=0.0, final_coder_bits_saved=0.0) for _ in range(3)]
    matched = 0

    def read_state():
        nonlocal matched
        state = next(states)
        if state[10:2486] != ratio.serialize():
            raise ValueError('first ratio-state divergence at record ' + str(matched))
        matched += 1
        return list(struct.iter_unpack('<BQQ', state[2486:]))

    try:
        initial = read_state()
        if [x[0] for x in initial] != vocabulary or any(p or q for _, p, q in initial):
            raise ValueError('initial cached rows differ')
        previous = None
        for i, byte in enumerate(raw):
            third = thirds[min(2, i * 3 // rows)]
            third['final_coder_bits_saved'] += final_gain[i]
            if previous is not None:
                p, q = previous
                symbol = mapping[byte]
                lp = -math.log2(p[symbol] / sum(p))
                lq = -math.log2(q[symbol] / sum(q))
                base_loss.append(lp)
                corrected_loss.append(lq)
                expert_gain.append(lp - lq)
                third['expert_bits_saved'] += lp - lq
                third['scored_symbols'] += 1
                ratio.observe(symbol)
                observed = read_state()
                if [x[0] for x in observed] != vocabulary or [(x[1], x[2]) for x in observed] != list(zip(p, q)):
                    raise ValueError('cached row changed during observe at byte ' + str(i))
            # A P record contains the newly computed base row. Replay predict
            # before comparing its inner state and its exact corrected masses.
            state = next(states)
            triples = list(struct.iter_unpack('<BQQ', state[2486:]))
            if [x[0] for x in triples] != vocabulary:
                raise ValueError('cached vocabulary differs at byte ' + str(i))
            base = [x[1] for x in triples]
            corrected = [x[2] for x in triples]
            if any(not 0 < x <= UNIT for x in base) or any(not 0 < x <= 4 * UNIT for x in corrected):
                raise ValueError('cached mass outside native bounds')
            floats = [bits(x / UNIT) for x in base]
            if [int(value(x) * UNIT) for x in floats] != base:
                raise ValueError('cached mass is not exact binary32')
            predicted = ratio.predict(floats)
            if [int(value(x) * UNIT) for x in predicted] != corrected:
                raise ValueError('corrected mass differs at byte ' + str(i))
            if state[10:2486] != ratio.serialize():
                raise ValueError('first ratio-state divergence at record ' + str(matched))
            matched += 1
            previous = base, corrected
        if next(states, None) is not None:
            raise ValueError('trailing state record')
    finally:
        ratio.close()
    return raw, dict(arm=arm, rows=rows, scored_symbols=len(expert_gain),
                     matched_calibration_states=matched, cached_mass_rows_verified=rows,
                     expert_parent_ideal_bits=math.fsum(base_loss),
                     expert_treatment_ideal_bits=math.fsum(corrected_loss),
                     expert_ideal_bits_saved=math.fsum(expert_gain),
                     final_coder_ideal_bits_saved=math.fsum(final_gain),
                     changed_q16_events=changed, chronological_thirds=thirds,
                     original_parent_predictions_identical=True,
                     initial_byte_unscored_by_expert=True, final_prediction_unconsumed=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'inputs', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    inputs = json.loads(Path(args.inputs).read_text())
    verify(inputs['inputs'])
    verify(list(plan['files'].values()))
    files = {k: ROOT / v['path'] for k, v in plan['files'].items()}
    vocabulary = json.loads(files['vocabulary'].read_text())['vocabulary_bytes']
    stored = files['stored'].read_bytes()
    if (len(stored) != plan['rows'] + 10 or stored[5] != 7 or
            int.from_bytes(stored[6:10], 'big') != plan['raw_population_bytes']):
        raise ValueError('stored frontend differs')
    arms = {}
    for arm in plan['arms']:
        raw, report = replay(files['parent_coder'], files[arm + '_coder'], files[arm + '_state'],
                             vocabulary, files['library'], plan['rows'], arm)
        if raw != stored[10:]:
            raise ValueError('coded truths differ from stored population')
        expected = plan['expected_final'][arm]
        if report['changed_q16_events'] != expected['changed_q16_events'] or abs(
                report['final_coder_ideal_bits_saved'] - expected['ideal_bits_saved']) > 1e-6:
            raise ValueError('final loss reference differs')
        arms[arm] = report
    result = dict(schema='gamma.enwiki9.ratio-loss-attribution.v1',
                  raw_population_bytes=plan['raw_population_bytes'], arms=arms,
                  objective_credit_bytes=0, full_corpus_score_bytes=None)
    verify(inputs['inputs'])
    verify(list(plan['files'].values()))
    with Path(args.output).open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
