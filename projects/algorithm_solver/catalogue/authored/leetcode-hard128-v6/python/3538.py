"""3538. Merge Operations for Minimum Travel Time.

Choose consecutive retained signs, carrying the preceding retained index to recover each merged time; O(n^2*k^2+n) time and O(n^2*k+n) space. Inputs are preserved.
"""

from functools import cache


def solve(l: int, n: int, k: int, position: list[int], time: list[int]) -> int:
    prefix = [0]
    for value in time:
        prefix.append(prefix[-1] + value)

    @cache
    def visit(previous, current, remaining):
        if current == n - 1:
            return 0 if remaining == 0 else float('inf')
        if remaining > n - current - 2:
            return float('inf')
        rate = prefix[current + 1] - prefix[previous + 1]
        best = float('inf')
        for following in range(current + 1, min(n, current + remaining + 2)):
            removed = following - current - 1
            best = min(best, (position[following] - position[current]) * rate
                       + visit(current, following, remaining - removed))
        return best

    return visit(-1, 0, k)


class Solution:
    def minTravelTime(self, l: int, n: int, k: int, position: list[int], time: list[int]) -> int:
        return solve(l, n, k, position, time)
