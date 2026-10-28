"""2454. Next Greater Element IV (Hard).

Specification: https://leetcode.com/problems/next-greater-element-iv/description/
"""


def solve(nums):
    n = len(nums)
    ans = [-1] * n
    for i in range(n):
        seen = 0
        for j in range(i + 1, n):
            if nums[j] > nums[i]:
                seen += 1
                if seen == 2:
                    ans[i] = nums[j]
                    break
    return ans


class Solution:
    def secondGreaterElement(self, nums):
        return solve(nums)
