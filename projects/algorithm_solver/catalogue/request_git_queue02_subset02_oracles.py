"""Source-blind queue02 definitions and bounded host-side reference oracles.

No candidate loader or execution engine. Finite tests are not full-domain proof.
Callers must authorize every statement-file read before supplying its bytes.
"""
from itertools import product, combinations_with_replacement, groupby
from math import comb, prod
import re

from . import imported_qualification as q

IDS = (2110, 2117, 2156, 2209, 2213, 2221)
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

PARAMETERS.update({2117: ('left', 'right'), 2156: ('s', 'power', 'modulo', 'k', 'hashValue'),
                   2209: ('floor', 'numCarpets', 'carpetLen'), 2213: ('s', 'queryCharacters', 'queryIndices')})
TITLES.update({2117: 'Abbreviating the Product of a Range', 2156: 'Find Substring With Given Hash Value',
               2209: 'Minimum White Tiles After Covering With Carpets', 2213: 'Longest Substring of One Repeating Character'})
SLUGS.update({2117: 'abbreviating-the-product-of-a-range', 2156: 'find-substring-with-given-hash-value',
              2209: 'minimum-white-tiles-after-covering-with-carpets', 2213: 'longest-substring-of-one-repeating-character'})
STATEMENT_SHA256.update({2117: '05318d336992bd023dc80cc6e1c1ffc455d4569c66e7961fb74796d134e45af2',
 2156: '63540b2cfaeff3e39c73111a71ced716feb535b1ab74c850b798fc13488f1c64',
 2209: 'bf7ac9574e0dab1d592ccae9ec1ffc314bb343d0f73917f521abd9f49b37f060',
 2213: '0e74c2d36fedd54fcd7c2633ea689f497433ad21128cf51455f757d41a0879b9'})
EXAMPLE_COUNT = {2110: 3, 2117: 3, 2156: 2, 2209: 2, 2213: 2, 2221: 2}
for _pid, _domain, _numeric, _complexity in [
 (2117, 'exact integers 1 <= left <= right <= 10000', 'exact decimal strings with leading/trailing five digits and trailing-zero exponent', 'range-size bounded arithmetic; near-full-range cases exercise precision without floating logarithm oracle'),
 (2156, 'lowercase ASCII string length 1..20000; 1<=k<=length; power/modulo 1..1e9; hashValue in [0,modulo); matching substring required', 'exact modular arithmetic, including products above IEEE-754 safe-integer range', 'linear-time target; length-20000 windows and k boundaries'),
 (2209, 'binary string length 1..1000; carpetLen 1..length; numCarpets 1..1000', 'exact integer 0..floor length', 'polynomial target; maximum floor/carpet counts; no full placement enumeration at large bounds'),
 (2213, 'lowercase ASCII s length 1..100000; queryCharacters length k 1..100000; k valid exact integer indices', 'array of exact integers 1..s length', 'subquadratic per-stream target; 100000 updates and length100000 shapes')]:
    OBLIGATIONS[_pid] = {'domain': _domain, 'result': _numeric, 'complexity': _complexity,
        'mutation_alias': 'No required argument mutation. Observe before/after and aliases under an explicitly declared effect policy.',
        'unknown': 'Candidate exported interface is unknown; ordered public parameters are definition-only evidence.'}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _text(x, alphabet, minimum, maximum):
    return type(x) is str and minimum <= len(x) <= maximum and all(c in alphabet for c in x)


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('unsupported fixed identity or ordered arguments')
    if pid in (2110, 2221):
        values = args[0]
        lo, hi, maximum = (1, 100000, 100000) if pid == 2110 else (0, 9, 1000)
        valid = type(values) is list and 1 <= len(values) <= maximum and all(_integer(v, lo, hi) for v in values)
    elif pid == 2117:
        left, right = args
        valid = _integer(left, 1, 10000) and _integer(right, left, 10000)
    elif pid == 2156:
        s, power, modulo, k, value = args
        valid = (_text(s, 'abcdefghijklmnopqrstuvwxyz', 1, 20000) and _integer(power, 1, 10**9)
                 and _integer(modulo, 1, 10**9) and _integer(k, 1, len(s)) and _integer(value, 0, modulo - 1))
        if valid:
            valid = value in _window_hashes(s, power, modulo, k)
    elif pid == 2209:
        floor, count, length = args
        valid = _text(floor, '01', 1, 1000) and _integer(count, 1, 1000) and _integer(length, 1, len(floor))
    else:
        s, chars, indices = args
        valid = (_text(s, 'abcdefghijklmnopqrstuvwxyz', 1, 100000) and _text(chars, 'abcdefghijklmnopqrstuvwxyz', 1, 100000)
                 and type(indices) is list and len(indices) == len(chars) and all(_integer(i, 0, len(s) - 1) for i in indices))
    if not valid:
        raise ValueError('arguments outside pinned full input domain')


