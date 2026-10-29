"""Deterministic edge, boundary, and domain-maximum cases for requested-156-1940-31."""

from copy import deepcopy
import importlib.util
from pathlib import Path

_ORACLES_PATH = Path(__file__).with_name("oracles.py")
_SPEC = importlib.util.spec_from_file_location("requested_156_1940_31_oracles", _ORACLES_PATH)
_ORACLES = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ORACLES)

PROBLEM_IDS = _ORACLES.PROBLEM_IDS
REFERENCES = _ORACLES.REFERENCES
validate_domain = _ORACLES.validate_domain

BASE_ARGS = {
    156: [([1, 2, 3, 4, 5],), ([],), ([1],)],
    159: [("eceba",), ("ccaabbb",), ("a",)],
    161: [("ab", "acb"), ("", ""), ("a", ""), ("ab", "ab")],
    163: [([0, 1, 3, 50, 75], 0, 99), ([-1], -1, -1), ([], 1, 5)],
    280: [([3, 5, 2, 1, 6, 4],), ([6, 6, 5, 6, 3, 8],), ([1, 2],)],
    286: [
        ([[2147483647, -1, 0, 2147483647],
          [2147483647, 2147483647, 2147483647, -1],
          [2147483647, -1, 2147483647, -1],
          [0, -1, 2147483647, 2147483647]],),
        ([[-1]],),
    ],
    294: [("++++",), ("+",), ("+++++",), ("++--+++",)],
    737: [
        (["great", "acting", "skills"], ["fine", "drama", "talent"],
         [["great", "good"], ["fine", "good"], ["drama", "acting"], ["skills", "talent"]]),
        (["I", "love", "leetcode"], ["I", "love", "onepiece"], [["manga", "onepiece"], ["platform", "anime"]]),
    ],
    742: [([1, 3, 2], 1), ([1], 1), ([1, 2, 3, 4, None, None, None, 5, None, 6], 2)],
    751: [("255.0.0.7", 10), ("117.145.102.62", 8), ("0.0.0.0", 4)],
    755: [([2, 1, 1, 2, 1, 2, 2], 4, 3), ([1, 2, 3, 4], 2, 2), ([3, 1, 3], 5, 1)],
    758: [(["ab", "bc"], "aabcd"), (["ab", "cb"], "aabcd"), (["z"], "abc")],
    772: [("1+1",), ("6-4/2",), ("2*(5+5*2)/3+(6/2+8)",), ("(2+6*3+5-(3*14/7+2)*5)+3",)],
    774: [([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 9), ([23, 24, 36, 39, 46, 56, 57, 65, 84, 98], 1)],
    903: [("DID",), ("D",), ("IDID",)],
    911: [
        (["TopVotedCandidate", "q", "q", "q", "q", "q", "q"],
         [[[0, 1, 1, 0, 0, 1, 0], [0, 5, 10, 15, 20, 25, 30]], [3], [12], [25], [15], [24], [8]]),
        (["TopVotedCandidate", "q"], [[[0, 0, 1], [0, 1, 2]], [2]]),
    ],
    1213: [
        ([1, 2, 3, 4, 5], [1, 2, 5, 7, 9], [1, 3, 4, 5, 8]),
        ([197, 418, 523, 876, 1356], [501, 880, 1593, 1710, 1870], [521, 682, 1337, 1395, 1764]),
    ],
    1214: [([2, 1, 4], [1, 0, 3], 5), ([0, -10, 10], [5, 1, 7, 0, 2], 18)],
    1215: [(0, 21), (10, 15), (0, 0)],
    1229: [
        ([[10, 50], [60, 120], [140, 210]], [[0, 15], [60, 70]], 8),
        ([[10, 50], [60, 120], [140, 210]], [[0, 15], [60, 70]], 12),
    ],
    1230: [([0.4], 1), ([0.5, 0.5, 0.5, 0.5, 0.5], 0), ([0.2, 0.8, 0.5], 2)],
    1692: [(3, 2), (4, 2), (20, 5)],
    1714: [
        ([0, 1, 2, 3, 4, 5, 6, 7], [[0, 3], [5, 1], [4, 2]]),
        ([100, 200, 100, 200, 100, 200], [[0, 1], [0, 2], [1, 2]]),
    ],
    1740: [
        ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 0),
        ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 7),
        ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 5),
    ],
    1820: [
        ([[1, 1, 1], [1, 0, 1], [0, 0, 1]],),
        ([[1, 0, 1, 0], [1, 0, 0, 0], [0, 0, 1, 0], [1, 1, 1, 0]],),
    ],
    1826: [
        ([2, 3, 4, 5], [2, 1, 3, 4]),
        ([2, 2, 2, 2, 2], [2, 2, 2, 2, 5]),
        ([2, 3, 2, 2, 3, 2], [2, 3, 2, 3, 2, 7]),
    ],
    1908: [([1],), ([1, 2, 3],), ([1, 1, 1],)],
    1918: [([2, 1, 3], 4), ([3, 3, 5, 5], 7), ([5], 1)],
    1924: [
        ([[1, 1], [2, 2], [2, 0], [2, 4], [3, 3], [4, 2]],),
        ([[1, 2], [2, 2], [4, 2]],),
        ([[3, 3]],),
    ],
    1933: [("000111000",), ("00011111222",), ("011100022233",)],
    1940: [
        ([[1, 3, 4], [1, 4, 7, 9]],),
        ([[2, 3, 6, 8], [1, 2, 3, 5, 6, 7, 10], [2, 3, 4, 6, 9]],),
    ],
}

