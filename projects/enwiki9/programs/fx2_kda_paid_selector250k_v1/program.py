#!/usr/bin/env python3
"""Price one fixed causal selector family on retained KDA trajectories."""
import hashlib
import json
from pathlib import Path
import struct
import sys

from lib.fx2_kda_paid_selector_v1 import context, empty_histograms, fit, ratio_bounds, unpack_policy
from tools.wrt_exact import parse_store_bytes, read_dictionary_words


def analyze(body, traces):
    if set(traces) != {'P', 'D', 'S'} or any(len(t) != 224 * len(body) for t in traces.values()):
        raise ValueError('trace extent differs')
    histograms = {arm: empty_histograms() for arm in ('D', 'S')}
    counts = {arm: bytearray() for arm in traces}
    for i, rows in enumerate(zip(*(struct.iter_unpack('<7I', traces[a]) for a in ('P', 'D', 'S')))):
        truth = (body[i // 8] >> (7 - i % 8)) & 1
        for arm, row in zip(('P', 'D', 'S'), rows):
            if not 1 <= row[1] < 65536 or row[6] != truth:
                raise ValueError('count or truth differs at ' + str(i))
            counts[arm].extend(struct.pack('<H', row[1]))
        p, d, s = (row[1] for row in rows)
        for arm, alternative in (('D', d), ('S', s)):
            histograms[arm][context(p, alternative, i % 8)][p, alternative, truth] += 1
    reports, policies, products = {}, {}, {}
    for arm in ('D', 'S'):
        table, report, n, p = fit(histograms[arm])
        if unpack_policy(table) != report['selected_choices']:
            raise ValueError('instruction inverse differs')
        reports[arm], policies[arm], products[arm] = report, table, (n, p)
    if products['D'][1] != products['S'][1]:
        raise ValueError('common parent truth product differs')
    separation = ratio_bounds(products['D'][0], products['S'][0])
    return policies, dict(arms=reports, control_separation=separation,
        truth_alignment=True, policy_inverse=True, exact_common_parent_product=True,
        supplied_count_dependencies={a: dict(bytes=len(v), sha256=hashlib.sha256(v).hexdigest()) for a, v in counts.items()},
        conditional_count_bytes_per_treatment=len(counts['P']) + len(counts['D']),
        conditional_table_headroom_pass=reports['D']['paid_ideal_gain_lower_bits'] > 0 and separation['lower_bits'] > 0,
        fixed_family_paid_ideal_reject=reports['D']['paid_ideal_gain_upper_bits'] <= 0)


def main():
    root, out = map(Path, sys.argv[1:])
    native = root / 'results/fx2_kda_carry_opening250k_v1/work/native'
    stored, raw = (native / 'population.stored').read_bytes(), (native / 'population.raw').read_bytes()
    words = read_dictionary_words(native / 'dictionary/english.dic')
    parsed = parse_store_bytes(stored, words)
    if parsed.decoded != raw or parsed.stream[5:] != stored[10:] or len(raw) != 250000 or len(stored[10:]) != 151210:
        raise ValueError('frozen population or WRT inverse differs')
    policies, report = analyze(stored[10:], {a: (native / (a + '-encode.coder')).read_bytes() for a in ('P', 'D', 'S')})
    report.update(schema='gamma.enwiki9.kda-paid-selector.v1', raw_population='[0,250000)',
        raw_bytes=len(raw), modeled_bytes=len(stored[10:]), exact_wrt_inverse=True,
        fitted_and_evaluated_same_development_population=True, standalone_decoder=False,
        dictionary_bytes=(native / 'dictionary/english.dic').stat().st_size,
        source_and_runtime_package_cost_unknown=True, native_dual_trajectory_resources_unknown=True,
        g_P=None, g_S=None, complete_package_bytes=None, full_corpus_score_bytes=None,
        objective_credit_bytes=0, new_native_compression_runs=0, finite_coder_replayed=False,
        proof_scope='Exact minimum ideal loss among five rounded count mixtures in each of64 disjoint pre-truth contexts, with a transmitted25-byte table. No finite archive, cross-population, native resource or unrestricted optimum certificate.',
        limitations='Supplied P/D or P/S count streams and dictionary remain decoder dependencies. Native FXCM consumes neural predictions, so full parent state cannot be assumed shareable. No native integration authorized by this diagnostic alone.')
    for arm, table in policies.items():
        with out.with_suffix('.' + arm + '.policy').open('xb') as f: f.write(table)
    with out.open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True); f.write('\n')


if __name__ == '__main__': main()
