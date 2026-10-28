"""3371. Identify the Largest Outlier in an Array (Medium).

Specification: https://leetcode.com/problems/identify-the-largest-outlier-in-an-array/description/
"""


def solve(nums: list[int]) -> int:
    total = sum(nums)
    freq = {}
    for x in nums:
        freq[x] = freq.get(x, 0) + 1
    ans = float('-inf')
    for x in nums:
        rest = total - x
        if rest % 2 != 0:
            continue
        sum_val = rest // 2
        need = 2 if sum_val == x else 1
        if freq.get(sum_val, 0) >= need:
            ans = max(ans, x)
    return ans


class Solution:
    def getLargestOutlier(self, nums: list[int]) -> int:
        return solve(nums)
