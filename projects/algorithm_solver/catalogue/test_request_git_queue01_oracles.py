"""Source-free focused tests; no statement/source files opened by these tests."""
from itertools import combinations, permutations, product

import unittest
from contextlib import contextmanager


@contextmanager
def raises(error, match=None):
    try:
        yield
    except error as exc:
        if match is not None:
            assert match in str(exc)
    else:
        raise AssertionError(f"{error.__name__} not raised")


def parametrized(names, cases):
    def decorate(fn):
        def run():
            for case in cases:
                fn(*case)
        run.__name__ = fn.__name__
        return run
    return decorate

from . import imported_qualification as q
from . import request_git_queue01_oracles as o


@parametrized('pid,args,answer', [
    (1957, ['leeetcode'], 'leetcode'), (1957, ['aaabaaaa'], 'aabaa'),
    (1957, ['aab'], 'aab'), (1957, ['zzzzzz'], 'zz'),
    (1971, [3, [[0, 1], [1, 2], [2, 0]], 0, 2], True),
    (1971, [6, [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]], 0, 5], False),
    (1971, [1, [], 0, 0], True),
    (2017, [[[2, 5, 4], [1, 5, 1]]], 4),
    (2017, [[[3, 3, 1], [8, 5, 2]]], 4),
    (2017, [[[1, 3, 1, 15], [1, 3, 3, 1]]], 7),
    (2048, [1], 22), (2048, [1000], 1333), (2048, [3000], 3133),
    (2048, [0], 1), (2048, [1000000], 1224444),
])
def test_definition_examples_and_degenerate_cases(pid, args, answer):
    assert q.exact(o.expected(pid, args), answer)


@parametrized('pid,args', [
    (1957, ['']), (1957, ['A']), (1957, ['é']), (1957, ['a'*100001]), (1957, [1]),
    (1971, [True, [], 0, 0]), (1971, [0, [], 0, 0]), (1971, [200001, [], 0, 0]),
    (1971, [2, [[0, 0]], 0, 1]), (1971, [2, [[0, 1], [1, 0]], 0, 1]),
    (1971, [2, [[0, True]], 0, 1]), (1971, [2, [[0, 2]], 0, 1]),
    (1971, [2, [], -1, 0]), (1971, [2, [], 0, 2]),
    (2017, [[[1]]]), (2017, [[[], []]]), (2017, [[[1], [1, 2]]]),
    (2017, [[[True], [1]]]), (2017, [[[0], [1]]]), (2017, [[[1], [100001]]]),
    (2048, [True]), (2048, [-1]), (2048, [1000001]), (2048, [1.0]),
])
def test_full_domain_invalid_shapes(pid, args):
    with raises(ValueError):
        o.validate(pid, args)


def test_full_domains_distinct_from_reference_budgets():
    for pid, args in [(1957, ['z'*100000]), (1971, [200000, [], 0, 199999]),
                      (2017, [[[100000]*50000, [100000]*50000]])]:
        o.validate(pid, args)
        with raises(ValueError, match='budget'):
            o.expected(pid, args)
    o.validate(2048, [1000000])
    for pid, args in [(True, ['a']), (9999, []), (1957, ('a',)), (1957, ['a', 'b'])]:
        with raises(ValueError):
            o.validate(pid, args)


def test_subsequence_reference_matches_run_bound_on_small_strings():
    for n in range(1, 7):
        for chars in product('ab', repeat=n):
            value = ''.join(chars)
            blocks = []
            for char in value:
                if not blocks or blocks[-1][0] != char:
                    blocks.append([char, 1])
                else:
                    blocks[-1][1] += 1
            assert o.expected(1957, [value]) == ''.join(char*min(length, 2) for char, length in blocks)


def test_grid_path_enumeration_matches_split_derivation():
    for n in range(1, 5):
        for cells in product((1, 5), repeat=2*n):
            grid = [list(cells[:n]), list(cells[n:])]
            by_split = min(max(sum(grid[0][i+1:]), sum(grid[1][:i])) for i in range(n))
            assert o.expected(2017, [grid]) == by_split
    for n in range(1, 20):
        assert o.expected(2017, [[[100000]*n, [100000]*n]]) == n//2*100000


def test_complete_balanced_integer_scan_matches_digit_multiset_construction():
    constructed = set()
    for count in range(1, 8):
        for digits in combinations(range(1, 8), count):
            if sum(digits) > 7:
                continue
            bag = ''.join(str(d)*d for d in digits)
            for ordering in set(permutations(bag)):
                value = int(''.join(ordering))
                if value <= 1224444:
                    constructed.add(value)
    assert o.balanced_numbers() == tuple(sorted(constructed))


def test_packet_expectations_remain_host_only():
    case = {'args': ['aaab'], 'expected': 'aab', 'compare': 'return'}
    packet = q.packet([case])
    assert packet['calls'] == [{'args': ['aaab']}]
    assert 'expected' not in str(packet)
    assert o.expected_observation_bytes([case], 'python') < q.LIMITS['max_output_bytes']
    with raises(ValueError):
        o.expected_observation_bytes([case], 'other')


def test_unpinned_statement_rejected_without_file_access():
    with raises(ValueError, match='pinned'):
        o.public_examples(1957, b'not the official statement')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(value) for name, value in globals().copy().items()
                              if name.startswith("test_") and callable(value))


if __name__ == "__main__":
    unittest.main()