def _window_hashes(s, power, modulo, k):
    # Right-to-left rolling evaluator used only for full-domain existence validation.
    value = 0
    high = pow(power, k, modulo)
    result = [0] * (len(s) - k + 1)
    for i in range(len(s) - 1, -1, -1):
        value = (value * power + ord(s[i]) - 96) % modulo
        if i + k < len(s):
            value = (value - (ord(s[i + k]) - 96) * high) % modulo
        if i <= len(s) - k:
            result[i] = value
    return result


def _abbreviate_integer(value):
    zeros = 0
    while value % 10 == 0:
        value //= 10
        zeros += 1
    # Bounded 9-digit conversions avoid altering interpreter-wide numeric limits.
    blocks = []
    while value:
        value, block = divmod(value, 10**9)
        blocks.append(block)
    digits = str(blocks[-1]) + ''.join(f'{b:09d}' for b in blocks[-2::-1])
    return (digits if len(digits) <= 10 else digits[:5] + '...' + digits[-5:]) + 'e' + str(zeros)


def expected(pid, args):
    """Small reference: enumerate all intervals or simulate successive rows."""
    validate(pid, args)
    if pid == 2117:
        return _abbreviate_integer(prod(range(args[0], args[1] + 1)))
    if pid == 2156:
        s, power, modulo, k, value = args
        if len(s) > 60:
            raise ValueError('reference budget exceeded')
        return next(s[i:i+k] for i in range(len(s)-k+1)
                    if sum((ord(s[i+j])-96) * pow(power, j, modulo) for j in range(k)) % modulo == value)
    if pid == 2209:
        floor, count, length = args
        if len(floor) > 12:
            raise ValueError('reference budget exceeded')
        if count * length >= len(floor):
            return 0
        white = sum((c == '1') << i for i, c in enumerate(floor))
        placements = [((1 << length) - 1) << i for i in range(len(floor) - length + 1)]
        best = len(floor)
        for selected in combinations_with_replacement(placements, count):
            covered = 0
            for mask in selected:
                covered |= mask
            best = min(best, (white & ~covered).bit_count())
        return best
    if pid == 2213:
        s, chars, indices = args
        if len(s) * len(chars) > 10000:
            raise ValueError('reference budget exceeded')
        row, result = list(s), []
        for c, i in zip(chars, indices):
            row[i] = c
            result.append(max(sum(1 for _ in run) for _, run in groupby(row)))
        return result
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
    if pid == 2117:
        left, right = args
        primes = []
        composite = bytearray(right + 1)
        for x in range(2, right + 1):
            if not composite[x]:
                primes.append(x)
                for multiple in range(x*x, right + 1, x):
                    composite[multiple] = 1
        value = 1
        for prime in primes:
            factor, exponent = prime, 0
            while factor <= right:
                exponent += right // factor - (left - 1) // factor
                factor *= prime
            value *= pow(prime, exponent)
        return _abbreviate_integer(value)
    if pid not in (2110, 2221):
        raise ValueError('large oracle requires explicit constructive case witness')
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
    if len(cases) != EXAMPLE_COUNT[pid]:
        raise ValueError('incomplete public examples')
    return cases


