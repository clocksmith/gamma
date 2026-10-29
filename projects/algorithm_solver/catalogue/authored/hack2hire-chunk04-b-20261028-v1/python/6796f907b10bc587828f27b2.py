"""Hack2Hire 6796f907b10bc587828f27b2 (Calculate Total Waiting Time) over an INFERRED spec; qualification unknown."""
from bisect import bisect_right


def solve(arr):
    n = len(arr)
    if n == 0:
        return 0
    ordered = sorted(arr)
    prefix = [0]
    for v in ordered:
        prefix.append(prefix[-1] + v)
    top = ordered[-1]
    tree = [0] * (top + 1)  # Fenwick tree over values 1..top
    total = 0
    for i, v in enumerate(arr):
        j = v
        while j <= top:
            tree[j] += 1
            j += j & -j
        smaller, j = 0, v - 1
        while j > 0:
            smaller += tree[j]
            j -= j & -j
        cut = bisect_right(ordered, v - 1)
        before_last_round = prefix[cut] + (n - cut) * (v - 1)
        completion = before_last_round + (i + 1 - smaller)
        total += completion - v
    return total


class Solution:
    def totalWaitingTime(self, arr):
        return solve(arr)