MAX_ARGS = {
    156: [([1, 2, 3, 4, 5, None, None, 6, 7],)],
    159: [("ab" * 128 + "cd" * 128,)],
    161: [("a" * 128 + "b" + "c" * 128, "a" * 128 + "x" + "c" * 128)],
    163: [(list(range(0, 512, 3)), 0, 600)],
    280: [(list(range(256)),)],
    286: [([[0 if (r == 0 and c == 0) else 2147483647 for c in range(16)] for r in range(16)],)],
    294: [("+" * 30 + "-" + "+" * 29,)],
    737: [(["w" + str(i) for i in range(64)], ["u" + str(i) for i in range(64)], [["w" + str(i), "u" + str(i)] for i in range(64)])],
    742: [(list(range(1, 128)), 2)],
    751: [("192.168.0.1", 1000)],
    755: [([i % 7 + 1 for i in range(64)], 100, 32)],
    758: [(["abc", "bcd", "cde"], "abcdef" * 32)],
    772: [("+".join(f"({i}*2-{i}//2)".replace("//", "/") for i in range(1, 33)),)],
    774: [([i * 100 for i in range(128)], 500)],
    903: [("DI" * 32,)],
    911: [(["TopVotedCandidate"] + ["q"] * 64, [[[i % 5 for i in range(64)], [i * 5 for i in range(64)]]] + [[i * 5 + 2] for i in range(64)])],
    1213: [(list(range(0, 256, 2)), list(range(0, 256, 3)), list(range(0, 256, 6)))],
    1214: [(list(range(1, 128)), list(range(100, 227)), 200)],
    1215: [(0, 10**6)],
    1229: [([[i * 20, i * 20 + 15] for i in range(128)], [[i * 20 + 5, i * 20 + 18] for i in range(128)], 10)],
    1230: [([0.25 + (i % 5) * 0.1 for i in range(64)], 20)],
    1692: [(128, 32)],
    1714: [([(i * 17) % 1000 for i in range(256)], [[i, (i % 7) + 1] for i in range(64)])],
    1740: [(list(range(1, 128)), 64, 127)],
    1820: [([[1 if (r + c) % 3 == 0 else 0 for c in range(24)] for r in range(24)],)],
    1826: [(list(range(256)), list(range(128)) + [999] + list(range(128, 255)))],
    1908: [([(i % 7) + 1 for i in range(64)],)],
    1918: [([(i % 9) + 1 for i in range(128)], 2000)],
    1924: [([[i % 17, (i * 7) % 19] for i in range(64)],)],
    1933: [("000" * 64 + "11" + "222" * 64,)],
    1940: [([list(range(i, 128 + i)) for i in range(8)],)],
}


def build_cases(problem_id: int, include_maximum: bool = False):
    ref = REFERENCES[problem_id]
    raw_tuples = list(BASE_ARGS[problem_id])
    if include_maximum:
        raw_tuples.extend(MAX_ARGS[problem_id])
    rows = []
    for tup in raw_tuples:
        args = deepcopy(list(tup))
        validate_domain(problem_id, *deepcopy(args))
        expected = ref(*deepcopy(args))
        rows.append({"args": args, "expected": expected})
    return rows
