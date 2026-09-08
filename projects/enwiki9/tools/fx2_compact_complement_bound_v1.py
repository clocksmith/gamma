#!/usr/bin/env python3
"""Exact ideal-cost ceilings for a frozen pair; not a finite codec certificate."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

PLAN = 'operations/provenance/fx2_compact_complement_bound_v1_plan.json'
TRACES = 'results/fx2_compact_v26_fixture50051_q0_v1/work/'
PARENT = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work/'


def product(values):
    """Balanced exact products keep the oracle arithmetic bounded and efficient."""
    values = list(values)
    while len(values) > 1:
        values = [values[i] * values[i + 1] if i + 1 < len(values)
                  else values[i] for i in range(0, len(values), 2)]
    return values[0] if values else 1


def ceil_log2_ratio(numerator, denominator):
    """Least integer k with numerator/denominator <= 2**k, including k < 0."""
    if numerator <= 0 or denominator <= 0:
        raise ValueError('positive ratio required')
    k = numerator.bit_length() - denominator.bit_length()
    below = numerator <= (denominator << k) if k >= 0 else (numerator << -k) <= denominator
    return k if below else k + 1


def analyze(parent, treatment, block_bytes=(1, 64, 1024)):
    if not parent or len(parent) != len(treatment) or len(parent) % 8:
        raise ValueError('nonempty whole-byte matched population required')
    if any(not isinstance(p, int) or not 1 <= p <= 65535 for p in parent + treatment):
        raise ValueError('invalid actual-bit Q16 count')
    if any(not isinstance(n, int) or n < 1 for n in block_bytes):
        raise ValueError('positive fixed block size required')
    gains = [math.log2(d / p) for p, d in zip(parent, treatment)]
    positive = [(p, d) for p, d in zip(parent, treatment) if d > p]
    ceiling = ceil_log2_ratio(product(d for p, d in positive), product(p for p, d in positive))
    blocks = []
    for size in block_bytes:
        numerators, denominators, selected = [], [], 0
        for start in range(0, len(parent), size * 8):
            pp = product(parent[start:start + size * 8])
            dd = product(treatment[start:start + size * 8])
            if dd > pp:
                selected += 1
                numerators.append(dd)
                denominators.append(pp)
        labels = (len(parent) + size * 8 - 1) // (size * 8)
        gross = ceil_log2_ratio(product(numerators), product(denominators))
        blocks.append(dict(block_bytes=size, blocks=labels, treatment_blocks=selected,
                           gross_ideal_gain_ceiling_bits=gross, selector_bits=labels,
                           after_selector_ideal_gain_ceiling_bits=gross - labels))
    return dict(events=len(parent), changed_events=sum(p != d for p, d in zip(parent, treatment)),
                treatment_better_events=len(positive),
                treatment_worse_events=sum(d < p for p, d in zip(parent, treatment)),
                all_treatment_ideal_gain_bits_approx=math.fsum(gains),
                clairvoyant_ideal_gain_bits_approx=math.fsum(g for g in gains if g > 0),
                clairvoyant_ideal_gain_ceiling_bits=ceiling, fixed_block_oracles=blocks,
                floating_point_authority='Diagnostic only; ceilings use exact integer products and shifts')


def aligned_counts(left, right, body):
    if len(left) != len(right) or len(left) != len(body) * 8 * 28:
        raise ValueError('trace/body length mismatch')
    parents, treatments = [], []
    for i, (p, d) in enumerate(zip(struct.iter_unpack('<7I', left), struct.iter_unpack('<7I', right))):
        truth = (body[i // 8] >> (7 - i % 8)) & 1
        if p[6] != truth or d[6] != truth or not 0 < p[1] < 65536 or not 0 < d[1] < 65536:
            raise ValueError('trace truth/count mismatch at event ' + str(i))
        parents.append(p[1] if truth else 65536 - p[1])
        treatments.append(d[1] if truth else 65536 - d[1])
    return parents, treatments


def audit():
    plan = json.loads((ROOT / PLAN).read_text())
    for row in plan['inputs']:
        path = ROOT / row['path']
        with path.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        if path.stat().st_size != row['bytes'] or digest != row['sha256']:
            raise ValueError('input identity differs: ' + row['path'])
    parsed = parse_store_bytes((ROOT / (PARENT + 'fixture.stored')).read_bytes(),
                              read_dictionary_words(ROOT / (PARENT + 'dictionary/english.dic')))
    raw = (ROOT / (PARENT + 'prof_input/input')).read_bytes()
    if parsed.decoded != raw:
        raise ValueError('raw inverse differs')
    body = parsed.stream[5:]
    if len(raw) != 50051 or len(body) != 32478:
        raise ValueError('frozen population differs')
    parent, treatment = aligned_counts((ROOT / (TRACES + 'P/encode.trace')).read_bytes(),
                                      (ROOT / (TRACES + 'D/encode.trace')).read_bytes(), body)
    report = analyze(parent, treatment)
    old = json.loads((ROOT / 'operations/provenance/fx2_compact_v26_terminal_20260908.json').read_text())
    if report['changed_events'] != old['posthoc_diagnostic']['changed_quantized_events']:
        raise ValueError('prior change count differs')
    cost = old['overlapping_local_inventory_delta_bytes']
    return dict(schema='gamma.enwiki9.compact-complement-bound.v1', status='passed',
                plan=PLAN, raw_bytes=len(raw), modeled_bytes=len(body), exact_wrt_inverse=True,
                trace_truth_alignment=True, **report,
                measured_replacement_inventory_delta_bytes=cost,
                oracle_ideal_ceiling_below_replacement_inventory_bits=report['clairvoyant_ideal_gain_ceiling_bits'] < 8 * cost,
                proof='For any per-event convex mixture of these fixed two quantized streams, actual truth mass is at most max(P,D). The product of max(P,D)/P bounds its ideal likelihood ratio. Integer shifts compute an exact ceiling of its base-two logarithm.',
                limitations=['Oracle uses future truth; it is not a decoder or a causal prediction result',
                             'No finite arithmetic archive saving bound is proved',
                             'Replacement inventory is an observed overlapping subtotal, not the cost of a yet-unbuilt joint codec',
                             'A combined decoder must reconstruct both probability trajectories within its resource and package limits',
                             'Fixed block labels exclude model, framing, termination and runtime costs',
                             'This used fixture supplies no full-corpus or confirmation evidence'],
                archive_saving_bytes=None, complete_package_bytes=None, objective_credit_bytes=0,
                full_corpus_score_bytes=None)


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('no arguments expected')
    print(json.dumps(audit(), indent=2))
