#!/usr/bin/env python3
"""Conditional diagnostic on retained FX2 probabilities, never a native codec."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.context_edit_continuation_v1 import Continuation, core
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

PLAN = 'operations/provenance/context_edit_fx2_audit_v1_plan.json'
BASE = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work/'
TRACE = 'results/fx2_half_tail_fixture50051_q0_v1/work/P/encode.trace'
ARMS = ('P', 'K', 'L', 'D', 'S')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


class Adapter:
    """Explicit WRT adapter: consumes one supplied pre-truth parent p per bit."""
    def __init__(self):
        self.expert = Continuation('wrt-byte-v1')
        self.mixtures = {a: core.SleepingMixture() for a in ('L', 'D', 'S')}
        self.prefix = self.bits = 0
        self.histograms = self.pending = None
        self.lookups = dict(eligible=0, empty=0, collision=0, hit=0)
        self.active_bytes = {a: 0 for a in ('L', 'D', 'S')}

    def predict(self, parent):
        if self.pending is not None:
            raise ValueError('truth pending')
        if type(parent) is not int or not 0 < parent < 65536:
            raise ValueError('invalid supplied parent probability')
        if self.bits == 0:
            e = self.expert
            if e.active is None and len(e.tail) >= 8:
                key = bytes(e.tail[-8:])
                row = e.bank[e.slot(key)]
                self.lookups['eligible'] += 1
                self.lookups['empty' if row is None else 'hit' if row[0] == key else 'collision'] += 1
            self.histograms = e.predict()
            for a, h in self.histograms.items():
                self.active_bytes[a] += h is not None
        candidates = {a: None if h is None else core.conditional_p1(h, self.prefix, self.bits)
                      for a, h in self.histograms.items()}
        predictions = {a: self.mixtures[a].predict(parent, q) for a, q in candidates.items()}
        self.pending = (parent, candidates)
        return dict(P=parent, K=parent, **predictions)

    def observe(self, truth):
        if self.pending is None or type(truth) is not int or truth not in (0, 1):
            raise ValueError('valid prediction and decoded bit required')
        parent, candidates = self.pending
        for a, q in candidates.items():
            self.mixtures[a].observe(parent, q, truth)
        self.prefix = (self.prefix << 1) | truth
        self.bits += 1
        self.pending = None
        if self.bits == 8:
            self.expert.observe(self.prefix)
            self.prefix = self.bits = 0
            self.histograms = None

    def snapshot(self):
        return dict(expert=self.expert.snapshot(),
                    mixtures={a: dict(parent_weight=m.parent_weight, awake_updates=m.awake_updates)
                              for a, m in self.mixtures.items()},
                    prefix=self.prefix, bits=self.bits, pending=self.pending,
                    histograms=self.histograms)


def evaluate(body, trace):
    if not body or len(trace) != len(body) * 8 * 28:
        raise ValueError('native coordinate length mismatch')
    state = Adapter()
    losses = {a: [0.0, 0.0, 0.0] for a in ARMS}
    changed = {a: 0 for a in ARMS}
    witnesses = {a: hashlib.sha256() for a in ARMS}
    snapshots = []
    separation = dict(D_L=0, D_S=0)
    for i, record in enumerate(struct.iter_unpack('<7I', trace)):
        parent, truth = record[1], record[6]
        predictions = state.predict(parent)  # No current truth passed to prediction.
        if truth != ((body[i // 8] >> (7 - i % 8)) & 1):
            raise ValueError('native trace truth mismatch')
        third = min(2, (i // 8) * 3 // len(body))
        for a, q in predictions.items():
            if not 0 < q < 65536:
                raise ValueError('invalid output probability')
            losses[a][third] -= math.log2((q if truth else 65536 - q) / 65536)
            changed[a] += q != parent
            witnesses[a].update(struct.pack('<H', q))
        separation['D_L'] += predictions['D'] != predictions['L']
        separation['D_S'] += predictions['D'] != predictions['S']
        state.observe(truth)
        if i % 256 == 255 or i + 1 == len(body) * 8:
            snapshots.append(dict(decoded_bytes=(i + 1) // 8,
                                  sha256=hashlib.sha256(canonical(state.snapshot())).hexdigest()))
    gains = {a: [p - q for p, q in zip(losses['P'], row)] for a, row in losses.items()}
    total = {a: math.fsum(row) for a, row in losses.items()}
    separated = total['D'] < min(total['P'], total['L'], total['S'])
    promising = separated and all(x > 0 for x in gains['D'])
    return dict(raw_coordinate='explicit WRT body bytes, MSB first; raw input is separately inverted',
                modeled_bytes=len(body), bit_records=len(body) * 8,
                lookups=state.lookups, triggers=state.expert.triggers, active_bytes=state.active_bytes,
                changed_q16_events=changed, differing_control_events=separation,
                ideal_bits=total, chronological_third_ideal_saved_bits=gains,
                ideal_saved_bits={a: total['P'] - q for a, q in total.items()},
                probability_sha256={a: h.hexdigest() for a, h in witnesses.items()},
                state_boundaries=snapshots, state_boundary_count=len(snapshots),
                mixture_terminal={a: vars(m) for a, m in state.mixtures.items()},
                P_K_identity=witnesses['P'].digest() == witnesses['K'].digest(),
                diagnostic_predicate_passed=promising,
                decision='eligible_for_separately_frozen_native_gate' if promising else 'do_not_integrate_this_configuration',
                archive_saving_bytes=None, complete_package_bytes=None, objective_credit_bytes=0,
                scope='Conditional predictive evidence only. Supplied parent probabilities and dictionary remain dependencies. State hashes cover this adapter every32 bytes plus terminal; native parent and coder state are not certified.')


def audit():
    plan = json.loads((ROOT / PLAN).read_text())
    for row in plan['inputs']:
        data = (ROOT / row['path']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('input identity mismatch: ' + row['path'])
    parsed = parse_store_bytes((ROOT / (BASE + 'fixture.stored')).read_bytes(),
                               read_dictionary_words(ROOT / (BASE + 'dictionary/english.dic')))
    raw = (ROOT / (BASE + 'prof_input/input')).read_bytes()
    if parsed.decoded != raw or len(raw) != 50051 or len(parsed.stream[5:]) != 32478:
        raise ValueError('raw inverse or frozen scope mismatch')
    result = evaluate(parsed.stream[5:], (ROOT / TRACE).read_bytes())
    return dict(schema='gamma.enwiki9.context-edit-fx2-audit.v1', plan=PLAN,
                raw_bytes=len(raw), exact_frontend_inverse=True, **result)


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('no arguments expected')
    print(json.dumps(audit(), indent=2))
