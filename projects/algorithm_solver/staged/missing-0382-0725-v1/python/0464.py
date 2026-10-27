"""464. Can I Win. Memoized minimax over the chosen-number mask."""

from functools import lru_cache

def solve(maxChoosableInteger: int, desiredTotal: int) -> bool:
    if desiredTotal <= 0:
        return True
    if maxChoosableInteger * (maxChoosableInteger + 1) // 2 < desiredTotal:
        return False
    @lru_cache(None)
    def win(mask, remaining):
        for value in range(maxChoosableInteger, 0, -1):
            bit = 1 << (value - 1)
            if mask & bit:
                continue
            if value >= remaining or not win(mask | bit, remaining - value):
                return True
        return False
    return win(0, desiredTotal)


class Solution:
    def canIWin(self, maxChoosableInteger: int, desiredTotal: int) -> bool:
        return solve(maxChoosableInteger, desiredTotal)
