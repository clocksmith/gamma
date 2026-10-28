"""Definition-derived host oracles. Never imports a supplied solution.

This is an exposed, owner-provided program cohort. Historical reserved source
and case datasets are not inputs. Finite public-domain evidence is not a claim
of held-out performance or automatic canonical-catalogue promotion.
"""
from collections import Counter, defaultdict
from itertools import accumulate
from math import comb
import re
import string

IDS = (1, 5, 125, 326, 338, 414, 496, 500, 509, 557,
       561, 628, 693, 697, 709, 724, 739, 852, 946, 953)
ARITY = {pid: 2 if pid in (1, 496, 946, 953) else 1 for pid in IDS}
PROTECTED_EXISTING_IDS = (125, 414, 496, 561, 628, 693, 697, 709, 724, 852)


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def integers(value, low, high, minimum, maximum):
    return (type(value) is list and minimum <= len(value) <= maximum
            and all(integer(x, low, high) for x in value))


def text(value, alphabet, minimum, maximum):
    return (type(value) is str and minimum <= len(value) <= maximum
            and all(x in alphabet for x in value))


def sum_pairs(nums, target):
    counts = Counter(nums)
    possibilities = []
    for x, count in counts.items():
        y = target - x
        if x > y:
            continue
        multiplicity = count * counts[y] if x != y else count * (count - 1) // 2
        if multiplicity:
            possibilities.append((x, y, multiplicity))
    if sum(row[2] for row in possibilities) != 1:
        raise ValueError('Two Sum requires exactly one index pair')
    x, y, _ = possibilities[0]
    indices = [i for i, value in enumerate(nums) if value in (x, y)]
    return sorted(indices)


def validate(pid, args):
    if pid not in IDS or type(args) is not list or len(args) != ARITY[pid]:
        raise ValueError('fixed problem and ordered argument interface required')
    x = args[0]
    printable = ''.join(map(chr, range(32, 127)))
    good = False
    if pid == 1:
        good = integers(x, -10**9, 10**9, 2, 10000) and integer(args[1], -10**9, 10**9)
        if good:
            sum_pairs(x, args[1])
    elif pid == 5:
        good = text(x, string.ascii_letters + string.digits, 1, 1000)
    elif pid == 125:
        good = text(x, printable, 1, 200000)
    elif pid == 326:
        good = integer(x, -2**31, 2**31 - 1)
    elif pid == 338:
        good = integer(x, 0, 100000)
    elif pid == 414:
        good = integers(x, -2**31, 2**31 - 1, 1, 10000)
    elif pid == 496:
        y = args[1]
        good = (integers(x, 0, 10000, 1, 1000) and integers(y, 0, 10000, 1, 1000)
                and len(x) <= len(y) and len(set(x)) == len(x)
                and len(set(y)) == len(y) and set(x) <= set(y))
    elif pid == 500:
        good = (type(x) is list and 1 <= len(x) <= 20
                and all(text(w, string.ascii_letters, 1, 100) for w in x))
    elif pid == 509:
        good = integer(x, 0, 30)
    elif pid == 557:
        good = (text(x, printable, 1, 50000) and x == x.strip(' ') and '  ' not in x)
    elif pid == 561:
        good = integers(x, -10000, 10000, 2, 20000) and len(x) % 2 == 0
    elif pid == 628:
        good = integers(x, -1000, 1000, 3, 10000)
    elif pid == 693:
        good = integer(x, 1, 2**31 - 1)
    elif pid == 697:
        good = integers(x, 0, 49999, 1, 50000)
    elif pid == 709:
        good = text(x, printable, 1, 100)
    elif pid == 724:
        good = integers(x, -1000, 1000, 1, 10000)
    elif pid == 739:
        good = integers(x, 30, 100, 1, 100000)
    elif pid == 852:
        good = integers(x, 0, 1000000, 3, 100000)
        if good:
            peak = x.index(max(x))
            good = (0 < peak < len(x) - 1
                    and all(a < b for a, b in zip(x[:peak], x[1:peak + 1]))
                    and all(a > b for a, b in zip(x[peak:], x[peak + 1:])))
    elif pid == 946:
        y = args[1]
        good = (integers(x, 0, 1000, 1, 1000) and integers(y, 0, 1000, 1, 1000)
                and len(set(x)) == len(x) and len(y) == len(x) and set(x) == set(y))
    elif pid == 953:
        y = args[1]
        good = (type(x) is list and 1 <= len(x) <= 100
                and all(text(w, string.ascii_lowercase, 1, 20) for w in x)
                and text(y, string.ascii_lowercase, 26, 26) and len(set(y)) == 26)
    if not good:
        raise ValueError('outside independently pinned public input domain')


def longest_length(s):
    # Interval DP is independent of the candidates' centre-expansion algorithms.
    rows = [bytearray(len(s)) for _ in s]
    longest = 1
    for start in range(len(s) - 1, -1, -1):
        for end in range(start, len(s)):
            if s[start] == s[end] and (end - start < 2 or rows[start + 1][end - 1]):
                rows[start][end] = 1
                longest = max(longest, end - start + 1)
    return longest


