"""1187. Make Array Strictly Increasing (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/make-array-strictly-increasing/description/
Canonical API: solve(arr1, arr2); also exposes Solution.makeArrayIncreasing.
Inputs are preserved. Gamma independent qualification is pending.
"""

from bisect import bisect_right


def solve(arr1: list[int], arr2: list[int]) -> int:
    replacements = sorted(set(arr2))
    infinity = float("inf")
    # Index is replacement count; value is the smallest possible final element.
    smallest_tail = [-1]
    for value in arr1:
        next_tails = [infinity] * (len(smallest_tail) + 1)
        for count, previous in enumerate(smallest_tail):
            if previous == infinity:
                continue
            if value > previous:
                next_tails[count] = min(next_tails[count], value)
            replacement_index = bisect_right(replacements, previous)
            if replacement_index < len(replacements):
                next_tails[count + 1] = min(
                    next_tails[count + 1], replacements[replacement_index]
                )

        # A no-cheaper state with a no-smaller tail can never improve a suffix.
        best_tail = infinity
        for count, tail in enumerate(next_tails):
            if tail >= best_tail:
                next_tails[count] = infinity
            else:
                best_tail = tail
        while next_tails and next_tails[-1] == infinity:
            next_tails.pop()
        if not next_tails:
            return -1
        smallest_tail = next_tails

    return next(count for count, tail in enumerate(smallest_tail) if tail != infinity)

class Solution:
    def makeArrayIncreasing(self, arr1: list[int], arr2: list[int]) -> int:
        return solve(arr1, arr2)
