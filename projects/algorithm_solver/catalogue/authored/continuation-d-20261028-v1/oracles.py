"""Source-blind bounded references for the ten exact continuation-D definitions."""
from collections import Counter
from itertools import permutations

IDS = (3702, 3703, 3704, 3708, 3713, 3714, 3719, 3720, 3721, 3722)
PARAMETERS = {3702: ('nums',), 3703: ('s', 'k'), 3704: ('n',), 3708: ('nums',),
              3713: ('s',), 3714: ('s',), 3719: ('nums',), 3720: ('s', 'target'),
              3721: ('nums',), 3722: ('s',)}


def integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != len(PARAMETERS[pid]):
        raise ValueError('exact assigned identity and ordered argument list required')
    if pid in (3702, 3708, 3719, 3721):
        array = args[0]
        lower = 0 if pid == 3702 else 1
        max_value = 10**9 if pid in (3702, 3708) else 100000
        min_size = 3 if pid == 3708 else 1
        max_size = 1500 if pid == 3719 else 100000
        valid = type(array) is list and min_size <= len(array) <= max_size and all(integer(x, lower, max_value) for x in array)
    elif pid == 3704:
        valid = integer(args[0], 2, 10**15)
    else:
        s = args[0]
        maximum = {3703: 100000, 3713: 1000, 3714: 100000, 3720: 300, 3722: 1000}[pid]
        minimum = 2 if pid == 3703 else 1
        alphabet = '()' if pid == 3703 else 'abc' if pid == 3714 else 'abcdefghijklmnopqrstuvwxyz'
        valid = type(s) is str and minimum <= len(s) <= maximum and all(c in alphabet for c in s)
        if valid and pid == 3703: valid = integer(args[1], 1, len(s)//2)
        if valid and pid == 3720:
            target = args[1]
            valid = type(target) is str and len(target) == len(s) and all(c in alphabet for c in target)
    if not valid: raise ValueError('outside full pinned public domain')


def reference(pid, args):
    """Literal search definitions, separate from the eventual scalable sources."""
    validate(pid, args)
    if pid == 3702:
        array = args[0]
        if len(array) > 16: raise ValueError('subset enumeration work bound')
        best = 0
        for mask in range(1, 1 << len(array)):
            value = 0
            for index, item in enumerate(array):
                if mask >> index & 1: value ^= item
            if value: best = max(best, mask.bit_count())
        return best
    if pid == 3703:
        s, k = args
        if len(s) > 300: raise ValueError('literal rewrite work bound')
        pattern = '(' * k + ')' * k
        while pattern in s: s = s.replace(pattern, '')
        return s
    if pid == 3704:
        n = args[0]
        if n > 20000: raise ValueError('literal positive-pair work bound')
        return sum('0' not in str(a) and '0' not in str(n-a) for a in range(1, n))
    if pid == 3708:
        array = args[0]
        if len(array) > 35: raise ValueError('literal interval work bound')
        return max(right-left for left in range(len(array)) for right in range(left+1, len(array)+1)
                   if all(array[i-2]+array[i-1] == array[i] for i in range(left+2, right)))
    if pid in (3713, 3714):
        s = args[0]
        if len(s) > 24: raise ValueError('literal substring work bound')
        return max(right-left for left in range(len(s)) for right in range(left+1, len(s)+1)
                   if len(set(Counter(s[left:right]).values())) == 1)
    if pid in (3719, 3721):
        array = args[0]
        if len(array) > 30: raise ValueError('literal distinct-set interval work bound')
        best = 0
        for left in range(len(array)):
            for right in range(left+1, len(array)+1):
                distinct = set(array[left:right])
                if sum(x % 2 == 0 for x in distinct) == sum(x % 2 == 1 for x in distinct):
                    best = max(best, right-left)
        return best
    if pid == 3720:
        s, target = args
        if len(s) > 8: raise ValueError('complete permutation work bound')
        return min((''.join(p) for p in set(permutations(s)) if ''.join(p) > target), default='')
    s = args[0]
    if len(s) > 40: raise ValueError('literal index-map reversal work bound')
    options = []
    for k in range(1, len(s)+1):
        options.append(''.join(s[k-1-i] if i < k else s[i] for i in range(len(s))))
        boundary = len(s)-k
        options.append(''.join(s[i] if i < boundary else s[boundary+len(s)-1-i] for i in range(len(s))))
    return min(options)


def power_ten_no_zero_pairs(digits):
    """Closed-form carry certificate, independently checked by small enumeration.

    For 10**digits: units have nine complementary choices. While both numbers
    continue, each interior position has eight nonzero digit pairs. One number
    may end at any interior position, after which the other is forced to nines.
    """
    if type(digits) is not int or not 1 <= digits <= 15: raise ValueError('power-ten witness range')
    return 9 * 8**(digits-1) + 18 * sum(8**i for i in range(digits-1))


def exact(left, right):
    if type(left) is not type(right): return False
    if type(left) is list: return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right
