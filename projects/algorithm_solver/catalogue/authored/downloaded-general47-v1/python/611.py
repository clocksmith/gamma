"""611. Valid Triangle Number (Medium).

Specification: https://leetcode.com/problems/valid-triangle-number/description/
"""


def solve(nums: list[int]) -> int:
    ordered = sorted(nums)
    count = 0
    for k in range(len(ordered) - 1, 1, -1):
        left, right = 0, k - 1
        while left < right:
            if ordered[left] + ordered[right] > ordered[k]:
                count += right - left
                right -= 1
            else:
                left += 1
    return count


class Solution:
    def triangleNumber(self, nums: list[int]) -> int:
        return solve(nums)
