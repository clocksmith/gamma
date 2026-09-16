"""Exact paid selection between fixed, supplied causal trajectories.

This minimizes ideal data cost within 5**64 policies, not finite archive bytes.
Producing both input trajectories natively remains a separate obligation.
"""
from collections import Counter
import math

from lib.fx2_closing_cost_v1 import ceiling_ratio
from lib.fx2_paid_odds_v1 import product

Q = 65536
CONTEXTS = 64
CHOICES = 5
POLICY_BYTES = 25


def context(parent, alternative, bit_position):
    if not 1 <= parent < Q or not 1 <= alternative < Q or not 0 <= bit_position < 8:
        raise ValueError('invalid pre-truth coordinates')
    return 8 * bit_position + 2 * (parent >> 14) + int(alternative > parent)


def corrected(parent, alternative, choice):
    if not 1 <= parent < Q or not 1 <= alternative < Q or not 0 <= choice < CHOICES:
        raise ValueError('invalid count or mixture choice')
    # Convex integer interpolation, nearest rounding with ties upward.
    return ((4 - choice) * parent + choice * alternative + 2) // 4


def pack_policy(choices):
    if len(choices) != CONTEXTS or any(type(j) is not int or not 0 <= j < CHOICES for j in choices):
        raise ValueError('expected 64 three-bit choices in [0,5)')
    value = 0
    for j in choices:
        value = (value << 3) | j
    return b'\x01' + value.to_bytes(24, 'big')


def unpack_policy(data):
    if len(data) != POLICY_BYTES or data[0] != 1:
        raise ValueError('unsupported table version or extent')
    value = int.from_bytes(data[1:], 'big')
    choices = [(value >> (3 * (CONTEXTS - 1 - i))) & 7 for i in range(CONTEXTS)]
    if any(j >= CHOICES for j in choices):
        raise ValueError('reserved choice')
    return choices


def truth_product(histogram, choice):
    values = []
    for (p, d, y), n in sorted(histogram.items()):
        if y not in (0, 1) or type(n) is not int or n <= 0:
            raise ValueError('invalid outcome or multiplicity')
        c = corrected(p, d, choice)
        values.append(pow(c if y else Q - c, n))
    return product(values)


def select_context(histogram):
    values = [truth_product(histogram, j) for j in range(CHOICES)]
    j = max(range(CHOICES), key=lambda i: values[i])  # identity wins ties
    return j, values[j], values[0]


def ratio_bounds(n, d):
    return dict(lower_bits=-ceiling_ratio(d, n), upper_bits=ceiling_ratio(n, d),
                diagnostic_bits=math.log2(n) - math.log2(d))


def fit(histograms):
    if len(histograms) != CONTEXTS:
        raise ValueError('context count differs')
    choices, rows, selected, parents = [], [], [], []
    for cid, hist in enumerate(histograms):
        if any(context(p, d, cid // 8) != cid for p, d, y in hist):
            raise ValueError('wrong causal context')
        j, n, d = select_context(hist)
        choices.append(j); selected.append(n); parents.append(d)
        rows.append(dict(context=cid, events=sum(hist.values()), choice=j, **ratio_bounds(n, d)))
    table = pack_policy(choices)
    n, d = product(selected), product(parents)
    bounds = ratio_bounds(n, d)
    cost = 8 * len(table)
    report = dict(contexts=rows, events=sum(r['events'] for r in rows), selected_choices=choices,
                  policy_bytes=len(table), paid_instruction_bits=cost, ideal_gain=bounds,
                  paid_ideal_gain_lower_bits=bounds['lower_bits'] - cost,
                  paid_ideal_gain_upper_bits=bounds['upper_bits'] - cost,
                  paid_ideal_gain_diagnostic_bits=bounds['diagnostic_bits'] - cost,
                  exact_family_optimum=True, finite_archive_optimum=False)
    return table, report, n, d


def empty_histograms():
    return [Counter() for _ in range(CONTEXTS)]