def maximum_product(xs):
    # Extremal product DP, not the candidates' sorted-tail formula.
    low, high = [1, None, None, None], [1, None, None, None]
    for x in xs:
        for k in (3, 2, 1):
            if low[k - 1] is None:
                continue
            values = [x * low[k - 1], x * high[k - 1]]
            if low[k] is not None:
                values += [low[k], high[k]]
            low[k], high[k] = min(values), max(values)
    return high[3]


def expected(pid, args):
    validate(pid, args)
    x = args[0]
    if pid == 1:
        return sum_pairs(x, args[1])
    if pid == 5:
        return longest_length(x)  # Host predicate parameter, not a required string.
    if pid == 125:
        normalized = ''.join(c.lower() for c in x if c in string.ascii_letters + string.digits)
        return normalized == normalized[::-1]
    if pid == 326:
        return x in {3**k for k in range(20)}
    if pid == 338:
        return [bin(i).count('1') for i in range(x + 1)]
    if pid == 414:
        values = sorted(set(x))
        return values[-3] if len(values) >= 3 else values[-1]
    if pid == 496:
        y = args[1]
        return [next((v for v in y[y.index(a) + 1:] if v > a), -1) for a in x]
    if pid == 500:
        rows = [set(row) for row in ('qwertyuiop', 'asdfghjkl', 'zxcvbnm')]
        return [word for word in x if any(set(word.lower()) <= row for row in rows)]
    if pid == 509:
        return 0 if x == 0 else sum(comb(x - 1 - k, k) for k in range((x - 1) // 2 + 1))
    if pid == 557:
        return re.sub(r'[^ ]+', lambda m: ''.join(reversed(m.group())), x)
    if pid == 561:
        count, answer = 0, 0
        for value, frequency in sorted(Counter(x).items()):
            answer += value * ((frequency + (count % 2 == 0)) // 2)
            count += frequency
        return answer
    if pid == 628:
        return maximum_product(x)
    if pid == 693:
        bits = bin(x)[2:]
        return all(a != b for a, b in zip(bits, bits[1:]))
    if pid == 697:
        positions = defaultdict(list)
        for i, value in enumerate(x):
            positions[value].append(i)
        degree = max(map(len, positions.values()))
        return min(p[-1] - p[0] + 1 for p in positions.values() if len(p) == degree)
    if pid == 709:
        return x.translate(str.maketrans(string.ascii_uppercase, string.ascii_lowercase))
    if pid == 724:
        prefix = [0, *accumulate(x)]
        return next((i for i in range(len(x)) if prefix[i] == prefix[-1] - prefix[i + 1]), -1)
    if pid == 739:
        future, answer = [len(x)] * 101, [0] * len(x)
        for i in range(len(x) - 1, -1, -1):
            position = min(future[x[i] + 1:], default=len(x))
            answer[i] = position - i if position < len(x) else 0
            future[x[i]] = i
        return answer
    if pid == 852:
        return x.index(max(x))
    if pid == 946:
        rank = {value: i for i, value in enumerate(x)}
        sequence = [rank[value] for value in args[1]]
        # Stack outputs from increasing input avoid a 312 pattern. For each
        # earlier high value, subsequent lower values must be descending.
        for i, value in enumerate(sequence):
            lower = [v for v in sequence[i + 1:] if v < value]
            if any(a < b for a, b in zip(lower, lower[1:])):
                return False
        return True
    rank = {value: i for i, value in enumerate(args[1])}
    transformed = [tuple(rank[c] for c in word) for word in x]
    return all(a <= b for a, b in zip(transformed, transformed[1:]))


def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    if type(a) is dict:
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def matches(pid, args, value, want):
    if pid == 1:
        return (type(value) is list and len(value) == 2
                and all(type(i) is int for i in value) and sorted(value) == want)
    if pid == 5:
        return (type(value) is str and len(value) == want
                and value in args[0] and value == value[::-1])
    if pid == 500:
        return (type(value) is list and all(type(s) is str for s in value)
                and Counter(value) == Counter(want))
    return exact(value, want)


def compare(pid, args, want, record, language):
    if 'error' in record:
        return False, 'candidate_error'
    kind = str if pid == 5 else type(want)
    types = {'python': {list: 'list', int: 'int', bool: 'bool', str: 'str'},
             'javascript': {list: 'object', int: 'number', bool: 'boolean', str: 'string'}}
    if record.get('result_type') != types[language][kind]:
        return False, 'result_type'
    if not matches(pid, args, record.get('result'), want):
        return False, 'result_value'
    if not exact(record.get('args_before'), args) or not exact(record.get('args_after'), args):
        return False, 'input_effects'
    if not exact(record.get('alias_edges'), []):
        return False, 'mutable_return_alias'
    return True, None
