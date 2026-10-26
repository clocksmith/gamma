"""1889. Minimum Space Wasted From Packaging."""

from bisect import bisect_right


def solve(packages: list[int], boxes: list[list[int]]) -> int:
    """Supplier sweeps over sorted packages; O(n log n + B log B + B log n) time, O(n+B) space. Inputs are preserved."""
    modulus = 1_000_000_007
    ordered = sorted(packages)
    total = sum(ordered)
    best = None
    for supplier in boxes:
        sizes = sorted(supplier)
        if not sizes or sizes[-1] < ordered[-1]:
            continue
        cursor = 0
        capacity = 0
        for size in sizes:
            following = bisect_right(ordered, size, cursor)
            capacity += (following - cursor) * size
            cursor = following
            if cursor == len(ordered):
                break
        waste = capacity - total
        best = waste if best is None else min(best, waste)
    return -1 if best is None else best % modulus


class Solution:
    def minWastedSpace(self, packages: list[int], boxes: list[list[int]]) -> int:
        return solve(packages, boxes)
