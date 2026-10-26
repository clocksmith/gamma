"""3878. Count Good Subarrays."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n B) expected time and O(n+B) space, B<=31; compressed suffix-OR intervals joined to the last matching element."""
    groups = []
    last = {}
    answer = 0
    for right, value in enumerate(nums):
        last[value] = right
        following = [(value, 1)]
        for previous, count in groups:
            combined = previous | value
            if following[-1][0] == combined:
                following[-1] = (combined, following[-1][1] + count)
            else:
                following.append((combined, count))
        groups = following
        upper = right
        for combined, count in groups:
            lower = upper - count + 1
            answer += max(0, min(upper, last.get(combined, -1)) - lower + 1)
            upper = lower - 1
    return answer


class Solution:
    def countGoodSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
