"""Deterministic edge, boundary, and domain-maximum cases for requested-243-370-35."""

from copy import deepcopy
import importlib.util
from pathlib import Path

_ORACLES_PATH = Path(__file__).with_name("oracles.py")
_SPEC = importlib.util.spec_from_file_location("requested_243_370_35_oracles", _ORACLES_PATH)
_ORACLES = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ORACLES)

PROBLEM_IDS = _ORACLES.PROBLEM_IDS
REFERENCES = _ORACLES.REFERENCES
validate_domain = _ORACLES.validate_domain

BASE_ARGS = {
    243: [
        (["practice", "makes", "perfect", "coding", "makes"], "coding", "practice"),
        (["practice", "makes", "perfect", "coding", "makes"], "makes", "coding"),
        (["a", "b"], "a", "b"),
    ],
    245: [
        (["practice", "makes", "perfect", "coding", "makes"], "makes", "coding"),
        (["practice", "makes", "perfect", "coding", "makes"], "makes", "makes"),
        (["a", "a"], "a", "a"),
    ],
    246: [("69",), ("88",), ("962",), ("1",), ("818",)],
    247: [(2,), (1,), (3,), (4,)],
    248: [("50", "100"), ("0", "0"), ("10", "1000"), ("0", "1680")],
    249: [
        (["abc", "bcd", "acef", "xyz", "az", "ba", "a", "z"],),
        (["a"],),
        (["ab", "bc", "cd"],),
    ],
    250: [
        ([5, 1, 5, 5, 5, None, 5],),
        ([],),
        ([5, 5, 5, 5, 5, None, 5],),
    ],
    254: [(1,), (12,), (37,), (32,)],
    255: [([5, 2, 1, 3, 6],), ([5, 2, 6, 1, 3],), ([1],)],
    256: [
        ([[17, 2, 17], [16, 16, 5], [14, 3, 19]],),
        ([[7, 6, 2]],),
        ([[1, 2, 3], [4, 5, 6]],),
    ],
    259: [([-2, 0, 1, 3], 2), ([], 0), ([0], 0), ([3, 1, 0, -2], 4)],
    265: [
        ([[1, 5, 3], [2, 9, 4]],),
        ([[1, 3], [2, 4]],),
        ([[8]],),
    ],
    267: [("aabb",), ("abc",), ("aaa",), ("aabbc",)],
    269: [
        (["wrt", "wrf", "er", "ett", "rftt"],),
        (["z", "x"],),
        (["z", "x", "z"],),
        (["abc", "ab"],),
    ],
    270: [
        ([4, 2, 5, 1, 3], 3.714286),
        ([1], 4.428571),
        ([4, 2, 5, 1, 3], 3.5),
    ],
    272: [
        ([4, 2, 5, 1, 3], 3.714286, 2),
        ([1], 0.0, 1),
        ([4, 2, 5, 1, 3], 2.1, 3),
    ],
    276: [(3, 2), (1, 1), (7, 2), (4, 3)],
    296: [
        ([[1, 0, 0, 0, 1], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]],),
        ([[1, 1]],),
        ([[1, 0, 1], [0, 1, 0]],),
    ],
    298: [
        ([1, None, 3, 2, 4, None, None, None, 5],),
        ([2, None, 3, 2, None, 1],),
        ([1],),
    ],
    302: [
        ([["0", "0", "1", "0"], ["0", "1", "1", "0"], ["0", "1", "0", "0"]], 0, 2),
        ([["1"]], 0, 0),
        ([["0", "1"], ["1", "1"]], 1, 1),
    ],
    311: [
        ([[1, 0, 0], [-1, 0, 3]], [[7, 0, 0], [0, 0, 0], [0, 0, 1]]),
        ([[0]], [[0]]),
        ([[1, 2], [3, 4]], [[5, 6], [7, 8]]),
    ],
    314: [
        ([3, 9, 20, None, None, 15, 7],),
        ([3, 9, 8, 4, 0, 1, 7],),
        ([],),
    ],
    317: [
        ([[1, 0, 2, 0, 1], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]],),
        ([[1, 0]],),
        ([[1]],),
    ],
    320: [("word",), ("a",), ("ab",)],
    325: [([1, -1, 5, -2, 3], 3), ([-2, -1, 2, 1], 1), ([1, 2, 3], 10)],
    333: [
        ([10, 5, 15, 1, 8, None, 7],),
        ([4, 2, 7, 2, 3, 5, None, 2, None, None, None, None, None, 1],),
        ([],),
    ],
    340: [("eceba", 2), ("aa", 1), ("abcdef", 0), ("abaccc", 2)],
    351: [(1, 1), (1, 2), (2, 3)],
    356: [([[1, 1], [-1, 1]],), ([[1, 1], [-1, -1]],), ([[0, 0]],)],
    358: [("aabbcc", 3), ("aaabc", 3), ("aaadbbcc", 2), ("a", 0)],
    360: [
        ([-4, -2, 2, 4], 1, 3, 5),
        ([-4, -2, 2, 4], -1, 3, 5),
        ([0, 1, 2], 0, -2, 1),
    ],
    361: [
        ([["0", "E", "0", "0"], ["E", "0", "W", "E"], ["0", "E", "0", "0"]],),
        ([["W", "W", "W"], ["0", "0", "0"], ["E", "E", "E"]],),
        ([["0"]],),
    ],
    366: [([1, 2, 3, 4, 5],), ([1],)],
    369: [([1, 2, 3],), ([0],), ([9, 9, 9],), ([1, 9, 9],)],
    370: [
        (5, [[1, 3, 2], [2, 4, 3], [0, 2, -2]]),
        (10, [[2, 4, 6], [5, 6, 8], [1, 9, -4]]),
        (3, []),
    ],
}

