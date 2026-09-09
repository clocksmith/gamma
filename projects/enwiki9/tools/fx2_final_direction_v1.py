#!/usr/bin/env python3
"""Enclose the ideal derivative along a fixed recorded Q16 logit path."""
import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import struct

from fx2_weight_width_carry_model_v1 import verify

ROOT = Path(__file__).resolve().parents[1]
Q = 65536
SCALE = 10 ** 40


def histogram(events):
    coefficients = [0] * Q
    count = changed = 0
    for p, q, truth in events:
        if not 1 <= p < Q or not 1 <= q < Q or truth not in (0, 1):
            raise ValueError('invalid count or truth')
        weight = Q * truth - p
        coefficients[q] += weight
        coefficients[p] -= weight
        count += 1
        changed += p != q
    # logit(n/Q) = ln(n) - ln(Q-n); preserve exact cancellation.
    return [0] + [coefficients[n] - coefficients[Q - n] for n in range(1, Q)], count, changed


def trace_events(parent, target, rows):
    if parent.stat().st_size != rows * 28 or target.stat().st_size != rows * 28:
        raise ValueError('trace length differs')
    index = 0
    with parent.open('rb') as a, target.open('rb') as b:
        while block := a.read(28 * 4096):
            other = b.read(len(block))
            if len(other) != len(block):
                raise ValueError('truncated target trace')
            for p, q in zip(struct.iter_unpack('<7I', block), struct.iter_unpack('<7I', other)):
                if p[0] != q[0] or p[6] != q[6]:
                    raise ValueError('parent prediction or truth differs at bit ' + str(index))
                yield p[1], q[1], p[6]
                index += 1


def log_bounds(n):
    if not isinstance(n, int) or not 1 <= n < Q:
        raise ValueError('logarithm domain differs')
    if n == 1:
        return 0, 0
    with localcontext() as context:
        context.prec = 80
        rounded = Decimal(n).ln()
    # ln(n)<12 in this domain. Correct rounding at80 significant decimal
    # digits has absolute error<10^-77, far below one SCALE unit (10^-40).
    # as_integer_ratio and all following operations are exact integers.
    numerator, denominator = rounded.as_integer_ratio()
    floor = numerator * SCALE // denominator
    return floor - 1, floor + 2


def certificate(coefficients, logarithms):
    if len(coefficients) != Q or coefficients[0] != 0:
        raise ValueError('coefficient domain differs')
    lower = upper = 0
    for n, weight in enumerate(coefficients):
        if not weight:
            continue
        lo, hi = logarithms[n]
        if lo > hi:
            raise ValueError('reversed logarithm interval')
        lower += weight * (lo if weight > 0 else hi)
        upper += weight * (hi if weight > 0 else lo)
    denominator = Q * SCALE
    sign = 'positive' if lower > 0 else 'negative' if upper < 0 else 'zero' if lower == upper == 0 else 'unresolved'
    return dict(derivative_nats_lower_numerator=str(lower), derivative_nats_upper_numerator=str(upper),
                derivative_denominator=str(denominator), certified_sign=sign,
                derivative_bits_approx=(lower + upper) / (2 * denominator * math.log(2)),
                nonpositive_direction_certified=upper <= 0,
                positive_local_ideal_gain_exists=lower > 0)


def write(path, data):
    payload = (json.dumps(data, sort_keys=True, separators=(',', ':')) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(payload)
    return dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'inputs', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    inputs = json.loads(Path(args.inputs).read_text())
    verify(inputs['inputs'])
    verify(list(plan['files'].values()))
    parent = ROOT / plan['files']['P']['path']
    vectors, counts = {}, {}
    for arm in ('D', 'S'):
        vectors[arm], rows, changed = histogram(trace_events(parent, ROOT / plan['files'][arm]['path'], plan['rows']))
        if rows != plan['rows'] or changed != plan['expected_changed'][arm]:
            raise ValueError('recorded event count differs')
        counts[arm] = dict(events=rows, changed_q16_events=changed)
    needed = sorted({n for vector in vectors.values() for n, value in enumerate(vector) if value})
    logarithms = {n: log_bounds(n) for n in needed}
    result = dict(schema='gamma.enwiki9.fixed-logit-direction.v1',
                  path_definition=plan['path_definition'], log_scale=str(SCALE), decimal_precision=80,
                  arms={arm: dict(**counts[arm], **certificate(vectors[arm], logarithms)) for arm in vectors},
                  objective_credit_bytes=0, full_corpus_score_bytes=None,
                  finite_archive_improvement_proved=False,
                  original_prerounding_native_strength_family_covered=False)
    verify(inputs['inputs'])
    verify(list(plan['files'].values()))
    output = Path(args.output)
    result['coefficients'] = write(output.with_suffix('.coefficients.json'), vectors)
    result['log_bounds'] = write(output.with_suffix('.log-bounds.json'),
                                 [[n, str(logarithms[n][0]), str(logarithms[n][1])] for n in needed])
    write(output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
