"""Source-blind queue02 definitions and bounded host-side reference oracles.

No candidate loader or execution engine. Finite tests are not full-domain proof.
Callers must authorize every statement-file read before supplying its bytes.
"""
from itertools import product
from math import comb
import re

from . import imported_qualification as q

IDS = (2110, 2221)
PARAMETERS = {2110: ('prices',), 2221: ('nums',)}
TITLES = {2110: 'Number of Smooth Descent Periods of a Stock',
          2221: 'Find Triangular Sum of an Array'}
SLUGS = {2110: 'number-of-smooth-descent-periods-of-a-stock',
         2221: 'find-triangular-sum-of-an-array'}
STATEMENT_SHA256 = {
    2110: 'd9225e9b06ce4516f289b9c03d13d1d4586c2cf98caaa3863d7022f273408f08',
    2221: '4d4fac1970f1138b0ff61144648602443bfa5d0e9e8e399a65a3f206ed6fe377',
}
SMALL_BUDGET = {2110: 50, 2221: 40}
OBLIGATIONS = {
    2110: {'domain': '1..100000 prices, each exact integer 1..100000',
           'result': 'exact integer 1..5000050000; reject bool/float coercion',
           'complexity': 'linear-time target; 100000-item descent and plateaus included',
           'mutation_alias': 'No required input mutation; record before/after and returned aliases. Qualification requires explicitly chosen effect policy.',
           'unknown': 'Public rendering gives ordered prices parameter, not language-specific exported entrypoint.'},
    2221: {'domain': '1..1000 digits, each exact integer 0..9',
           'result': 'exact integer 0..9',
           'complexity': 'quadratic-time target permitted; length-1000 mixed and uniform arrays included',
           'mutation_alias': 'Statement describes conceptual replacement, not a required caller mutation. Record effects; explicit effect policy required.',
           'unknown': 'Public rendering gives ordered nums parameter, not language-specific exported entrypoint.'},
}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != 1:
        raise ValueError('unsupported fixed identity or ordered arguments')
    values = args[0]
    lo, hi, maximum = (1, 100000, 100000) if pid == 2110 else (0, 9, 1000)
    if type(values) is not list or not 1 <= len(values) <= maximum or not all(_integer(v, lo, hi) for v in values):
        raise ValueError('array outside pinned full input domain')


def expected(pid, args):
    """Small reference: enumerate all intervals or simulate successive rows."""
    validate(pid, args)
    values = args[0]
    if len(values) > SMALL_BUDGET[pid]:
        raise ValueError('reference budget exceeded; input may remain valid')
    if pid == 2110:
        return sum(all(values[k] - values[k + 1] == 1 for k in range(i, j))
                   for i in range(len(values)) for j in range(i, len(values)))
    row = values[:]
    while len(row) > 1:
        row = [(row[i] + row[i + 1]) % 10 for i in range(len(row) - 1)]
    return row[0]


def analytic(pid, args):
    """Separate large reference: maximal descent runs or binomial coefficients."""
    validate(pid, args)
    a = args[0]
    if pid == 2221:
        return sum(comb(len(a) - 1, i) * x for i, x in enumerate(a)) % 10
    breaks = [-1] + [i for i in range(len(a) - 1) if a[i] != a[i + 1] + 1] + [len(a) - 1]
    return sum((b - a) * (b - a + 1) // 2 for a, b in zip(breaks, breaks[1:]))


def public_examples(pid, raw):
    if type(pid) is not int or pid not in IDS or type(raw) is not bytes or q.sha(raw) != STATEMENT_SHA256[pid]:
        raise ValueError('exact gated pinned definition required')
    text = re.sub(r'(?m)^L\d+: ?', '', raw.decode())
    if f'{pid}. {TITLES[pid]}' not in text or f'https://leetcode.com/problems/{SLUGS[pid]}/' not in text:
        raise ValueError('numeric/title/slug identity mismatch')
    import ast
    cases = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*([^\n]+)', text, re.S):
        call = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if call.args or tuple(k.arg for k in call.keywords) != PARAMETERS[pid]:
            raise ValueError('public ordered parameter mismatch')
        args = [ast.literal_eval(x.value) for x in call.keywords]
        answer = ast.literal_eval(match[2])
        if not q.exact(answer, expected(pid, args)):
            raise ValueError('public example disagreement')
        cases.append({'args': args, 'expected': answer, 'compare': 'return'})
    if len(cases) != {2110: 3, 2221: 2}[pid]:
        raise ValueError('incomplete public examples')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement)
    categories = ['pinned_public_example'] * len(cases)
    def add(a, category, large=False):
        cases.append({'args': [a], 'expected': analytic(pid, [a]) if large else expected(pid, [a]), 'compare': 'return'})
        categories.append(category)
    if pid == 2110:
        for n in range(1, 7):
            for values in product((1, 2, 3), repeat=n):
                add(list(values), 'exhaustive_small_three_values')
        for a in ([1] * 100000, list(range(100000, 0, -1)), list(range(1, 100001)), [1, 2] * 50000, [100000, 99999] * 50000):
            add(a, 'analytic_maximum_length', True)
        add([100000, 99999, 99998, 1], 'numeric_boundaries')
    else:
        for n in range(1, 4):
            for values in product(range(10), repeat=n):
                add(list(values), 'exhaustive_small_all_digits')
        for n in range(4, 9):
            for values in product((0, 1), repeat=n):
                add(list(values), 'exhaustive_binary_longer')
        for a in ([0] * 1000, [9] * 1000, [i % 10 for i in range(1000)], [1] + [0] * 999, [0] * 999 + [9]):
            add(a, 'analytic_maximum_length', True)
    return cases, categories


def expected_observation_bytes(batch, language):
    if language not in ('javascript', 'python'):
        raise ValueError('unsupported language')
    return sum(len(q.encoded({'i': i, 'result': c['expected'],
                             'result_type': q.expected_type(c['expected'], language),
                             'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []}))
               for i, c in enumerate(batch)) + len(q.encoded({'done': len(batch)})) + (language == 'python')


def build_cases(pid, statement):
    cases, categories = _generate_cases(pid, statement)
    if len(q.encoded(cases)) > q.MAX_FILE:
        raise ValueError('unchanged case-file budget exceeded')
    for _, batch in q.batches(cases):
        for language in ('python', 'javascript'):
            if expected_observation_bytes(batch, language) > q.LIMITS['max_output_bytes']:
                raise ValueError('unchanged output budget exceeded')
    return cases, categories