MAX_ARGS = {
    243: [(["w" + str(i % 20) for i in range(256)], "w1", "w15")],
    245: [(["w" + str(i % 20) for i in range(256)], "w5", "w5")],
    246: [("6" * 25 + "9" * 25,)],
    247: [(6,)],
    248: [("100", "9999999")],
    249: [(["abc", "bcd", "cde", "xyz", "yza", "zab"] * 32,)],
    250: [([7] * 127,)],
    254: [(720,)],
    255: [(list(range(1, 257)),)],
    256: [([[i % 17 + 1, (i * 3) % 19 + 1, (i * 7) % 23 + 1] for i in range(256)],)],
    259: [([i - 64 for i in range(128)], 10)],
    265: [([[(i + j * 3) % 29 + 1 for j in range(12)] for i in range(64)],)],
    267: [("aabbccddeeff",)],
    269: [(["abcd", "abce", "abcf", "bcde", "cdef", "defg"],)],
    270: [([8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15], 10.6)],
    272: [([8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15], 6.3, 7)],
    276: [(20, 4)],
    296: [([[1 if (r + c) % 5 == 0 else 0 for c in range(20)] for r in range(20)],)],
    298: [(list(range(1, 128)),)],
    302: [([["1" if 4 <= r <= 12 and 3 <= c <= 11 else "0" for c in range(16)] for r in range(16)], 8, 8)],
    311: [
        ([[i if (i + j) % 3 == 0 else 0 for j in range(16)] for i in range(16)],
         [[j if (i + j) % 4 == 0 else 0 for j in range(16)] for i in range(16)]),
    ],
    314: [(list(range(1, 128)),)],
    317: [([[1 if (r == 0 and c in (0, 7)) else 0 for c in range(8)] for r in range(8)],)],
    320: [("abcdefgh",)],
    325: [([(i % 7) - 3 for i in range(256)], 5)],
    333: [([8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15],)],
    340: [("abcdefgh" * 32, 4)],
    351: [(1, 6)],
    356: [([[i, i * 2] for i in range(1, 65)] + [[-i, i * 2] for i in range(1, 65)],)],
    358: [("abcdefgh" * 32, 4)],
    360: [(list(range(-128, 128)), -2, 5, -3)],
    361: [([["E" if (r + c) % 3 == 0 else ("W" if (r + c) % 7 == 0 else "0") for c in range(16)] for r in range(16)],)],
    366: [(list(range(1, 128)),)],
    369: [([9] * 128,)],
    370: [(256, [[i, min(255, i + 20), (i % 7) - 3] for i in range(0, 256, 4)])],
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
