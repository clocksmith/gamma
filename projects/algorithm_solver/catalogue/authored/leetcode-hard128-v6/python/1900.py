"""1900. The Earliest and Latest Rounds Where Players Compete.

Memoize protected-player positions; enumerate reachable winner counts without enumerating complete tournaments.
"""

from functools import lru_cache


def solve(n: int, firstPlayer: int, secondPlayer: int) -> list[int]:
    @lru_cache(None)
    def rounds(size, first, second):
        if first + second == size + 1:
            return (1, 1)
        reachable = {(0, 0)}
        for left in range(1, (size + 1) // 2 + 1):
            right = size + 1 - left
            if left in (first, second):
                winners = (left,)
            elif right in (first, second):
                winners = (right,)
            elif left == right:
                winners = (left,)
            else:
                winners = (left, right)
            reachable = {(a + (winner < first), b + (winner < second))
                         for a, b in reachable for winner in winners}
        earliest, latest = size, 0
        for before_first, before_second in reachable:
            low, high = rounds((size + 1) // 2, before_first + 1, before_second + 1)
            earliest = min(earliest, low + 1)
            latest = max(latest, high + 1)
        return earliest, latest

    first, second = sorted((firstPlayer, secondPlayer))
    return list(rounds(n, first, second))


class Solution:
    def earliestAndLatest(self, n: int, firstPlayer: int, secondPlayer: int) -> list[int]:
        return solve(n, firstPlayer, secondPlayer)
