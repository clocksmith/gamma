"""3301. Maximize the Total Height of Unique Towers (Medium).

Specification: https://leetcode.com/problems/maximize-the-total-height-of-unique-towers/description/
"""


def solve(maximumHeight: list[int]) -> int:
    prev = float('inf')
    ans = 0
    for h in sorted(maximumHeight, reverse=True):
        cur = min(h, prev - 1)
        if cur <= 0:
            return -1
        ans += cur
        prev = cur
    return ans


class Solution:
    def maximumTotalSum(self, maximumHeight: list[int]) -> int:
        return solve(maximumHeight)
