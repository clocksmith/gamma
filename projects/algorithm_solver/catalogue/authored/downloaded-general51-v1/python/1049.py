"""1049. Last Stone Weight II (Medium).

Specification: https://leetcode.com/problems/last-stone-weight-ii/description/
"""


def solve(stones: list[int]) -> int:
    total = sum(stones)
    reachable = {0}
    for stone in stones:
        reachable = reachable | {value + stone for value in reachable}
    best = 0
    for value in reachable:
        if value <= total // 2:
            best = max(best, value)
    return total - 2 * best


class Solution:
    def lastStoneWeightII(self, stones: list[int]) -> int:
        return solve(stones)
