"""3877. Minimum Removals to Achieve Target XOR."""
from __future__ import annotations


def solve(nums: list[int], target: int) -> int:
    """O(n*2^14) time and O(2^14) space; find a minimum-cardinality removed subset with the required XOR."""
    limit = 1 << 14
    unreachable = len(nums) + 1
    best = [unreachable] * limit
    best[0] = 0
    total = 0
    for value in nums:
        total ^= value
        following = best.copy()
        for state, count in enumerate(best):
            if count < unreachable:
                following[state ^ value] = min(following[state ^ value], count + 1)
        best = following
    answer = best[total ^ target]
    return answer if answer <= len(nums) else -1


class Solution:
    def minRemovals(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
