"""1387. Sort Integers by The Power Value: memoize Collatz lengths iteratively and sort by length then value."""


def solve(lo: int, hi: int, k: int) -> int:
    """O(T + m log m) time and O(T + m) space for m values and T newly visited Collatz states; inputs are read-only."""
    lengths = {1: 0}

    def power(value: int) -> int:
        path = []
        current = value
        while current not in lengths:
            path.append(current)
            current = current // 2 if current % 2 == 0 else 3 * current + 1
        steps = lengths[current]
        for current in reversed(path):
            steps += 1
            lengths[current] = steps
        return lengths[value]

    ordered = sorted(range(lo, hi + 1), key=lambda value: (power(value), value))
    return ordered[k - 1]


class Solution:
    def getKth(self, lo: int, hi: int, k: int) -> int:
        return solve(lo, hi, k)
