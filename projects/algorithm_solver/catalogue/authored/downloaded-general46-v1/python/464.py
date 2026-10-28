"""464. Can I Win (Medium).

Specification: https://leetcode.com/problems/can-i-win/description/
"""


def solve(maxChoosableInteger: int, desiredTotal: int) -> bool:
    if desiredTotal <= 0:
        return True
    total = maxChoosableInteger * (maxChoosableInteger + 1) // 2
    if total < desiredTotal:
        return False
    if maxChoosableInteger >= desiredTotal:
        return True
    memo = {}

    def can_win(used, remaining):
        key = (used, remaining)
        if key in memo:
            return memo[key]
        result = False
        for choice in range(1, maxChoosableInteger + 1):
            if (used >> (choice - 1)) & 1:
                continue
            if choice >= remaining or not can_win(used | (1 << (choice - 1)), remaining - choice):
                result = True
                break
        memo[key] = result
        return result

    return can_win(0, desiredTotal)


class Solution:
    def canIWin(self, maxChoosableInteger: int, desiredTotal: int) -> bool:
        return solve(maxChoosableInteger, desiredTotal)
