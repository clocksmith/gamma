"""3255. Find the Power of K-Size Subarrays II (Medium).

Specification: https://leetcode.com/problems/find-the-power-of-k-size-subarrays-ii/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    res = []
    streak = 0
    for i, x in enumerate(nums):
        streak = streak + 1 if i > 0 and x == nums[i - 1] + 1 else 1
        if i >= k - 1:
            res.append(x if streak >= k else -1)
    return res


class Solution:
    def results(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
