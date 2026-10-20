"""Public development oracles for twenty literal JS implementations.

No corpus fixtures, candidate imports, subprocesses, network or sandbox execution.
`cases_by_problem` is HOST ONLY. Send `input_packet()` (never this module or its
case dictionary) into the sandbox. Results are compared here on the host.
All inputs are preserved; #1051 sorts a slice and #605 only tracks occupancy.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import itertools
import json
import math
import random
import re
import sys

SEED = 20261020
METHODS = {
    136: "singleNumber", 169: "majorityElement", 242: "isAnagram",
    387: "firstUniqChar", 575: "distributeCandies", 771: "numJewelsInStones",
    961: "repeatedNTimes", 1051: "heightChecker", 1108: "defangIPaddr",
    1119: "removeVowels",
    121: "maxProfit", 551: "checkRecord", 594: "findLHS",
    605: "canPlaceFlowers", 643: "findMaxAverage", 657: "judgeCircle",
    674: "findLengthOfLCIS", 704: "search", 709: "toLowerCase", 724: "pivotIndex",
}
PARAMS = {
    136: ["nums"], 169: ["nums"], 242: ["s", "t"], 387: ["s"],
    575: ["candyType"], 771: ["jewels", "stones"], 961: ["nums"],
    1051: ["heights"], 1108: ["address"], 1119: ["s"],
    121: ["prices"], 551: ["s"], 594: ["nums"], 605: ["flowerbed", "n"],
    643: ["nums", "k"], 657: ["moves"], 674: ["nums"], 704: ["nums", "target"],
    709: ["s"], 724: ["nums"],
}
DOMAINS = {
    136: "Nonempty integer array; exactly one value occurs once, all others twice; values in [-30000,30000].",
    169: "Nonempty integer array with a strict majority; values in [-10^9,10^9].",
    242: "Two nonempty lowercase ASCII strings; exact character multiplicity, no Unicode normalization.",
    387: "Nonempty lowercase ASCII string; zero-based index of first unique character, or -1.",
    575: "Positive even-length array; integer candy types in [-100000,100000].",
    771: "Distinct nonempty ASCII letter jewels and nonempty ASCII letter stones; case-sensitive.",
    961: "Length 2N, N>=2; N+1 distinct integers in [0,10000]; one occurs N times, all others once.",
    1051: "Nonempty heights array, length<=100, values in [1,100]; input must remain unchanged.",
    1108: "Canonical valid dotted-decimal IPv4, four decimal octets in [0,255], no leading zeroes.",
    1119: "Nonempty lowercase ASCII string; remove exactly a,e,i,o,u.",
    121: "Nonempty prices array in [0,10000]; at most one buy then later sell, or zero profit.",
    551: "Nonempty ASCII A/L/P attendance; fewer than two A and no three consecutive L.",
    594: "Nonempty signed integer array in [-10^9,10^9]; subsequence max-min exactly1.",
    605: "Nonempty binary flowerbed, no adjacent existing flowers; n in [0,length]; selected source preserves input.",
    643: "Nonempty integers [-10000,10000], 1<=k<=length; maximum contiguous length-k average.",
    657: "Nonempty ASCII U/D/L/R moves; return whether endpoint is origin.",
    674: "Nonempty integers [-10^9,10^9]; longest strictly increasing contiguous run.",
    704: "Nonempty strictly increasing distinct integers [-9999,9999], target in same range; exact index or -1.",
    709: "Nonempty printable ASCII string of length<=100; uppercase Latin letters become lowercase, others unchanged.",
    724: "Nonempty integers [-1000,1000]; leftmost index with equal sums strictly to its left/right.",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def oracle(problem, args):
    """Independent host specifications, deliberately not candidate algorithms."""
    if problem == 136:
        counts = Counter(args[0])
        singles = [v for v, count in counts.items() if count == 1]
        assert len(singles) == 1 and all(n in (1, 2) for n in counts.values())
        return singles[0]
    if problem == 169:
        middle = sorted(args[0])[len(args[0]) // 2]
        assert args[0].count(middle) > len(args[0]) // 2
        return middle
    if problem == 242:
        return sorted(args[0]) == sorted(args[1])
    if problem == 387:
        return next((i for i, c in enumerate(args[0]) if args[0].count(c) == 1), -1)
    if problem == 575:
        # Subset search is an independent optimum oracle on exhaustive small cases.
        values = args[0]
        if len(values) <= 6:
            return max(len(set(choice)) for choice in itertools.combinations(values, len(values) // 2))
        return min(len(Counter(values)), len(values) // 2)
    if problem == 771:
        return sum(args[1].count(jewel) for jewel in args[0])
    if problem == 961:
        counts = Counter(args[0])
        assert len(args[0]) % 2 == 0 and len(args[0]) >= 4
        n = len(args[0]) // 2
        assert len(counts) == n + 1 and sorted(counts.values()) == [1] * n + [n]
        return next(v for v, count in counts.items() if count == n)
    if problem == 1051:
        # Histogram expansion avoids reproducing the source's heap sort.
        histogram = Counter(args[0])
        ordered = [height for height in range(1, 101) for _ in range(histogram[height])]
        return sum(a != b for a, b in zip(args[0], ordered))
    if problem == 1108:
        octets = args[0].split(".")
        assert len(octets) == 4 and all(str(int(x)) == x and 0 <= int(x) <= 255 for x in octets)
        return "[.]".join(octets)
    if problem == 1119:
        return re.sub("[aeiou]", "", args[0])
    if problem == 121:
        prices = args[0]
        return max([0] + [prices[j] - prices[i] for i in range(len(prices)) for j in range(i + 1, len(prices))])
    if problem == 551:
        return args[0].count("A") < 2 and "LLL" not in args[0]
    if problem == 594:
        values = args[0]
        if len(values) <= 8:
            valid = [len(s) for n in range(1, len(values) + 1)
                     for s in itertools.combinations(values, n) if max(s) - min(s) == 1]
            return max(valid, default=0)
        # Direct characterization by all allowed lower endpoints; no object-key representation.
        return max((sum(v in (low, low + 1) for v in values)
                    for low in set(values) if low + 1 in values), default=0)
    if problem == 605:
        bed, required = args
        assert len(bed) <= 12  # This development oracle enumerates placements.
        free = [i for i, value in enumerate(bed) if value == 0]
        if required > len(free):
            return False
        # Existence search over exact-sized placements, independent of greedy scanning.
        for places in itertools.combinations(free, required):
            occupied = {i for i, value in enumerate(bed) if value == 1} | set(places)
            if all(i + 1 not in occupied for i in occupied):
                return True
        return False
    if problem == 643:
        values, k = args
        return max(sum(values[start:start + k]) for start in range(len(values) - k + 1)) / k
    if problem == 657:
        moves = args[0]
        return moves.count("U") == moves.count("D") and moves.count("L") == moves.count("R")
    if problem == 674:
        values = args[0]
        return max(j - i for i in range(len(values)) for j in range(i + 1, len(values) + 1)
                   if all(values[k] < values[k + 1] for k in range(i, j - 1)))
    if problem == 704:
        values, target = args
        return next((i for i, value in enumerate(values) if value == target), -1)
    if problem == 709:
        return args[0].lower()
    if problem == 724:
        values = args[0]
        return next((i for i in range(len(values)) if sum(values[:i]) == sum(values[i + 1:])), -1)
    raise ValueError("Unapproved problem")


def _generate():
    out = {problem: [] for problem in METHODS}
    seen = {problem: set() for problem in METHODS}

    def add(problem, *args):
        args = deepcopy(list(args))
        token = canonical(args)
        if token not in seen[problem]:
            seen[problem].add(token)
            out[problem].append({"args": args, "expected": oracle(problem, args)})

    # Complete small domains, filtered only by each mathematical input promise.
    for length in (1, 3, 5):
        for values in itertools.product((-1, 0, 1), repeat=length):
            counts = Counter(values)
            if list(counts.values()).count(1) == 1 and all(n in (1, 2) for n in counts.values()):
                add(136, list(values))
    for length in range(1, 6):
        for values in itertools.product((0, 1, 2), repeat=length):
            if max(Counter(values).values()) > length // 2:
                add(169, list(values))
    words = ["".join(w) for length in range(1, 4) for w in itertools.product("ab", repeat=length)]
    for left, right in itertools.product(words, repeat=2):
        add(242, left, right)
    for length in range(1, 8):
        for chars in itertools.product("ab", repeat=length):
            add(387, "".join(chars))
    for length in (2, 4):
        for values in itertools.product((-1, 0, 1), repeat=length):
            add(575, list(values))
    jewels = ["".join(x) for n in (1, 2) for x in itertools.permutations("aA", n)]
    stones = ["".join(x) for n in range(1, 4) for x in itertools.product("aAb", repeat=n)]
    for left, right in itertools.product(jewels, stones):
        add(771, left, right)
    for values in itertools.product((0, 1, 2), repeat=4):
        if sorted(Counter(values).values()) == [1, 1, 2]:
            add(961, list(values))
    for length in range(1, 5):
        for values in itertools.product((1, 2, 3), repeat=length):
            add(1051, list(values))
    for octets in itertools.product((0, 1, 255), repeat=4):
        add(1108, ".".join(map(str, octets)))
    for length in range(1, 6):
        for chars in itertools.product("aex", repeat=length):
            add(1119, "".join(chars))

    # Hand edges are authored, not taken from any corpus or evaluation set.
    edges = {
        136: [[[-30000]], [[30000]], [[-30000, 30000, -30000]], [[0, -1, -1]],
              [[30000, 0, -30000, 30000, 0]]],
        169: [[[-10**9]], [[10**9, -10**9, 10**9]], [[0, -1, 0, 1, 0]]],
        242: [["z", "z"], ["az", "za"], ["aab", "abb"], ["abc", "ab"],
              ["abcdefghijklmnopqrstuvwxyz", "zyxwvutsrqponmlkjihgfedcba"]],
        387: [["z"], ["zz"], ["z" + "a" * 99], ["a" * 99 + "z"],
              ["a" * 50 + "z" + "a" * 50], ["abcdefghijklmnopqrstuvwxyz" * 2]],
        575: [[[-100000, 100000]], [[4] * 100], [list(range(100))],
              [[-100000, 0, 100000, -100000, 0, 100000]]],
        771: [["a", "A"], ["A", "a"], ["aA", "aA" * 25], ["zZ", "z" * 50]],
        961: [[[1, 2, 1, 3]], [[0, 1, 2, 0]], [[10000, 0, 10000, 9999]]],
        1051: [[[100]], [[100, 1]], [[2, 10, 1]], [[5] * 100],
               [list(range(1, 101))], [list(range(100, 0, -1))]],
        1108: [["10.20.100.200"], ["255.254.253.252"], ["0.10.0.100"]],
        1119: [["aeiou"], ["bcdxyz"], ["u" * 1000], ["z" * 1000],
               ["abcdefghijklmnopqrstuvwxyz"], ["uoiea" * 200]],
    }
    for problem, cases in edges.items():
        for args in cases:
            add(problem, *args)

    rng = random.Random(SEED)
    for _ in range(32):
        distinct = rng.sample(range(-30000, 30001), rng.randint(1, 25))
        values = distinct[:1] + [v for v in distinct[1:] for _ in range(2)]
        rng.shuffle(values)
        add(136, values)
        size = rng.randint(1, 100)
        majority = rng.choice((-10**9, -1, 0, 1, 10**9))
        values = [majority] * (size // 2 + 1) + [rng.randint(-100, 100) for _ in range(size - size // 2 - 1)]
        rng.shuffle(values)
        add(169, values)
        word = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(1, 80)))
        other = list(word)
        rng.shuffle(other)
        add(242, word, "".join(other))
        add(242, word, "".join(other) + "z")
        add(387, word)
        add(575, [rng.randint(-20, 20) for _ in range(2 * rng.randint(1, 50))])
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        jewel = "".join(rng.sample(alphabet, rng.randint(1, 20)))
        stone = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 50)))
        add(771, jewel, stone)
        n = rng.randint(2, 30)
        selected = rng.sample(range(10001), n + 1)
        values = [selected[0]] * n + selected[1:]
        rng.shuffle(values)
        add(961, values)
        add(1051, [rng.randint(1, 100) for _ in range(rng.randint(1, 100))])
        add(1108, ".".join(str(rng.randrange(256)) for _ in range(4)))
        add(1119, word)

    # The original ten inventories above remain byte-for-byte identical to V1.
    # Complete small domains for the additional ten, with no candidate feedback.
    for length in range(1, 5):
        for values in itertools.product((0, 1, 2), repeat=length):
            add(121, list(values))
            add(674, list(values))
        for chars in itertools.product("ALP", repeat=length):
            add(551, "".join(chars))
        for values in itertools.product((-1, 0, 1), repeat=length):
            add(594, list(values))
            add(724, list(values))
            if length <= 3:
                for k in range(1, length + 1):
                    add(643, list(values), k)
    for length in range(1, 7):
        for bed in itertools.product((0, 1), repeat=length):
            if not any(a == b == 1 for a, b in zip(bed, bed[1:])):
                for n in range(length + 1):
                    add(605, list(bed), n)
    for length in range(1, 4):
        for moves in itertools.product("UDLR", repeat=length):
            add(657, "".join(moves))
        for chars in itertools.product("aAZ0!", repeat=length):
            add(709, "".join(chars))
    for length in range(1, 6):
        for values in itertools.combinations((-2, -1, 0, 1, 2), length):
            for target in range(-3, 4):
                add(704, list(values), target)

    extra_edges = {
        121: [[[0]], [[10000]], [[10000, 0, 10000]], [[9, 7, 4, 1]],
              [[2, 8, 1, 7]], [[5, 5, 5]], [[4, 3, 9, 1, 8]]],
        551: [["LLL"], ["LLPL"], ["LALL"], ["ALLA"], ["P" * 1000],
              ["L" * 1000], ["LPL" * 100 + "A"]],
        594: [[[10**9]], [[-10**9, -10**9 + 1, -10**9]], [[-1, 1]],
              [[4, 4, 4]], [[8, 7, 8, 9, 8, 7]], [[10**9, 10**9 - 1]]],
        605: [[[0], 0], [[0], 1], [[1], 0], [[1], 1], [[0] * 12, 6],
              [[0] * 12, 7], [[1, 0, 0, 0, 1], 1], [[1, 0, 0, 0, 1], 2],
              [[0, 0, 1, 0, 0], 2]],
        643: [[[-10000, -9999], 1], [[10000, -10000, 10000], 3],
              [[1, 0, 0], 3], [[-1, 0, 0], 3], [[7, 7, 7], 2],
              [[0, 1, 8, 9, 10], 2], [[10000] * 100, 100]],
        657: [["UDLR"], ["ULDR"], ["UUDDLR"], ["URDLU"], ["L" * 1000 + "R" * 1000]],
        674: [[[10**9]], [[-10**9, 0, 10**9]], [[1, 2, 2, 3]], [[1, 9, 2, 3, 4]],
              [[4, 3, 2, 1]], [list(range(30))]],
        704: [[[-9999, 0, 9999], -9999], [[-9999, 0, 9999], 9999],
              [[-9999, 0, 9999], 1], [[0], -9999], [[0], 9999], [[0], 0]],
        709: [["ABCDEFGHIJKLMNOPQRSTUVWXYZ"], ["abcdefghijklmnopqrstuvwxyz"],
              ["@AZ[az`"], [" !" + "0123456789" + ":;<=>?"],
              ["Z" * 100], ["aB cD!\t".replace("\t", " ")]],
        724: [[[0]], [[1]], [[0, 0, 0]], [[1, -1, 0]], [[0, 1, -1]],
              [[1, 2, 3]], [[-1000, 1000, 0]], [[1, 7, 3, 6, 5, 6]]],
    }
    for problem, cases in extra_edges.items():
        for args in cases:
            add(problem, *args)
    rng = random.Random(SEED + 1)
    for _ in range(32):
        add(121, [rng.randrange(10001) for _ in range(rng.randint(1, 40))])
        add(551, "".join(rng.choice("ALP") for _ in range(rng.randint(1, 80))))
        add(594, [rng.randint(-10, 10) for _ in range(rng.randint(1, 40))])
        bed = [0] * rng.randint(1, 12)
        for position in rng.sample(range(len(bed)), len(bed)):
            if rng.randrange(2) and (position == 0 or bed[position - 1] == 0) and (position + 1 == len(bed) or bed[position + 1] == 0):
                bed[position] = 1
        add(605, bed, rng.randrange(len(bed) + 1))
        values = [rng.randint(-10000, 10000) for _ in range(rng.randint(1, 40))]
        add(643, values, rng.randint(1, len(values)))
        add(657, "".join(rng.choice("UDLR") for _ in range(rng.randint(1, 80))))
        add(674, [rng.randint(-10, 10) for _ in range(rng.randint(1, 30))])
        values = sorted(rng.sample(range(-9999, 10000), rng.randint(1, 40)))
        add(704, values, rng.choice(values))
        add(704, values, rng.randint(-9999, 9999))
        add(709, "".join(chr(rng.randint(32, 126)) for _ in range(rng.randint(1, 100))))
        add(724, [rng.randint(-10, 10) for _ in range(rng.randint(1, 40))])
    return out


cases_by_problem = _generate()
method_names = dict(METHODS)


def input_packet(problem, offset=0, limit=4):
    """Only this return value may be serialized into a candidate task mount."""
    if type(problem) is not int or problem not in METHODS:
        raise ValueError("Unapproved problem")
    cases = cases_by_problem[problem]
    if type(offset) is not int or type(limit) is not int or not 0 <= offset < len(cases) or not 1 <= limit <= 16:
        raise ValueError("Invalid bounded call slice")
    return {
        "entry": {"class": "Solution", "method": METHODS[problem]},
        "method": METHODS[problem], "params": [[name, ""] for name in PARAMS[problem]],
        "interface": "solution-class",
        "calls": [{"args": deepcopy(c["args"]), "kwargs": {}, "capture_args": True}
                  for c in cases[offset:offset + limit]],
    }


def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if type(expected) is list:
        return len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
    if type(expected) is dict:
        return actual.keys() == expected.keys() and all(exact(actual[k], expected[k]) for k in expected)
    return actual == expected


def check_observation(problem, index, observation):
    """Host-side semantic/effect check; native/protocol proof is separate."""
    if type(index) is not int or not 0 <= index < len(cases_by_problem[problem]):
        raise ValueError("Unknown case index")
    case = cases_by_problem[problem][index]
    if type(observation) is not dict:
        return {"passed": False, "result_ok": False, "input_preserved": False}
    clean = not any(k in observation for k in ("error", "load_error"))
    result_ok = clean and "result" in observation and exact(observation["result"], case["expected"])
    if problem == 643:
        result = observation.get("result")
        # JSON's 7 versus 7.0 are the same JS Number. Bool and nonfinite remain forbidden.
        # All integer sums are exactly representable, so correctly rounded division
        # must match the host binary64 value. No epsilon can hide a wrong window.
        result_ok = (clean and type(result) in (int, float) and -10000 <= result <= 10000
                     and math.isfinite(result) and result == case["expected"])
    preserved = clean and exact(observation.get("args_before"), case["args"]) and exact(observation.get("args_after"), case["args"])
    return {"passed": result_ok and preserved, "result_ok": result_ok, "input_preserved": preserved}


def check_records(problem, offset, records):
    """Reject malformed/reordered/duplicate records, then compare on host."""
    if type(records) is not list or len(records) < 2:
        raise ValueError("Missing observations/completion")
    count = len(records) - 1
    input_packet(problem, offset, count)  # validates ID, offset and bound
    if offset + count > len(cases_by_problem[problem]):
        raise ValueError("Case slice exceeds inventory")
    end = records[-1]
    if type(end) is not dict or set(end) != {"done"} or type(end["done"]) is not int or end["done"] != count:
        raise ValueError("Invalid completion")
    results = []
    for i, observation in enumerate(records[:-1]):
        if type(observation) is not dict or type(observation.get("i")) is not int or observation["i"] != i:
            raise ValueError("Invalid observation index/order")
        results.append(check_observation(problem, offset + i, observation))
    return {"total": count, "passed": sum(r["passed"] for r in results), "observations": results}


def manifest():
    return {
        "schema": "gamma.literal-pilot-development-checks.v2",
        "author": "/root/review_standard", "seed": SEED,
        "purpose": "Public/shareable development checks; not fresh held-out evaluation or corpus qualification.",
        "provenance": "Authored from problem knowledge; no corpus fixture or protected data access.",
        "numeric_scope": "All integer inputs and intermediate sums are JS safe integers. #643 has finite binary64 averages and exact numeric equality (JSON whole-number spelling allowed); all other result types exact. No BigInt/coercion coverage.",
        "text_scope": "ASCII only: lowercase242/387/1119, case-sensitive letters771, ALP551, UDLR657, printableASCII709, IPv4decimal1108. No Unicode generalization.",
        "mutation": "All20 preserve every input argument, including1051 whose original sorts values.slice() and605 whose original tracks virtual occupancy without writes.",
        "coverage_limits": "Development checks, not a proof of all official inputs; #605 placement oracle deliberately bounded to12 cells; string/array maxima not exhaustively covered.",
        "encoding_target": "At most16 literal dictionary entries, all emitted source bytes accounted; this suite judges behavior only, not compression compliance.",
        "problems": {str(p): {"method": METHODS[p], "domain": DOMAINS[p], "cases": len(cases),
                              "host_cases_sha256": hashlib.sha256(canonical(cases).encode()).hexdigest(),
                              "input_only_sha256": hashlib.sha256(canonical([c["args"] for c in cases]).encode()).hexdigest()}
                     for p, cases in cases_by_problem.items()},
        "total_cases": sum(map(len, cases_by_problem.values())),
        "candidate_runs": 0,
        "sandbox_rule": "Do not mount this module or cases_by_problem. Emit inputs only; native exit/resource/protocol/source binding must be verified by the root runner before check_records.",
    }


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("manifest", "inputs", "compare"))
    parser.add_argument("--id", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()
    if args.action == "manifest":
        result = manifest()
    elif args.action == "inputs":
        result = input_packet(args.id, args.offset, args.limit)
    else:
        raw = sys.stdin.read(4 * 1024 * 1024 + 1)
        if len(raw.encode()) > 4 * 1024 * 1024:
            raise ValueError("Observation input too large")
        records = [json.loads(line, object_pairs_hook=_object,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
                   for line in raw.splitlines() if line.strip()]
        result = check_records(args.id, args.offset, records)
    print(canonical(result))


if __name__ == "__main__":
    main()
