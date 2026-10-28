"""403. Frog Jump (Hard).

Specification: https://leetcode.com/problems/frog-jump/description/
"""


def solve(stones: list[int]) -> bool:
    positions = set(stones)
    reachable = {stone: set() for stone in stones}
    reachable[stones[0]].add(0)
    for stone in stones:
        for jump in list(reachable[stone]):
            for next_jump in (jump - 1, jump, jump + 1):
                if next_jump > 0 and stone + next_jump in positions:
                    reachable[stone + next_jump].add(next_jump)
    return len(reachable[stones[-1]]) > 0


class Solution:
    def canCross(self, stones: list[int]) -> bool:
        return solve(stones)