def _generate_cases(pid, statement):
    cases = public_examples(pid, statement)
    categories = ['pinned_public_example'] * len(cases)
    sentinel = object()
    def add_args(args, category, answer=sentinel):
        validate(pid, args)
        cases.append({'args': args, 'expected': expected(pid, args) if answer is sentinel else answer, 'compare': 'return'})
        categories.append(category)
    def add(a, category, large=False):
        add_args([a], category, analytic(pid, [a]) if large else sentinel)
    if pid == 2110:
        for n in range(1, 7):
            for values in product((1, 2, 3), repeat=n):
                add(list(values), 'exhaustive_small_three_values')
        for a in ([1] * 100000, list(range(100000, 0, -1)), list(range(1, 100001)), [1, 2] * 50000, [100000, 99999] * 50000):
            add(a, 'analytic_maximum_length', True)
        add([100000, 99999, 99998, 1], 'numeric_boundaries')
    elif pid == 2221:
        for n in range(1, 4):
            for values in product(range(10), repeat=n):
                add(list(values), 'exhaustive_small_all_digits')
        for n in range(4, 9):
            for values in product((0, 1), repeat=n):
                add(list(values), 'exhaustive_binary_longer')
        for a in ([0] * 1000, [9] * 1000, [i % 10 for i in range(1000)], [1] + [0] * 999, [0] * 999 + [9]):
            add(a, 'analytic_maximum_length', True)
    elif pid == 2117:
        for left in range(1, 61):
            for right in range(left, 61):
                add_args([left, right], 'exhaustive_small_ranges')
        for args in ([1, 10000], [2, 9999], [9000, 10000], [9999, 10000], [999, 1000], [371, 375]):
            add_args(args, 'exact_big_integer_large_boundary', analytic(pid, args))
    elif pid == 2156:
        for n in range(1, 6):
            for letters in product('ab', repeat=n):
                s = ''.join(letters)
                for k in range(1, n + 1):
                    for power, modulo in ((1, 1), (2, 5), (3, 8)):
                        hashes = {sum((ord(s[i+j])-96) * pow(power, j, modulo) for j in range(k)) % modulo for i in range(n-k+1)}
                        for value in sorted(hashes):
                            add_args([s, power, modulo, k, value], 'exhaustive_small_hashes')
        for k in (1, 9999, 20000):
            power, modulo = 999999999, 1000000000
            value = sum(26 * pow(power, j, modulo) for j in range(k)) % modulo
            add_args(['z' * 20000, power, modulo, k, value], 'analytic_uniform_maximum', 'z' * k)
        add_args(['a' * 19999 + 'z', 10**9, 999999937, 1, 26], 'analytic_last_match', 'z')
        add_args(['ab' * 10000, 1, 1, 10000, 0], 'analytic_collision_first_match', 'ab' * 5000)
    elif pid == 2209:
        for n in range(1, 7):
            for bits in product('01', repeat=n):
                for length in range(1, n + 1):
                    for count in range(1, min(3, n) + 1):
                        add_args([''.join(bits), count, length], 'exhaustive_small_placements')
        for floor, count, length, answer in [('0'*1000, 1, 1, 0), ('1'*1000, 1, 999, 1),
                ('1'*1000, 1000, 1, 0), ('1'*1000, 1, 1, 999), ('10'*500, 1, 500, 250),
                ('1'*1000, 999, 1, 1), ('0'*999+'1', 1, 1, 0)]:
            add_args([floor, count, length], 'analytic_maximum_floor', answer)
    elif pid == 2213:
        for n in range(1, 6):
            for letters in product('ab', repeat=n):
                s = ''.join(letters)
                for indices in product(range(n), repeat=2):
                    for chars in ('aa', 'ab', 'ba', 'bb'):
                        add_args([s, chars, list(indices)], 'exhaustive_two_updates')
        add_args(['a'*100000, 'a'*100000, [0]*100000], 'analytic_maximum_noops', [100000]*100000)
        add_args(['a'*100000, 'ba'*50000, [50000]*100000], 'analytic_maximum_split_rejoin', [50000, 100000]*50000)
        add_args(['ab'*50000, 'ba'*50000, [0]*100000], 'analytic_maximum_endpoint_toggle', [2, 1]*50000)
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
