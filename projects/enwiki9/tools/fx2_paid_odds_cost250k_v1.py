#!/usr/bin/env python3
"""Price a fixed paid odds-correction family on retained native development counts."""
import json
from pathlib import Path
import struct
import sys

from lib.fx2_paid_odds_v1 import context, empty_histograms, fit, unpack_policy
from tools.wrt_exact import parse_store_bytes, read_dictionary_words


def analyze(body, trace):
    if not body or len(trace) != len(body) * 8 * 28:
        raise ValueError('trace extent differs')
    histograms = empty_histograms()
    for i, row in enumerate(struct.iter_unpack('<7I', trace)):
        count, truth = row[1], row[6]
        if truth != ((body[i // 8] >> (7 - i % 8)) & 1):
            raise ValueError('trace truth differs at bit ' + str(i))
        histograms[context(count, i % 8)][count, truth] += 1
    policy, report = fit(histograms)
    if unpack_policy(policy) != report['selected_choices']:
        raise ValueError('paid instruction inverse differs')
    report.update(truth_alignment=True, policy_roundtrip=True,
                  fitted_and_evaluated_same_population=True,
                  paid_ideal_headroom_pass=report['paid_ideal_gain_lower_bits'] > 0,
                  fixed_family_paid_ideal_reject=report['paid_ideal_gain_upper_bits'] <= 0)
    return policy, report


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    native = root / 'results/fx2_kda_carry_opening250k_v1/work/native'
    stored = (native / 'population.stored').read_bytes()
    raw = (native / 'population.raw').read_bytes()
    parsed = parse_store_bytes(stored, read_dictionary_words(native / 'dictionary/english.dic'))
    if parsed.decoded != raw or parsed.stream[5:] != stored[10:]:
        raise ValueError('WRT inverse differs')
    if len(raw) != 250000 or len(stored[10:]) != 151210:
        raise ValueError('frozen population differs')
    policy, report = analyze(stored[10:], (native / 'P-encode.coder').read_bytes())
    report.update(schema='gamma.enwiki9.fx2-paid-odds-cost.v1',
                  raw_population='[0,250000)', raw_bytes=len(raw), modeled_bytes=len(stored[10:]),
                  prior_exposure='Already exposed opening development population; not confirmation.',
                  exact_wrt_inverse=True, parent_state='Unchanged retained parent counts; no native feedback executed.',
                  g_P=None, g_S=None, n_1=None, n_2=None, complete_package_bytes=None,
                  full_corpus_score_bytes=None, objective_credit_bytes=0,
                  archive_authority='No new archive. Paid ideal bound excludes finite-coder effects and shared code.',
                  mathematical_scope='Partition by parent count bucket and bit position. All alternatives see the same events. Three bits per context, including unused and identity entries. Enumerating seven exact integer products in each disjoint context attains the minimum ideal data plus table cost over this fixed family.')
    with out.with_suffix('.policy').open('xb') as f:
        f.write(policy)
    with out.open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
