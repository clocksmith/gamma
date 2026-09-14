"""Exact development selection of a fixed, explicitly transmitted odds table.

No corpus access here. This optimizes ideal loss, not finite archive bytes.
Contexts depend on pre-truth parent counts and bit position only. The caller
must prove that its parent computes those counts without feedback from us.
"""
from collections import Counter
import math

from lib.fx2_closing_cost_v1 import ceiling_ratio

Q = 65536
FACTORS = ((1, 1), (1, 2), (3, 4), (7, 8), (8, 7), (4, 3), (2, 1))
CONTEXTS = 128
POLICY_BYTES = 48  # 128 fixed three-bit indices; index 7 is invalid.


def context(count, bit_position):
    if not 1 <= count < Q or not 0 <= bit_position < 8:
        raise ValueError('invalid pre-truth coordinate')
    return bit_position * 16 + (count >> 12)


def corrected_count(count, choice):
    if not 1 <= count < Q or not 0 <= choice < len(FACTORS):
        raise ValueError('invalid count or choice')
    a, b = FACTORS[choice]
    denominator = a * count + b * (Q - count)
    # Nearest integer, ties upward, followed by the declared coder clamp.
    return max(1, min(Q - 1, (Q * a * count + denominator // 2) // denominator))


def pack_policy(choices):
    if len(choices) != CONTEXTS or any(type(j) is not int or not 0 <= j < 7 for j in choices):
        raise ValueError('policy requires 128 indices in [0,7)')
    value = 0
    for j in choices:
        value = (value << 3) | j
    return value.to_bytes(POLICY_BYTES, 'big')


def unpack_policy(data):
    if len(data) != POLICY_BYTES:
        raise ValueError('policy length differs')
    value = int.from_bytes(data, 'big')
    choices = [(value >> (3 * (CONTEXTS - 1 - i))) & 7 for i in range(CONTEXTS)]
    if any(j == 7 for j in choices):
        raise ValueError('reserved policy index')
    return choices


def product(values):
    """Balanced exact multiplication avoids sequential big-integer growth."""
    values = list(values)
    while len(values) > 1:
        values = [values[i] * values[i + 1] if i + 1 < len(values) else values[i]
                  for i in range(0, len(values), 2)]
    return values[0] if values else 1


def truth_product(histogram, choice):
    factors = []
    for (count, truth), frequency in sorted(histogram.items()):
        if truth not in (0, 1) or type(frequency) is not int or frequency <= 0:
            raise ValueError('invalid truth or multiplicity')
        q = corrected_count(count, choice)
        factors.append(pow(q if truth else Q - q, frequency))
    return product(factors)


def select_context(histogram):
    # Common Q**n and fixed three-bit instruction cost cancel. Stable ties
    # favor identity. This is exhaustive selection of all seven alternatives.
    values = [truth_product(histogram, j) for j in range(len(FACTORS))]
    choice = max(range(len(values)), key=lambda j: values[j])
    selected, parent = values[choice], values[0]
    lower = -ceiling_ratio(parent, selected)
    upper = ceiling_ratio(selected, parent)
    return choice, dict(events=sum(histogram.values()), choice=choice,
                        ideal_gain_lower_bits=lower, ideal_gain_upper_bits=upper,
                        diagnostic_ideal_gain_bits=math.log2(selected) - math.log2(parent))


def fit(histograms):
    if len(histograms) != CONTEXTS:
        raise ValueError('context population differs')
    choices, rows = [], []
    for cid, histogram in enumerate(histograms):
        for count, truth in histogram:
            if context(count, cid // 16) != cid:
                raise ValueError('histogram assigned to incorrect causal context')
        choice, row = select_context(histogram)
        row['context'] = cid
        choices.append(choice)
        rows.append(row)
    policy = pack_policy(choices)
    overhead = 8 * len(policy)
    return policy, dict(
        contexts=rows, events=sum(r['events'] for r in rows),
        policy_bytes=len(policy), paid_instruction_bits=overhead,
        diagnostic_ideal_gain_bits=math.fsum(r['diagnostic_ideal_gain_bits'] for r in rows),
        paid_ideal_gain_lower_bits=sum(r['ideal_gain_lower_bits'] for r in rows) - overhead,
        paid_ideal_gain_upper_bits=sum(r['ideal_gain_upper_bits'] for r in rows) - overhead,
        selected_choices=choices,
        selection='Exact minimum ideal data plus fixed instruction cost among 7**128 policies; ties favor identity.',
        scope='Development fit only; no finite coder, native integration, shared code cost, transfer or full-corpus claim.')


def empty_histograms():
    return [Counter() for _ in range(CONTEXTS)]
